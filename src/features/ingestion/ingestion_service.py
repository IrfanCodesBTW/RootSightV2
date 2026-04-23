import json
import logging
from typing import List, Any
from pathlib import Path
from pydantic import BaseModel
from ...schemas.incident import Incident
from ...utils.config import settings

logger = logging.getLogger(__name__)

class RawEvent(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str
    service: str


def _load_bundle_logs(file_to_load: str) -> list[dict[str, Any]]:
    bundle_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_incidents" / Path(file_to_load).name
    if not bundle_path.exists():
        logger.warning("ingest_logs.bundle_missing bundle_file=%s", file_to_load)
        return []
    with bundle_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        logger.error("ingest_logs.bundle_invalid_shape bundle_file=%s", file_to_load)
        return []
    logs = data.get("logs", [])
    if not isinstance(logs, list):
        logger.error("ingest_logs.logs_invalid_shape bundle_file=%s", file_to_load)
        return []
    return [entry for entry in logs if isinstance(entry, dict)]


async def ingest_logs(incident: Incident, bundle_file: str = None, manual_logs: list[dict[str, Any]] = None) -> List[RawEvent]:
    """
    Fetches, filters, and samples logs for the given incident.
    Returns a maximum of settings.MAX_LOG_LINES (default 100) normalized events.
    """
    logger.info("ingest_logs.start incident_id=%s bundle_file=%s", incident.incident_id, bundle_file)
    raw_logs = []

    try:
        if manual_logs:
            raw_logs = manual_logs
            logger.info("[INGEST] using manual logs count: %d", len(raw_logs))
        elif settings.DEMO_MODE or bundle_file:
            file_to_load = bundle_file if bundle_file else "cdn_502_incident.json"
            raw_logs = _load_bundle_logs(file_to_load)
            logger.info("[INGEST] raw_events count: %d", len(raw_logs))
        else:
            logger.warning("ingest_logs.external_not_configured incident_id=%s", incident.incident_id)
            return []

        filtered_events = []
        for log in raw_logs:
            level = str(log.get("level", "")).upper()
            message = str(log.get("message", ""))

            is_deploy = "deploy" in message.lower()
            is_high_severity = level in ["ERROR", "CRITICAL", "WARN", "WARNING"]

            if is_deploy or is_high_severity:
                filtered_events.append(RawEvent(
                    timestamp=str(log.get("timestamp", "")),
                    level=level,
                    message=message,
                    source=str(log.get("host", log.get("source", "unknown"))),
                    service=str(log.get("service", incident.service))
                ))

        def priority_score(event: RawEvent) -> int:
            if event.level == "CRITICAL": return 0
            if event.level == "ERROR": return 1
            if "deploy" in event.message.lower(): return 2
            if event.level in ["WARN", "WARNING"]: return 3
            return 4

        filtered_events.sort(key=priority_score)
        sampled_events = filtered_events[:settings.MAX_LOG_LINES]
        sampled_events.sort(key=lambda x: x.timestamp)

        logger.info(
            "ingest_logs.complete incident_id=%s loaded=%s sampled=%s",
            incident.incident_id,
            len(raw_logs),
            len(sampled_events),
        )
        return sampled_events

    except Exception as e:
        logger.exception("ingest_logs.failed incident_id=%s", incident.incident_id)
        return []
