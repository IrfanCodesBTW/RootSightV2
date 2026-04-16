"""
RootSight — Timeline Agent

Extracts meaningful events from normalized logs and
reconstructs a chronological incident timeline.
Uses Gemini LLM for event extraction and classification.
"""

from __future__ import annotations
import json

from src.schemas.incident import IncidentHeader
from src.schemas.logs import NormalizedLogSet
from src.schemas.timeline import IncidentTimeline, TimelineEvent
from src.integrations.gemini_client import gemini_client
from src.prompts.timeline_prompt import TIMELINE_SYSTEM_INSTRUCTION, TIMELINE_USER_PROMPT
from src.utils.logger import get_logger

logger = get_logger("agents.timeline")

# Max log entries to send to the LLM (to stay within context limits)
MAX_LOGS_FOR_LLM = 200


def run(header: IncidentHeader, log_set: NormalizedLogSet) -> IncidentTimeline:
    """
    Reconstruct incident timeline from normalized logs using Gemini.

    Args:
        header: Incident header with context.
        log_set: Normalized log set.

    Returns:
        IncidentTimeline with chronological events.
    """
    logger.info(f"Timeline Agent — building timeline for {header.incident_id}")

    if not log_set.logs:
        logger.warning("No logs to build timeline from")
        return IncidentTimeline(
            incident_id=header.incident_id,
            events=[],
            timeline_confidence=0,
            gaps=["No log data available for timeline reconstruction"],
        )

    # Prepare logs for LLM (truncate if too many)
    logs_for_llm = log_set.logs[:MAX_LOGS_FOR_LLM]
    logs_text = "\n".join(
        f"[{log.timestamp}] [{log.level}] [{log.service}] {log.message}"
        for log in logs_for_llm
    )

    if len(log_set.logs) > MAX_LOGS_FOR_LLM:
        logs_text += f"\n\n... ({len(log_set.logs) - MAX_LOGS_FOR_LLM} additional log entries truncated)"

    # Build the prompt
    prompt = TIMELINE_USER_PROMPT.format(
        incident_id=header.incident_id,
        service=header.service,
        alert_title=header.alert_title,
        severity=header.severity,
        timestamp=header.timestamp,
        log_count=len(logs_for_llm),
        logs_text=logs_text,
    )

    try:
        result = gemini_client.generate(
            prompt=prompt,
            system_instruction=TIMELINE_SYSTEM_INSTRUCTION,
            response_schema=IncidentTimeline,
            temperature=0.2,
        )

        if isinstance(result, dict):
            # Ensure incident_id is set
            result["incident_id"] = header.incident_id
            timeline = IncidentTimeline(**result)
        else:
            logger.warning("Unexpected response format from Gemini")
            timeline = _fallback_timeline(header, log_set)

    except Exception as e:
        logger.error(f"Gemini timeline generation failed: {e}")
        timeline = _fallback_timeline(header, log_set)

    # Sort events chronologically
    timeline.events.sort(key=lambda e: e.timestamp)

    logger.info(
        f"Timeline Agent — complete: {len(timeline.events)} events, "
        f"confidence: {timeline.timeline_confidence}%"
    )
    return timeline


def _fallback_timeline(header: IncidentHeader, log_set: NormalizedLogSet) -> IncidentTimeline:
    """
    Build a basic timeline from logs without LLM assistance.
    Used when Gemini is unavailable.
    """
    logger.info("Building fallback timeline from error logs")
    events = []

    # Add deploy markers as events
    for dm in header.deploy_markers:
        events.append(TimelineEvent(
            timestamp=dm.deployed_at,
            event_type="deploy",
            description=f"Deployment {dm.version} by {dm.deployer}",
            evidence_source="deploy marker",
            severity="info",
        ))

    # Extract ERROR and WARN level logs as events
    seen_messages = set()
    for log in log_set.logs:
        if log.level in ("ERROR", "CRITICAL", "FATAL"):
            # Deduplicate by message prefix
            msg_key = log.message[:80]
            if msg_key not in seen_messages:
                seen_messages.add(msg_key)
                events.append(TimelineEvent(
                    timestamp=log.timestamp,
                    event_type="error_spike",
                    description=log.message[:200],
                    evidence_source="application logs",
                    severity="critical" if log.level in ("CRITICAL", "FATAL") else "high",
                ))
        elif log.level == "WARN":
            msg_key = log.message[:80]
            if msg_key not in seen_messages:
                seen_messages.add(msg_key)
                events.append(TimelineEvent(
                    timestamp=log.timestamp,
                    event_type="other",
                    description=log.message[:200],
                    evidence_source="application logs",
                    severity="warning",
                ))

    events.sort(key=lambda e: e.timestamp)

    return IncidentTimeline(
        incident_id=header.incident_id,
        events=events[:20],  # Limit fallback events
        timeline_confidence=25,
        gaps=["Timeline built without AI analysis — may be incomplete or noisy"],
    )
