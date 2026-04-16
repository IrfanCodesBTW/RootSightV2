"""
RootSight — Action Agent

Generates follow-up action drafts: Jira tickets, Slack messages,
diagnostic checks, and mitigation steps. Uses Gemini LLM.
"""

from __future__ import annotations
import json

from src.schemas.incident import IncidentHeader
from src.schemas.rca import RCAHypotheses
from src.schemas.impact import ImpactAssessment
from src.schemas.memory import SimilarIncidents
from src.schemas.actions import ActionPayloads, JiraTicket, SlackMessage, MitigationAction
from src.integrations.gemini_client import gemini_client
from src.prompts.action_prompt import ACTION_SYSTEM_INSTRUCTION, ACTION_USER_PROMPT
from src.utils.logger import get_logger

logger = get_logger("agents.action")


def run(
    header: IncidentHeader,
    hypotheses: RCAHypotheses,
    impact: ImpactAssessment,
    similar: SimilarIncidents,
) -> ActionPayloads:
    """
    Generate follow-up action drafts from incident analysis.

    Args:
        header: Incident context.
        hypotheses: RCA hypotheses.
        impact: Impact assessment.
        similar: Similar past incidents.

    Returns:
        ActionPayloads with Jira, Slack, mitigation, and follow-up drafts.
    """
    logger.info(f"Action Agent — generating actions for {header.incident_id}")

    # Prepare context text for the prompt
    hypotheses_text = ""
    for h in hypotheses.hypotheses:
        hypotheses_text += (
            f"  Hypothesis {h.rank} (confidence: {h.confidence}%): {h.statement}\n"
            f"  Supporting: {', '.join(h.supporting_evidence[:3])}\n\n"
        )
    if not hypotheses_text:
        hypotheses_text = "(No hypotheses generated)"

    impact_text = (
        f"Severity: {impact.severity}\n"
        f"Affected services: {', '.join(impact.affected_services)}\n"
        f"Duration: ~{impact.estimated_duration_minutes} minutes\n"
        f"User impact: {impact.user_impact.description}\n"
        f"Blast radius: {impact.business_impact.blast_radius}"
    )

    similar_text = ""
    if similar.matches:
        for m in similar.matches:
            similar_text += (
                f"  {m.matched_incident_id}: {m.title} "
                f"(similarity: {m.similarity_score})\n"
                f"  Prior cause: {m.previous_root_cause}\n"
                f"  Prior fix: {m.previous_resolution}\n\n"
            )
    else:
        similar_text = similar.no_match_message or "(No similar incidents found)"

    prompt = ACTION_USER_PROMPT.format(
        incident_id=header.incident_id,
        service=header.service,
        alert_title=header.alert_title,
        severity=header.severity,
        hypotheses_text=hypotheses_text,
        impact_text=impact_text,
        similar_text=similar_text,
    )

    try:
        result = gemini_client.generate(
            prompt=prompt,
            system_instruction=ACTION_SYSTEM_INSTRUCTION,
            response_schema=ActionPayloads,
            temperature=0.3,
        )

        if isinstance(result, dict):
            result["incident_id"] = header.incident_id
            actions = ActionPayloads(**result)
        else:
            logger.warning("Unexpected response format from Gemini")
            actions = _fallback_actions(header, hypotheses, impact)

    except Exception as e:
        logger.error(f"Gemini action generation failed: {e}")
        actions = _fallback_actions(header, hypotheses, impact)

    logger.info(
        f"Action Agent — complete: {len(actions.immediate_checks)} checks, "
        f"{len(actions.mitigation)} mitigations, Jira + Slack drafts ready"
    )
    return actions


def _fallback_actions(
    header: IncidentHeader,
    hypotheses: RCAHypotheses,
    impact: ImpactAssessment,
) -> ActionPayloads:
    """Generate basic actions when Gemini is unavailable."""
    logger.info("Building fallback action payloads")

    top_hyp = hypotheses.hypotheses[0].statement if hypotheses.hypotheses else "Unknown root cause"

    return ActionPayloads(
        incident_id=header.incident_id,
        immediate_checks=[
            f"Check {header.service} pod/container logs for active errors",
            f"Verify {header.service} health endpoint status",
            "Review recent deployments and config changes",
        ],
        mitigation=[
            MitigationAction(
                action=f"Consider rolling back {header.service} to last known good version",
                risk_level="medium",
                approval_required=True,
                reason="Standard mitigation for service errors",
            ),
        ],
        jira_ticket=JiraTicket(
            project="INCIDENT",
            summary=f"[{impact.severity}] {header.alert_title}",
            description=(
                f"## Incident: {header.incident_id}\n\n"
                f"**Service:** {header.service}\n"
                f"**Severity:** {impact.severity}\n"
                f"**Duration:** ~{impact.estimated_duration_minutes} minutes\n\n"
                f"### Top Hypothesis\n{top_hyp}\n\n"
                f"### Impact\n{impact.user_impact.description}\n\n"
                f"*Generated by RootSight (fallback mode)*"
            ),
            priority="Highest" if impact.severity in ("P1", "P2") else "High",
            labels=["incident", header.service, impact.severity.lower()],
            assignee_suggestion=f"{header.service}-team-oncall",
        ),
        slack_message=SlackMessage(
            channel="#incidents",
            text=(
                f"{'🔴' if impact.severity == 'P1' else '🟠' if impact.severity == 'P2' else '🟡'} "
                f"**{impact.severity} Incident — {header.service}**\n"
                f"{header.alert_title}\n"
                f"Duration: ~{impact.estimated_duration_minutes} min\n"
                f"Hypothesis: {top_hyp}\n"
                f"_Generated by RootSight_"
            ),
        ),
        follow_up=[
            "Write post-mortem using incident brief as starting point",
            f"Review monitoring coverage for {header.service}",
            "Update runbook with learnings from this incident",
        ],
    )
