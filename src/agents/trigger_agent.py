"""
RootSight — Trigger Agent

Parses and validates incoming alert payloads.
Produces an IncidentHeader to start the pipeline.
No LLM required.
"""

from __future__ import annotations

from src.schemas.incident import IncidentHeader
from src.integrations.pagerduty import parse_webhook, load_mock_webhook
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("agents.trigger")


def run(payload: dict = None) -> IncidentHeader:
    """
    Parse an incoming alert payload into an IncidentHeader.

    Args:
        payload: Alert payload dict. If None and DEMO_MODE is on,
                 loads the mock webhook payload.

    Returns:
        Validated IncidentHeader.

    Raises:
        ValueError: If the payload is malformed or missing required fields.
    """
    logger.info("Trigger Agent — starting")

    if payload is None:
        if settings.DEMO_MODE:
            logger.info("Demo mode — loading mock webhook")
            payload = load_mock_webhook()
        else:
            raise ValueError("No alert payload provided and DEMO_MODE is off")

    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict payload, got {type(payload).__name__}")

    try:
        header = parse_webhook(payload)
    except Exception as e:
        logger.error(f"Failed to parse webhook: {e}")
        raise ValueError(f"Invalid alert payload: {e}") from e

    # Validate required fields
    if not header.incident_id or header.incident_id == "UNKNOWN":
        raise ValueError("Missing incident_id in alert payload")
    if not header.service or header.service == "unknown-service":
        logger.warning("Service not identified in alert — defaulting to 'unknown-service'")
    if not header.timestamp:
        logger.warning("No timestamp in alert payload")

    logger.info(
        f"Trigger Agent — complete: {header.incident_id} "
        f"[{header.severity}] {header.alert_title}"
    )
    return header
