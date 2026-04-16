"""
RootSight — Impact Agent

Estimates incident severity, blast radius, duration,
and user/business impact. Uses Gemini LLM.
"""

from __future__ import annotations
import json

from src.schemas.incident import IncidentHeader
from src.schemas.timeline import IncidentTimeline
from src.schemas.impact import ImpactAssessment, UserImpact, BusinessImpact
from src.integrations.gemini_client import gemini_client
from src.prompts.impact_prompt import IMPACT_SYSTEM_INSTRUCTION, IMPACT_USER_PROMPT
from src.utils.logger import get_logger

logger = get_logger("agents.impact")


def run(header: IncidentHeader, timeline: IncidentTimeline) -> ImpactAssessment:
    """
    Estimate incident impact from timeline and header context.

    Args:
        header: Incident context.
        timeline: Reconstructed timeline.

    Returns:
        ImpactAssessment with severity, duration, and impact estimates.
    """
    logger.info(f"Impact Agent — assessing impact for {header.incident_id}")

    timeline_text = "\n".join(
        f"[{e.timestamp}] [{e.event_type}] [{e.severity}] {e.description}"
        for e in timeline.events
    )
    if not timeline_text:
        timeline_text = "(No timeline events available)"

    prompt = IMPACT_USER_PROMPT.format(
        incident_id=header.incident_id,
        service=header.service,
        alert_title=header.alert_title,
        severity=header.severity,
        environment=header.environment,
        region=header.region,
        timeline_text=timeline_text,
    )

    try:
        result = gemini_client.generate(
            prompt=prompt,
            system_instruction=IMPACT_SYSTEM_INSTRUCTION,
            response_schema=ImpactAssessment,
            temperature=0.2,
        )

        if isinstance(result, dict):
            result["incident_id"] = header.incident_id
            assessment = ImpactAssessment(**result)
        else:
            logger.warning("Unexpected response format from Gemini")
            assessment = _fallback_impact(header, timeline)

    except Exception as e:
        logger.error(f"Gemini impact assessment failed: {e}")
        assessment = _fallback_impact(header, timeline)

    logger.info(
        f"Impact Agent — complete: {assessment.severity} severity, "
        f"~{assessment.estimated_duration_minutes} min duration, "
        f"{len(assessment.affected_services)} services affected"
    )
    return assessment


def _fallback_impact(header: IncidentHeader, timeline: IncidentTimeline) -> ImpactAssessment:
    """Basic impact estimate when Gemini is unavailable."""
    logger.info("Building fallback impact assessment")

    # Estimate duration from timeline events
    duration = 0
    if timeline.events and len(timeline.events) >= 2:
        try:
            from datetime import datetime
            first = datetime.fromisoformat(timeline.events[0].timestamp.replace("Z", "+00:00"))
            last = datetime.fromisoformat(timeline.events[-1].timestamp.replace("Z", "+00:00"))
            duration = int((last - first).total_seconds() / 60)
        except (ValueError, IndexError):
            pass

    return ImpactAssessment(
        incident_id=header.incident_id,
        affected_services=[header.service],
        severity=header.severity,
        estimated_duration_minutes=duration,
        detection_to_response_minutes=0,
        user_impact=UserImpact(
            estimate="qualitative",
            description=f"Impact assessment unavailable — {header.service} experienced issues",
            confidence=10,
            data_limitation="Full impact analysis requires AI-powered assessment",
        ),
        business_impact=BusinessImpact(
            description="Business impact could not be estimated without AI analysis",
            blast_radius=f"At minimum: {header.service}",
        ),
    )
