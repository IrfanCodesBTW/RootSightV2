"""
RootSight — PagerDuty Integration

Parses PagerDuty V2 webhook payloads into IncidentHeader models.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from src.config import settings, MOCK_DIR
from src.schemas.incident import IncidentHeader, DeployMarker
from src.utils.logger import get_logger

logger = get_logger("integrations.pagerduty")


def parse_webhook(payload: dict) -> IncidentHeader:
    """
    Parse a PagerDuty V2 webhook payload (or simulated payload)
    into an IncidentHeader.

    For demo mode, the payload is expected to already be in
    our simplified format. For real PagerDuty webhooks,
    this would extract from the nested V2 event structure.
    """
    # Support both our simplified format and PagerDuty V2 events
    if "event" in payload and "data" in payload.get("event", {}):
        # Real PagerDuty V2 event structure
        event = payload["event"]
        data = event["data"]
        header = IncidentHeader(
            incident_id=data.get("id", "UNKNOWN"),
            service=data.get("service", {}).get("summary", "unknown-service"),
            alert_title=data.get("title", "Untitled Alert"),
            severity=_map_severity(data.get("urgency", "low")),
            timestamp=data.get("created_at", ""),
            source="pagerduty",
            description=data.get("description", ""),
        )
    else:
        # Simplified / simulated format (direct fields)
        deploy_markers = [
            DeployMarker(**dm) for dm in payload.get("deploy_markers", [])
        ]
        header = IncidentHeader(
            incident_id=payload.get("incident_id", "UNKNOWN"),
            service=payload.get("service", "unknown-service"),
            alert_title=payload.get("alert_title", "Untitled Alert"),
            severity=payload.get("severity", "P3"),
            timestamp=payload.get("timestamp", ""),
            source=payload.get("source", "simulated"),
            environment=payload.get("environment", "production"),
            region=payload.get("region", "us-east-1"),
            description=payload.get("description", ""),
            deploy_markers=deploy_markers,
        )

    logger.info(f"Parsed incident: {header.incident_id} — {header.alert_title}")
    return header


def load_mock_webhook() -> dict:
    """Load the mock PagerDuty webhook from the mock data directory."""
    mock_file = MOCK_DIR / "pagerduty_webhook.json"
    if not mock_file.exists():
        raise FileNotFoundError(f"Mock webhook not found: {mock_file}")
    with open(mock_file) as f:
        return json.load(f)


def _map_severity(urgency: str) -> str:
    """Map PagerDuty urgency to our P1-P4 scale."""
    return {
        "high": "P1",
        "medium": "P2",
        "low": "P3",
    }.get(urgency.lower(), "P3")
