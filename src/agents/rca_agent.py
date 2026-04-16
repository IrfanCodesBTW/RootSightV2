"""
RootSight — RCA Agent

Generates ranked root-cause hypotheses with confidence scores
and evidence chains. Uses Gemini LLM for reasoning.
"""

from __future__ import annotations
import json

from src.schemas.incident import IncidentHeader
from src.schemas.logs import NormalizedLogSet
from src.schemas.timeline import IncidentTimeline
from src.schemas.rca import RCAHypotheses, RCAHypothesis
from src.integrations.gemini_client import gemini_client
from src.prompts.rca_prompt import RCA_SYSTEM_INSTRUCTION, RCA_USER_PROMPT
from src.utils.logger import get_logger

logger = get_logger("agents.rca")

MAX_LOGS_FOR_RCA = 100


def run(
    header: IncidentHeader,
    timeline: IncidentTimeline,
    log_set: NormalizedLogSet,
) -> RCAHypotheses:
    """
    Generate root-cause hypotheses from timeline and log evidence.

    Args:
        header: Incident context.
        timeline: Reconstructed timeline.
        log_set: Normalized logs for evidence.

    Returns:
        RCAHypotheses with ranked, evidence-backed hypotheses.
    """
    logger.info(f"RCA Agent — analyzing incident {header.incident_id}")

    if not timeline.events and not log_set.logs:
        logger.warning("No timeline or logs — cannot generate meaningful RCA")
        return RCAHypotheses(
            incident_id=header.incident_id,
            hypotheses=[],
            overall_confidence=0,
            reasoning_note="Insufficient data for root cause analysis",
        )

    # Prepare timeline text
    timeline_text = "\n".join(
        f"[{e.timestamp}] [{e.event_type}] [{e.severity}] {e.description}"
        for e in timeline.events
    )
    if not timeline_text:
        timeline_text = "(No timeline events extracted)"

    # Prepare key log evidence (errors and warnings only)
    key_logs = [
        log for log in log_set.logs
        if log.level in ("ERROR", "CRITICAL", "FATAL", "WARN")
    ][:MAX_LOGS_FOR_RCA]
    logs_text = "\n".join(
        f"[{log.timestamp}] [{log.level}] [{log.service}] {log.message}"
        for log in key_logs
    )
    if not logs_text:
        logs_text = "(No error/warning logs found)"

    prompt = RCA_USER_PROMPT.format(
        incident_id=header.incident_id,
        service=header.service,
        alert_title=header.alert_title,
        severity=header.severity,
        timeline_text=timeline_text,
        log_count=len(key_logs),
        logs_text=logs_text,
    )

    try:
        result = gemini_client.generate(
            prompt=prompt,
            system_instruction=RCA_SYSTEM_INSTRUCTION,
            response_schema=RCAHypotheses,
            temperature=0.3,
        )

        if isinstance(result, dict):
            result["incident_id"] = header.incident_id
            hypotheses = RCAHypotheses(**result)
        else:
            logger.warning("Unexpected response format from Gemini")
            hypotheses = _fallback_rca(header, timeline)

    except Exception as e:
        logger.error(f"Gemini RCA generation failed: {e}")
        hypotheses = _fallback_rca(header, timeline)

    # Sort by rank
    hypotheses.hypotheses.sort(key=lambda h: h.rank)

    logger.info(
        f"RCA Agent — complete: {len(hypotheses.hypotheses)} hypotheses, "
        f"overall confidence: {hypotheses.overall_confidence}%"
    )
    return hypotheses


def _fallback_rca(header: IncidentHeader, timeline: IncidentTimeline) -> RCAHypotheses:
    """Generate a basic RCA when Gemini is unavailable."""
    logger.info("Building fallback RCA from timeline events")

    hypotheses = []

    # Check for deploy events
    deploy_events = [e for e in timeline.events if e.event_type == "deploy"]
    error_events = [e for e in timeline.events if e.severity in ("high", "critical")]

    if deploy_events and error_events:
        hypotheses.append(RCAHypothesis(
            rank=1,
            statement=f"Recent deployment may have introduced the issue (deploy detected near error onset)",
            confidence=40,
            supporting_evidence=[
                f"Deploy event at {deploy_events[0].timestamp}: {deploy_events[0].description}",
                f"Error events follow shortly after deployment",
            ],
            contradicting_evidence=["Correlation does not imply causation without deploy diff analysis"],
            missing_information=["Deployment diff/changelog", "Pre-deploy error rates"],
            plausibility="Deploy → error correlation is common but requires verification.",
        ))

    if error_events:
        hypotheses.append(RCAHypothesis(
            rank=len(hypotheses) + 1,
            statement=f"Service error in {header.service} — cause undetermined without LLM analysis",
            confidence=20,
            supporting_evidence=[f"Multiple error events detected: {error_events[0].description}"],
            contradicting_evidence=[],
            missing_information=["Full LLM analysis required for detailed hypothesis"],
            plausibility="Fallback hypothesis — requires AI-powered analysis for better insight.",
        ))

    return RCAHypotheses(
        incident_id=header.incident_id,
        hypotheses=hypotheses,
        overall_confidence=15,
        reasoning_note="Fallback analysis without AI — limited to pattern matching on timeline events.",
    )
