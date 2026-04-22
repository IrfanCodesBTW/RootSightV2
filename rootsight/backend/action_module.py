import logging
import uuid
from .schemas.incident import Incident
from .schemas.impact import Impact
from .schemas.hypothesis import HypothesisList
from .schemas.action import ActionList, Action, ActionType, ApprovalStatus, ExecutionStatus
from .llm_clients.groq_client import format_json

logger = logging.getLogger(__name__)

async def generate_actions(incident: Incident, impact: Impact, hypothesis_list: HypothesisList) -> ActionList:
    """
    Calls Groq (Llama 3) to rapidly format incident data into actionable drafts
    like a Jira ticket and a Slack update.
    """
    logger.info(
        "generate_actions.start incident_id=%s hypotheses=%s",
        incident.incident_id,
        len(hypothesis_list.hypotheses),
    )
    try:
        top_hypothesis = hypothesis_list.hypotheses[0] if hypothesis_list.hypotheses else None
        cause_statement = top_hypothesis.statement if top_hypothesis else "Unknown cause"

        prompt = f"""
        You are an expert SRE automation bot.
        Draft 2 follow-up actions for this incident.
        
        Incident: {incident.title} ({incident.service})
        Severity: {incident.severity}
        Impact: {impact.business_impact_summary or 'Unknown'}
        Top Hypothesis: {cause_statement}

        Draft exactly two actions:
        1. A Jira ticket (action_type: "jira_ticket") to investigate the root cause.
        2. A Slack responder update (action_type: "slack_responder") summarizing the current state.

        Return ONLY valid JSON matching this schema:
        {{
            "actions": [
                {{
                    "action_type": "jira_ticket|slack_responder",
                    "destination": "JIRA-BOARD or #slack-channel",
                    "payload_preview": "Short 1-sentence summary of what this is",
                    "full_payload": {{
                        // For Jira: title, description, priority
                        // For Slack: message
                    }}
                }}
            ]
        }}
        """

        response_dict = await format_json(prompt)
        if not isinstance(response_dict, dict):
            raise ValueError("Groq action response is not a JSON object.")

        actions = []
        raw_actions = response_dict.get("actions", [])
        if not isinstance(raw_actions, list):
            raw_actions = []

        for a in raw_actions:
            if not isinstance(a, dict):
                logger.warning("generate_actions.invalid_action_shape incident_id=%s action=%s", incident.incident_id, a)
                continue
            try:
                status = ApprovalStatus.PENDING
                exec_status = ExecutionStatus.DRAFT

                full_payload = a.get("full_payload", {})
                if not isinstance(full_payload, dict):
                    full_payload = {"value": full_payload}

                actions.append(Action(
                    action_id=str(uuid.uuid4())[:8],
                    incident_id=incident.incident_id,
                    action_type=ActionType(str(a.get("action_type", "jira_ticket")).lower()),
                    destination=str(a.get("destination", "unknown")) or "unknown",
                    payload_preview=str(a.get("payload_preview", "Draft action")) or "Draft action",
                    full_payload=full_payload,
                    approval_status=status,
                    execution_status=exec_status
                ))
            except ValueError as val_err:
                logger.warning("generate_actions.invalid_action incident_id=%s error=%s data=%s", incident.incident_id, val_err, a)

        result = ActionList(actions=actions)
        logger.info("generate_actions.complete incident_id=%s actions=%s", incident.incident_id, len(result.actions))
        return result

    except Exception:
        logger.exception("generate_actions.failed incident_id=%s", incident.incident_id)
        return ActionList(actions=[])
