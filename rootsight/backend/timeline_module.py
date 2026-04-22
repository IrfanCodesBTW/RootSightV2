import json
import logging
import uuid
from typing import List
from .schemas.incident import Incident
from .schemas.event import EventList, Event, EventType
from .ingestion_service import RawEvent
from .llm_clients.gemini_client import generate

logger = logging.getLogger(__name__)

async def build_timeline(raw_events: List[RawEvent], incident: Incident) -> EventList:
    """
    Calls Gemini to extract an ordered, structured timeline from sampled raw events.
    """
    logger.info("build_timeline.start incident_id=%s raw_events=%s", incident.incident_id, len(raw_events))
    if not raw_events:
        logger.warning("build_timeline.empty_input incident_id=%s", incident.incident_id)
        return EventList(events=[], timeline_confidence=0, gaps_detected=0, total_events=0, analysis_note="No logs ingested.")

    try:
        serialized_raw_events = json.dumps([e.model_dump(mode="json") for e in raw_events], indent=2)

        prompt = f"""
        You are an expert SRE analyzing a production incident.
        Incident: {incident.title} on {incident.service} at {incident.started_at}

        Extract a clean, ordered timeline from these log events.
        Focus on: deploys, errors, spikes, failures, recoveries, config changes.
        Ignore: repeated health checks, duplicate errors, routine noise.

        Logs:
        {serialized_raw_events}

        Return ONLY valid JSON matching this schema:
        {{
          "events": [
            {{
              "timestamp": "ISO8601",
              "event_type": "deploy|error_spike|latency_spike|cpu_spike|db_failure|timeout|failover|recovery|rollback|dependency_failure|config_change|unknown",
              "description": "concise description of what happened",
              "evidence_source": "log line or data source",
              "confidence": 0-100
            }}
          ],
          "timeline_confidence": 0-100,
          "gaps_detected": number,
          "analysis_note": "optional note about data quality"
        }}
        """

        response_dict = await generate(prompt)
        if not isinstance(response_dict, dict):
            raise ValueError("Timeline LLM response is not a JSON object.")

        events = []
        raw_event_items = response_dict.get("events", [])
        if not isinstance(raw_event_items, list):
            raw_event_items = []

        for e in raw_event_items:
            if not isinstance(e, dict):
                logger.warning("build_timeline.invalid_event_shape incident_id=%s event=%s", incident.incident_id, e)
                continue
            try:
                timestamp = e.get("timestamp")
                if not timestamp:
                    raise ValueError("Missing event timestamp.")
                event_type_value = str(e.get("event_type", "unknown")).lower()
                if event_type_value not in {item.value for item in EventType}:
                    event_type_value = EventType.UNKNOWN.value
                events.append(Event(
                    event_id=str(uuid.uuid4())[:8],
                    incident_id=incident.incident_id,
                    timestamp=timestamp,
                    event_type=EventType(event_type_value),
                    description=e.get("description") or "No description provided.",
                    evidence_source=e.get("evidence_source") or "Unknown source",
                    confidence=int(e.get("confidence", 50))
                ))
            except ValueError as val_err:
                logger.warning("build_timeline.invalid_event incident_id=%s error=%s data=%s", incident.incident_id, val_err, e)

        event_list = EventList(
            events=events,
            timeline_confidence=int(response_dict.get("timeline_confidence", 50)),
            gaps_detected=int(response_dict.get("gaps_detected", 0)),
            total_events=len(events),
            analysis_note=response_dict.get("analysis_note")
        )
        logger.info("build_timeline.complete incident_id=%s events=%s", incident.incident_id, len(event_list.events))
        return event_list

    except Exception as e:
        logger.exception("build_timeline.failed incident_id=%s", incident.incident_id)
        return EventList(events=[], timeline_confidence=0, gaps_detected=0, total_events=0, analysis_note="LLM failure.")
