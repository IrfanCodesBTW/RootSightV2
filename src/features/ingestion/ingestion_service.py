import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any, Tuple

from pydantic import BaseModel
from ...schemas.incident import Incident, Severity, IncidentStatus
from ...utils.config import settings

logger = logging.getLogger(__name__)


class RawEvent(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str
    service: str


def _load_bundle_logs(file_to_load: str) -> list[dict[str, Any]]:
    """Load logs from a bundle JSON file. Handles missing keys and files gracefully."""
    # Look in src/data/sample_incidents relative to this file
    bundle_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_incidents" / Path(file_to_load).name
    if not bundle_path.exists():
        logger.warning("ingest_logs.bundle_missing bundle_file=%s path=%s", file_to_load, bundle_path)
        return []
    try:
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
    except json.JSONDecodeError as e:
        logger.error("ingest_logs.bundle_json_decode_failed bundle_file=%s error=%s", file_to_load, e)
        return []
    except Exception as e:
        logger.error("ingest_logs.bundle_read_failed bundle_file=%s error=%s", file_to_load, e)
        return []


async def ingest_logs(payload: dict, incident_id: str) -> Tuple[List[RawEvent], Incident]:
    """
    Parses the trigger payload (which may contain manual logs or a bundle_file reference),
    creates the Incident record, and extracts normalized logs.

    On log source failure, returns empty logs and sets incident status to DEGRADED (not raises).
    """
    logger.info("ingest_logs.start incident_id=%s payload_keys=%s", incident_id, sorted(payload.keys()))

    # 1. Create the Incident object from payload or defaults
    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_id=incident_id,
        title=payload.get("title") or f"Incident {incident_id}",
        service=payload.get("service") or "unknown-service",
        severity=payload.get("severity") or Severity.P2,
        environment=payload.get("environment") or "production",
        region=payload.get("region") or "us-east-1",
        source=payload.get("source") or "api",
        description=payload.get("description"),
        started_at=payload.get("started_at") or now,
        detected_at=now,
        status=IncidentStatus.RUNNING,
    )

    # 2. Extract logs
    raw_logs = []
    bundle_file = payload.get("bundle_file")
    manual_logs = payload.get("logs")
    degraded = False

    if manual_logs:
        if isinstance(manual_logs, list):
            raw_logs = manual_logs
            logger.info("[INGEST] using manual logs count: %d", len(raw_logs))
        else:
            logger.warning("[INGEST] manual logs is not a list, ignoring")
            degraded = True
    elif bundle_file or settings.DEMO_MODE:
        file_to_load = bundle_file if bundle_file else "cdn_502_incident.json"
        raw_logs = _load_bundle_logs(file_to_load)
        if not raw_logs and bundle_file:
            logger.warning("[INGEST] bundle_file unreachable or empty, setting DEGRADED flag")
            degraded = True
        else:
            logger.info("[INGEST] loaded bundle_file=%s count=%d", file_to_load, len(raw_logs))

    if degraded:
        incident.status = IncidentStatus.DEGRADED

    # 3. Filter and Normalize
    filtered_events = []
    for log in raw_logs:
        try:
            level = str(log.get("level", "INFO")).upper()
            message = str(log.get("message", ""))

            # Simple heuristic: keep ERROR/WARN and anything mentioning "deploy"
            is_deploy = "deploy" in message.lower()
            is_high_severity = level in ["ERROR", "CRITICAL", "WARN", "WARNING", "FATAL"]

            if is_deploy or is_high_severity:
                filtered_events.append(
                    RawEvent(
                        timestamp=str(log.get("timestamp", now.isoformat())),
                        level=level,
                        message=message,
                        source=str(log.get("host", log.get("source", "unknown"))),
                        service=str(log.get("service", incident.service)),
                    )
                )
        except Exception:
            continue

    # 4. Sort and Sample (enforce 100-line cap)
    def priority_score(event: RawEvent) -> int:
        if event.level in ["CRITICAL", "FATAL"]:
            return 0
        if event.level == "ERROR":
            return 1
        if "deploy" in event.message.lower():
            return 2
        if event.level in ["WARN", "WARNING"]:
            return 3
        return 4

    filtered_events.sort(key=priority_score)
    sampled_events = filtered_events[: settings.MAX_LOG_LINES]

    # Final sort by timestamp for timeline building
    try:
        sampled_events.sort(key=lambda x: x.timestamp)
    except Exception:
        pass

    logger.info(
        "ingest_logs.complete incident_id=%s filtered=%s sampled=%s degraded=%s",
        incident_id,
        len(filtered_events),
        len(sampled_events),
        degraded,
    )
    return sampled_events, incident
