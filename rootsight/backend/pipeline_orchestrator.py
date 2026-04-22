import asyncio
import logging
from typing import Dict, Any
from .trigger_service import handle_trigger
from .ingestion_service import ingest_logs
from .timeline_module import build_timeline
from .rca_module import analyze_root_cause
from .impact_module import analyze_impact
from .memory_module import find_similar_incidents
from .action_module import generate_actions
from .schemas.incident import IncidentStatus

logger = logging.getLogger(__name__)

# In-memory state store for MVP demo purposes. 
# In production, this would be updated in the SQLite database via SQLModel.
pipeline_state: Dict[str, Dict[str, Any]] = {}

async def run_pipeline_async(incident_id: str, incident: Any, raw_events: list):
    """
    Background task to run the AI pipeline modules sequentially.
    Updates `pipeline_state` at each step.
    """
    state = pipeline_state.setdefault(incident_id, {"incident_id": incident_id, "incident": incident.model_dump()})
    try:
        logger.info("run_pipeline_async.start incident_id=%s raw_events=%s", incident_id, len(raw_events))
        state["status"] = "building_timeline"
        event_list = await build_timeline(raw_events, incident)
        state["timeline"] = event_list.model_dump()

        state["status"] = "analyzing_rca"
        hypothesis_list = await analyze_root_cause(event_list, incident)
        state["rca"] = hypothesis_list.model_dump()

        state["status"] = "estimating_impact"
        impact = await analyze_impact(incident, event_list, hypothesis_list)
        state["impact"] = impact.model_dump()

        state["status"] = "searching_memory"
        similar_incidents = await find_similar_incidents(incident, hypothesis_list)
        state["memory"] = similar_incidents.model_dump()

        state["status"] = "drafting_actions"
        actions = await generate_actions(incident, impact, hypothesis_list)
        state["actions"] = actions.model_dump()

        state["status"] = "completed"
        state["incident"]["status"] = IncidentStatus.RESOLVED.value
        logger.info("run_pipeline_async.complete incident_id=%s", incident_id)

    except Exception as exc:
        logger.exception("run_pipeline_async.failed incident_id=%s", incident_id)
        state["status"] = "failed"
        state["error"] = str(exc)

from .storage.database import engine
from sqlmodel import Session

async def start_pipeline(payload: dict) -> str:
    """
    Entry point. Validates payload, creates incident, starts background task.
    """
    logger.info("start_pipeline.start keys=%s", sorted(payload.keys()) if isinstance(payload, dict) else "invalid")
    with Session(engine) as session:
        trigger_result = handle_trigger(payload, session)
        incident_id = trigger_result["incident_id"]
        incident = trigger_result["incident"]
        pipeline_state[incident_id] = {
            "incident_id": incident_id,
            "incident": incident.model_dump(),
            "status": "starting",
            "timeline": None,
            "rca": None,
            "impact": None,
            "memory": None,
            "actions": None,
            "error": None
        }

    bundle_file = payload.get("bundle_file")
    try:
        raw_events = await ingest_logs(incident, bundle_file=bundle_file)
        pipeline_state[incident_id]["status"] = "started"
    except Exception as exc:
        pipeline_state[incident_id]["status"] = "failed"
        pipeline_state[incident_id]["error"] = str(exc)
        logger.exception("start_pipeline.ingest_failed incident_id=%s", incident_id)
        raise

    asyncio.create_task(run_pipeline_async(incident_id, incident, raw_events))

    logger.info("start_pipeline.complete incident_id=%s", incident_id)
    return incident_id

def get_pipeline_state(incident_id: str) -> dict:
    return pipeline_state.get(incident_id)

def get_all_incidents() -> list:
    return [state["incident"] for state in pipeline_state.values()]
