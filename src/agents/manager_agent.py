"""
RootSight — Manager Agent

Orchestrates the full incident analysis pipeline.
Runs agents sequentially, validates outputs, handles failures,
and assembles the final IncidentBrief.
"""

from __future__ import annotations
import time
from datetime import datetime

from src.schemas.incident import IncidentBrief, AgentStatus
from src.agents import (
    trigger_agent,
    log_agent,
    timeline_agent,
    rca_agent,
    impact_agent,
    memory_agent,
    action_agent,
)
from src.services import incident_store
from src.utils.logger import get_logger

logger = get_logger("agents.manager")


def run_pipeline(
    payload: dict = None,
    scenario_id: str = None,
) -> IncidentBrief:
    """
    Execute the full incident analysis pipeline.

    Pipeline sequence:
        1. Trigger Agent  →  IncidentHeader
        2. Log Agent      →  NormalizedLogSet
        3. Timeline Agent →  IncidentTimeline
        4. RCA Agent      →  RCAHypotheses
        5. Impact Agent   →  ImpactAssessment
        6. Memory Agent   →  SimilarIncidents
        7. Action Agent   →  ActionPayloads
        8. Manager        →  IncidentBrief (composite)

    Args:
        payload: Alert payload dict. None → demo mode loads mock data.
        scenario_id: Optional scenario ID for loading specific seed data.

    Returns:
        Complete IncidentBrief with all available analysis sections.
    """
    start_time = time.time()
    status = AgentStatus()
    brief_data = {
        "incident_id": "UNKNOWN",
        "header": None,
        "timeline": None,
        "hypotheses": None,
        "impact": None,
        "similar_incidents": None,
        "actions": None,
    }

    # ---------------------------------------------------------------
    # Step 1: Trigger Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 1/7: Trigger Agent")
    logger.info("=" * 60)
    try:
        header = trigger_agent.run(payload)
        status.trigger = "success"
        brief_data["incident_id"] = header.incident_id
        brief_data["header"] = header.model_dump()
    except Exception as e:
        status.trigger = f"failed: {e}"
        logger.error(f"Trigger Agent failed: {e} — pipeline cannot continue")
        return _build_brief(brief_data, status, start_time)

    # ---------------------------------------------------------------
    # Step 2: Log Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 2/7: Log Agent")
    logger.info("=" * 60)
    log_set = None
    try:
        log_set = log_agent.run(header, scenario_id=scenario_id)
        status.log = "success"
    except Exception as e:
        status.log = f"failed: {e}"
        logger.error(f"Log Agent failed: {e}")

    # ---------------------------------------------------------------
    # Step 3: Timeline Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 3/7: Timeline Agent")
    logger.info("=" * 60)
    timeline = None
    try:
        if log_set:
            timeline = timeline_agent.run(header, log_set)
            status.timeline = "success"
            brief_data["timeline"] = timeline.model_dump()
        else:
            status.timeline = "skipped: no logs available"
            logger.warning("Skipping Timeline Agent — no logs")
    except Exception as e:
        status.timeline = f"failed: {e}"
        logger.error(f"Timeline Agent failed: {e}")

    # ---------------------------------------------------------------
    # Step 4: RCA Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 4/7: RCA Agent")
    logger.info("=" * 60)
    hypotheses = None
    try:
        if timeline and log_set:
            hypotheses = rca_agent.run(header, timeline, log_set)
            status.rca = "success"
            brief_data["hypotheses"] = hypotheses.model_dump()
        else:
            status.rca = "skipped: no timeline/logs available"
            logger.warning("Skipping RCA Agent — missing dependencies")
    except Exception as e:
        status.rca = f"failed: {e}"
        logger.error(f"RCA Agent failed: {e}")

    # ---------------------------------------------------------------
    # Step 5: Impact Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 5/7: Impact Agent")
    logger.info("=" * 60)
    impact_result = None
    try:
        if timeline:
            impact_result = impact_agent.run(header, timeline)
            status.impact = "success"
            brief_data["impact"] = impact_result.model_dump()
        else:
            status.impact = "skipped: no timeline available"
            logger.warning("Skipping Impact Agent — no timeline")
    except Exception as e:
        status.impact = f"failed: {e}"
        logger.error(f"Impact Agent failed: {e}")

    # ---------------------------------------------------------------
    # Step 6: Memory Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 6/7: Memory Agent")
    logger.info("=" * 60)
    similar = None
    try:
        if hypotheses:
            similar = memory_agent.run(header, hypotheses)
            status.memory = "success"
            brief_data["similar_incidents"] = similar.model_dump()
        else:
            # Run memory with empty hypotheses
            from src.schemas.rca import RCAHypotheses
            empty_hyp = RCAHypotheses(incident_id=header.incident_id)
            similar = memory_agent.run(header, empty_hyp)
            status.memory = "success"
            brief_data["similar_incidents"] = similar.model_dump()
    except Exception as e:
        status.memory = f"failed: {e}"
        logger.error(f"Memory Agent failed: {e}")

    # ---------------------------------------------------------------
    # Step 7: Action Agent
    # ---------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STEP 7/7: Action Agent")
    logger.info("=" * 60)
    try:
        if hypotheses and impact_result:
            from src.schemas.memory import SimilarIncidents
            sim = similar or SimilarIncidents(
                incident_id=header.incident_id,
                no_match_message="Memory agent did not run",
            )
            actions = action_agent.run(header, hypotheses, impact_result, sim)
            status.action = "success"
            brief_data["actions"] = actions.model_dump()
        else:
            status.action = "skipped: missing RCA or impact data"
            logger.warning("Skipping Action Agent — missing dependencies")
    except Exception as e:
        status.action = f"failed: {e}"
        logger.error(f"Action Agent failed: {e}")

    # ---------------------------------------------------------------
    # Assemble final brief
    # ---------------------------------------------------------------
    brief = _build_brief(brief_data, status, start_time)

    # Save to incident store
    try:
        incident_store.save(brief)
    except Exception as e:
        logger.error(f"Failed to save incident brief: {e}")

    logger.info("=" * 60)
    logger.info(f"Pipeline complete: {brief.incident_id}")
    logger.info(f"Processing time: {brief.processing_time_seconds:.1f}s")
    logger.info(f"Overall confidence: {brief.overall_confidence}%")
    logger.info("=" * 60)

    return brief


def _build_brief(data: dict, status: AgentStatus, start_time: float) -> IncidentBrief:
    """Assemble the final IncidentBrief from collected data."""
    elapsed = time.time() - start_time

    # Calculate overall confidence from available sections
    confidence_sources = []
    if data.get("hypotheses"):
        confidence_sources.append(data["hypotheses"].get("overall_confidence", 0))
    if data.get("timeline"):
        confidence_sources.append(data["timeline"].get("timeline_confidence", 0))

    overall = int(sum(confidence_sources) / len(confidence_sources)) if confidence_sources else 0

    # Build confidence note
    success_count = sum(1 for v in status.model_dump().values() if v == "success")
    total_agents = 7
    notes = []
    if success_count < total_agents:
        notes.append(f"{total_agents - success_count} agent(s) did not complete successfully")
    if overall < 50:
        notes.append("Low confidence — results should be verified manually")
    elif overall < 75:
        notes.append("Moderate confidence — key findings are evidence-backed but gaps exist")
    else:
        notes.append("High confidence — strong evidence chain")

    return IncidentBrief(
        incident_id=data["incident_id"],
        generated_at=datetime.utcnow().isoformat() + "Z",
        processing_time_seconds=round(elapsed, 1),
        header=data.get("header"),
        timeline=data.get("timeline"),
        hypotheses=data.get("hypotheses"),
        impact=data.get("impact"),
        similar_incidents=data.get("similar_incidents"),
        actions=data.get("actions"),
        overall_confidence=overall,
        confidence_note=". ".join(notes),
        agent_status=status,
    )
