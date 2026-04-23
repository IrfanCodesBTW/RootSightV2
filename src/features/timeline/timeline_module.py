import json
import logging
import uuid
from typing import List
from ...schemas.incident import Incident
from ...schemas.event import EventList, EventType
from ..ingestion.ingestion_service import RawEvent
from pydantic import ValidationError
from ..llm_clients.gemini_client import generate, enforce_token_budget

logger = logging.getLogger(__name__)


def _fallback_timeline(incident: Incident, note: str = "Falling back due to error.") -> EventList:
    return EventList(events=[], timeline_confidence=0, gaps_detected=0, total_events=0, analysis_note=note)


async def build_timeline(raw_events: List[RawEvent], incident: Incident) -> EventList:
    """
    Calls Gemini to extract an ordered, structured timeline from sampled raw events.
    """
    logger.info("build_timeline.start incident_id=%s raw_events=%s", incident.incident_id, len(raw_events))
    if not raw_events:
        logger.warning("build_timeline.empty_input incident_id=%s", incident.incident_id)
        return _fallback_timeline(incident, "No logs ingested.")

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

        prompt = enforce_token_budget(prompt)
        response_dict = await generate(prompt)

        if not isinstance(response_dict, dict):
            raise ValueError("Timeline LLM response is not a JSON object.")

        # Inject mandatory fields for Pydantic validation
        raw_event_items = response_dict.get("events", [])
        if isinstance(raw_event_items, list):
            for e in raw_event_items:
                if isinstance(e, dict):
                    if "event_id" not in e:
                        e["event_id"] = str(uuid.uuid4())[:8]
                    if "incident_id" not in e:
                        e["incident_id"] = incident.incident_id
                    # Ensure event_type is valid
                    et = str(e.get("event_type", "unknown")).lower()
                    if et not in {item.value for item in EventType}:
                        e["event_type"] = "unknown"

        if "total_events" not in response_dict:
            response_dict["total_events"] = len(raw_event_items)

        try:
            event_list = EventList(**response_dict)
            logger.info(
                "build_timeline.complete incident_id=%s events=%s", incident.incident_id, len(event_list.events)
            )
            return event_list
        except ValidationError as e:
            logger.error(f"[TIMELINE] LLM output invalid: {e}")
            return _fallback_timeline(incident, f"Validation failed: {e}")

    except Exception as e:
        logger.exception("build_timeline.failed incident_id=%s", incident.incident_id)
        return _fallback_timeline(incident, f"LLM failure: {e}")
