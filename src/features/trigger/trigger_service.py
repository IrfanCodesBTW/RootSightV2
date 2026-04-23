import uuid
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlmodel import Session
from ...schemas.incident import IncidentCreate, Incident, IncidentStatus

logger = logging.getLogger(__name__)


def _resolve_bundle_path(bundle_file: str) -> Path:
    safe_name = Path(bundle_file).name
    if safe_name != bundle_file:
        raise HTTPException(status_code=422, detail="Invalid bundle_file path.")
    base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "sample_incidents"
    bundle_path = (base_dir / safe_name).resolve()
    if bundle_path.parent != base_dir.resolve():
        raise HTTPException(status_code=422, detail="Invalid bundle_file location.")
    return bundle_path

def handle_trigger(payload: dict, session: Session) -> dict:
    """
    Handles an incoming incident trigger.
    If 'bundle_file' is in payload, loads a local mock incident bundle.
    Otherwise, treats payload as a PagerDuty/Datadog webhook.
    """
    logger.info("handle_trigger.start keys=%s", sorted(payload.keys()) if isinstance(payload, dict) else "invalid")
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=422, detail="Payload must be a non-empty JSON object.")

    incident_create = None

    if "bundle_file" in payload:
        bundle_path = _resolve_bundle_path(str(payload["bundle_file"]))
        if not bundle_path.exists():
            raise HTTPException(status_code=422, detail=f"Bundle file {bundle_path.name} not found.")

        try:
            with bundle_path.open("r", encoding="utf-8") as f:
                bundle_data = json.load(f)
            if not isinstance(bundle_data, dict) or not isinstance(bundle_data.get("alert"), dict):
                raise ValueError("Bundle is missing a valid 'alert' object.")
            incident_create = IncidentCreate(**bundle_data["alert"])
        except Exception as e:
            logger.exception("handle_trigger.bundle_validation_failed bundle_file=%s", bundle_path.name)
            raise HTTPException(status_code=422, detail=f"Bundle alert validation failed: {str(e)}")

    else:
        try:
            incident_create = IncidentCreate(**payload)
        except Exception as e:
            logger.exception("handle_trigger.webhook_validation_failed")
            raise HTTPException(status_code=422, detail=f"Webhook validation failed: {str(e)}")

    if not incident_create:
        raise HTTPException(status_code=422, detail="Could not extract incident data from payload.")

    incident_id = str(uuid.uuid4())[:8]

    incident = Incident(
        **incident_create.model_dump(),
        incident_id=incident_id,
        detected_at=datetime.now(timezone.utc),
        status=IncidentStatus.ACTIVE
    )
    
    if session:
        try:
            session.add(incident)
            session.commit()
            session.refresh(incident)
        except Exception as e:
            session.rollback()
            logger.exception("handle_trigger.database_error incident_id=%s", incident_id)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info("handle_trigger.complete incident_id=%s", incident_id)
    return {"incident_id": incident_id, "status": "pipeline_started", "incident": incident}
