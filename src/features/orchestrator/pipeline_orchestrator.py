import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from ...schemas.incident import IncidentStatus

logger = logging.getLogger(__name__)

# In-memory pipeline state store  (production: migrate to DB via Incident.pipeline_state column)
_pipeline_states: dict[str, dict[str, Any]] = {}

# Pipeline step definitions in execution order
PIPELINE_STEP_KEYS = ["ingestion", "timeline", "rca", "impact", "memory", "actions"]


def _make_step_state() -> dict[str, dict]:
    """Create fresh per-step state dict."""
    return {key: {"status": "PENDING"} for key in PIPELINE_STEP_KEYS}


def _mark_step(state: dict, step: str, status: str, **extra):
    """Update a single step in the pipeline state."""
    state["pipeline_steps"][step] = {"status": status, **extra}
    state["current_step"] = step
    now = datetime.now().isoformat()
    if status == "RUNNING":
        state["pipeline_steps"][step]["started_at"] = now
    elif status in ("COMPLETE", "FAILED"):
        state["pipeline_steps"][step]["completed_at"] = now


async def start_pipeline(payload: dict) -> str:
    """
    Creates the pipeline state, runs ingestion synchronously to parse logs,
    then spawns the remaining pipeline as a background task.
    """
    from ..ingestion.ingestion_service import ingest_logs

    incident_id = str(uuid.uuid4())[:12]
    logger.info("start_pipeline incident_id=%s", incident_id)

    state = {
        "incident_id": incident_id,
        "status": IncidentStatus.RUNNING,
        "pipeline_steps": _make_step_state(),
        "current_step": "ingestion",
        "incident": None,
        "timeline": None,
        "rca": None,
        "impact": None,
        "memory": None,
        "actions": None,
        "error": None,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    _pipeline_states[incident_id] = state

    # --- Step 1: Ingestion (synchronous) ---
    _mark_step(state, "ingestion", "RUNNING")
    try:
        raw_events, incident = await ingest_logs(payload, incident_id)
        state["incident"] = incident.model_dump(mode="json") if hasattr(incident, "model_dump") else incident
        state["raw_events_count"] = len(raw_events) if raw_events else 0
        _mark_step(state, "ingestion", "COMPLETE")
    except Exception as e:
        logger.exception("start_pipeline.ingestion_failed incident_id=%s", incident_id)
        _mark_step(state, "ingestion", "FAILED")
        state["status"] = IncidentStatus.FAILED
        state["error"] = f"Ingestion failed: {e}"
        return incident_id

    # Launch remaining pipeline steps in background
    asyncio.create_task(_run_pipeline_async(incident_id, raw_events, incident))
    return incident_id


async def _run_pipeline_async(incident_id: str, raw_events, incident):
    """
    Execute pipeline steps 2-6 sequentially as a background task.
    Each step updates the shared state dict so the frontend can poll progress.
    """
    from ..timeline.timeline_module import build_timeline
    from ..rca.rca_module import analyze_root_cause
    from ..impact.impact_module import analyze_impact
    from ..memory.memory_module import find_similar_incidents
    from ..action.action_module import generate_actions

    state = _pipeline_states.get(incident_id)
    if not state:
        logger.error("_run_pipeline_async.state_missing incident_id=%s", incident_id)
        return

    try:
        # --- Step 2: Timeline ---
        _mark_step(state, "timeline", "RUNNING")
        try:
            event_list = await build_timeline(raw_events, incident)
            state["timeline"] = event_list.model_dump(mode="json") if hasattr(event_list, "model_dump") else event_list
            _mark_step(state, "timeline", "COMPLETE")
        except Exception:
            logger.exception("pipeline.timeline_failed incident_id=%s", incident_id)
            _mark_step(state, "timeline", "FAILED")
            # Continue with empty timeline
            from ...schemas.event import EventList

            event_list = EventList(events=[], timeline_confidence=0, gaps_detected=0, total_events=0)
            state["timeline"] = event_list.model_dump(mode="json")

        # --- Step 3: RCA ---
        _mark_step(state, "rca", "RUNNING")
        try:
            hypothesis_list = await analyze_root_cause(event_list, incident)
            state["rca"] = (
                hypothesis_list.model_dump(mode="json") if hasattr(hypothesis_list, "model_dump") else hypothesis_list
            )
            _mark_step(state, "rca", "COMPLETE")
        except Exception:
            logger.exception("pipeline.rca_failed incident_id=%s", incident_id)
            _mark_step(state, "rca", "FAILED")
            from ...schemas.hypothesis import HypothesisList

            hypothesis_list = HypothesisList(hypotheses=[], analysis_confidence=0, is_low_confidence=True)
            state["rca"] = hypothesis_list.model_dump(mode="json")

        # --- Step 4: Impact ---
        _mark_step(state, "impact", "RUNNING")
        try:
            impact = await analyze_impact(incident, event_list, hypothesis_list)
            state["impact"] = impact.model_dump(mode="json") if hasattr(impact, "model_dump") else impact
            _mark_step(state, "impact", "COMPLETE")
        except Exception:
            logger.exception("pipeline.impact_failed incident_id=%s", incident_id)
            _mark_step(state, "impact", "FAILED")
            impact = None

        # --- Step 5: Memory ---
        _mark_step(state, "memory", "RUNNING")
        try:
            memory_result = await find_similar_incidents(incident, hypothesis_list)
            state["memory"] = (
                memory_result.model_dump(mode="json") if hasattr(memory_result, "model_dump") else memory_result
            )
            _mark_step(state, "memory", "COMPLETE")
        except Exception:
            logger.exception("pipeline.memory_failed incident_id=%s", incident_id)
            _mark_step(state, "memory", "FAILED")

        # --- Step 6: Actions ---
        _mark_step(state, "actions", "RUNNING")
        try:
            if impact is not None:
                actions = await generate_actions(incident, impact, hypothesis_list)
            else:
                # Create a minimal impact for action generation
                from ...schemas.impact import Impact, SeverityBand

                minimal_impact = Impact(
                    incident_id=incident.incident_id,
                    affected_services=[incident.service],
                    severity_band=SeverityBand.MEDIUM,
                    probable_user_impact="Unknown",
                )
                actions = await generate_actions(incident, minimal_impact, hypothesis_list)
            state["actions"] = actions.model_dump(mode="json") if hasattr(actions, "model_dump") else actions
            _mark_step(state, "actions", "COMPLETE")
        except Exception:
            logger.exception("pipeline.actions_failed incident_id=%s", incident_id)
            _mark_step(state, "actions", "FAILED")

        # Determine final status: completed if all critical steps succeeded
        failed_steps = [k for k, v in state["pipeline_steps"].items() if v["status"] == "FAILED"]
        if not failed_steps:
            state["status"] = IncidentStatus.COMPLETED
        elif len(failed_steps) >= 3:
            state["status"] = IncidentStatus.FAILED
        else:
            state["status"] = IncidentStatus.PARTIAL

        state["completed_at"] = datetime.now().isoformat()
        logger.info(
            "pipeline.complete incident_id=%s status=%s failed_steps=%s", incident_id, state["status"], failed_steps
        )

    except Exception as e:
        logger.exception("pipeline.critical_failure incident_id=%s", incident_id)
        state["status"] = "failed"
        state["error"] = f"Pipeline crashed: {e}"
        state["completed_at"] = datetime.now().isoformat()


def get_pipeline_state(incident_id: str) -> Optional[dict]:
    """Return the full pipeline state for an incident."""
    return _pipeline_states.get(incident_id)


def get_all_incidents(page: int = 1, limit: int = 20) -> dict:
    """Return paginated incident list from in-memory state."""
    all_items = list(_pipeline_states.values())
    # Sort by started_at descending
    all_items.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    total = len(all_items)
    start = (page - 1) * limit
    end = start + limit
    items = all_items[start:end]
    return {"items": items, "total": total, "page": page, "limit": limit}
