import logging
import uuid
import json
from ...schemas.incident import Incident
from ...schemas.impact import Impact
from ...schemas.hypothesis import HypothesisList
from ...schemas.action import ActionList, Action, ActionType, ApprovalStatus, ExecutionStatus
from pydantic import ValidationError
from ..llm_clients.groq_client import format_json
from ..llm_clients.gemini_client import generate
from ..llm_clients.errors import strip_fences, enforce_token_budget

logger = logging.getLogger(__name__)


def _fallback_action(incident_id: str) -> ActionList:
    """Return a single 'manual review' action as fallback when LLM fails."""
    fallback = Action(
        action_id=str(uuid.uuid4())[:8],
        incident_id=incident_id,
        action_type=ActionType.MANUAL_REVIEW,
        destination="incident-response-team",
        payload_preview="Automated action generation failed. Manual review required.",
        full_payload={"message": "Please manually review this incident and determine next steps."},
        approval_status=ApprovalStatus.PENDING,
        execution_status=ExecutionStatus.DRAFT,
    )
    logger.warning("generate_actions.fallback incident_id=%s", incident_id)
    return ActionList(actions=[fallback])


async def generate_actions(incident: Incident, impact: Impact, hypothesis_list: HypothesisList) -> ActionList:
    """
    Calls Groq (Llama 3) to rapidly format incident data into actionable drafts
    like a Jira ticket and a Slack update.

    Always returns at least 1 action. Jira/Slack draft fields are never None (empty string default).
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
        Impact: {impact.business_impact_summary or "Unknown"}
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

        prompt = enforce_token_budget(prompt)
        response_dict = await format_json(prompt)

        # format_json returns None on failure
        if response_dict is None:
            logger.warning("generate_actions.llm_returned_none incident_id=%s", incident.incident_id)
            return _fallback_action(incident.incident_id)

        if not isinstance(response_dict, dict):
            raise ValueError("Groq action response is not a JSON object.")

        # Inject mandatory fields for Pydantic validation
        raw_actions = response_dict.get("actions", [])
        if isinstance(raw_actions, list):
            for a in raw_actions:
                if isinstance(a, dict):
                    if "action_id" not in a:
                        a["action_id"] = str(uuid.uuid4())[:8]
                    if "incident_id" not in a:
                        a["incident_id"] = incident.incident_id
                    if "approval_status" not in a:
                        a["approval_status"] = ApprovalStatus.PENDING.value
                    if "execution_status" not in a:
                        a["execution_status"] = ExecutionStatus.DRAFT.value
                    # Ensure action_type is valid
                    at = str(a.get("action_type", "jira_ticket")).lower()
                    if at not in {item.value for item in ActionType}:
                        a["action_type"] = "jira_ticket"
                    # Ensure Jira/Slack fields are never None — use empty string default
                    if a.get("destination") is None:
                        a["destination"] = ""
                    if a.get("payload_preview") is None:
                        a["payload_preview"] = ""
                    if a.get("full_payload") is None:
                        a["full_payload"] = {}
                    # Sanitize full_payload: replace None values with empty strings
                    if isinstance(a.get("full_payload"), dict):
                        a["full_payload"] = {
                            k: (v if v is not None else "") for k, v in a["full_payload"].items()
                        }

        try:
            result = ActionList(**response_dict)
            if not result.actions:
                return _fallback_action(incident.incident_id)
            logger.info(
                "generate_actions.complete incident_id=%s actions=%s", incident.incident_id, len(result.actions)
            )
            return result
        except ValidationError as e:
            logger.error("generate_actions.validation_failed incident_id=%s error=%s", incident.incident_id, e)
            return _fallback_action(incident.incident_id)

    except Exception:
        logger.exception("generate_actions.failed incident_id=%s", incident.incident_id)
        return _fallback_action(incident.incident_id)


async def draft_recovery_script_action(incident_id: str, incident_data: dict, rca_data: dict) -> str:
    """
    Generates a recovery bash script based on the incident state and RCA.
    """
    prompt = f"""
    [SYSTEM] You are an expert SRE. Draft a safe, idempotent bash recovery script for the following incident.
    [INCIDENT] {json.dumps(incident_data)}
    [RCA] {json.dumps(rca_data)}

    Guidelines:
    1. Include safety checks (e.g. check if service is running).
    2. Add comments explaining each step.
    3. Return ONLY a JSON object with a single "script" key containing the bash script as a string.
    """
    try:
        prompt = enforce_token_budget(prompt)
        raw_response = await generate(prompt)
        # generate() returns a dict — extract the script text from it
        if isinstance(raw_response, dict):
            script = raw_response.get("script", "")
            if not script:
                # Fallback: try to reconstruct from the dict
                script = json.dumps(raw_response, indent=2)
            return script
        # If somehow we got a string, strip fences
        return strip_fences(str(raw_response))
    except Exception as e:
        logger.exception("draft_recovery_script_action.failed incident_id=%s", incident_id)
        raise e
