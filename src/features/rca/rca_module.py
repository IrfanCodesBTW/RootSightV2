import json
import logging
import uuid
from ...schemas.incident import Incident
from ...schemas.event import EventList
from ...schemas.hypothesis import HypothesisList, Hypothesis
from pydantic import ValidationError
from ..llm_clients.gemini_client import generate
from ..llm_clients.errors import enforce_token_budget

logger = logging.getLogger(__name__)

# ── Prompt Templates ────────────────────────────────────────────────────────────

_BASE_PROMPT = """
You are an expert Site Reliability Engineer (SRE) AI specialized in incident Root Cause Analysis (RCA) for complex distributed systems.
Your task is to analyze a sequence of telemetry events and generate plausible hypotheses for the root cause of the ongoing incident.

Incident: {title} on {service}
Severity: {severity}

CRITICAL RULES:
1. EVIDENCE ANCHORING: Every hypothesis MUST be strictly grounded in the provided event data. You must explicitly cite the exact `id` of each event that supports your hypothesis in the `supporting_event_ids` array. If a hypothesis cannot be directly tied to specific event IDs, you MUST NOT generate it.
2. EVIDENCE STRENGTH: Classify the evidence supporting each hypothesis:
   - "strong": 3 or more correlated events directly support the hypothesis
   - "moderate": exactly 2 events support the hypothesis
   - "weak": only 1 event supports the hypothesis
3. CONFIDENCE GROUNDING: Assign a confidence level to each hypothesis using ONLY these categorical values: "high", "medium", or "low". Do not use percentages or numerical scores.
4. REJECTION RULE: If the provided EventList contains fewer than 3 events, you must refuse to generate hypotheses by returning an empty hypotheses array and setting `insufficient_data` to true.
5. LIMIT: Generate a maximum of 3 hypotheses. Rank them in descending order of confidence (highest confidence first).
6. CATEGORIES: The `category` must be exactly one of: "infrastructure", "application", "dependency", or "configuration".
7. RAW JSON ONLY: Your output MUST be exactly valid JSON matching the schema below. Do not output markdown formatting (like ```json), no backticks, and absolutely no preamble or conversational text.
{extra_instructions}

OUTPUT SCHEMA:
{{
  "hypotheses": [
    {{
      "id": "H1",
      "text": "Clear, concise description of the hypothesized root cause.",
      "supporting_event_ids": ["E1", "E2"],
      "evidence_strength": "strong" | "moderate" | "weak",
      "confidence": "high" | "medium" | "low",
      "category": "infrastructure" | "application" | "dependency" | "configuration",
      "recommended_action_hint": "Brief next step to verify or mitigate this cause."
    }}
  ],
  "insufficient_data": true | false
}}

<EVENT_LIST>
{serialized_events}
</EVENT_LIST>
"""

_RETRY_EXTRA = """
8. MANDATORY: The `supporting_event_ids` array MUST contain at least one valid event ID from the EVENT_LIST. An empty array is INVALID and will cause a system failure. Copy the exact `id` values from the events above.
9. MANDATORY: The `evidence_strength` field MUST be one of: "strong", "moderate", or "weak". This field is REQUIRED for every hypothesis.
"""


async def analyze_root_cause(event_list: EventList, incident: Incident) -> HypothesisList:
    """
    Calls Gemini to generate root cause hypotheses based ONLY on the compressed timeline.
    On validation failure, retries once with a stricter prompt. On second failure, returns fallback.
    """
    logger.info("analyze_root_cause.start incident_id=%s events=%s", incident.incident_id, len(event_list.events))

    if len(event_list.events) < 3:
        logger.warning("analyze_root_cause.insufficient_events incident_id=%s count=%s", incident.incident_id, len(event_list.events))
        return _fallback_hypothesis("Insufficient data for root cause analysis (requires at least 3 events).")

    # Pass only IDs and descriptions to keep it strictly event-anchored
    events_for_llm = [
        {"id": e.event_id, "description": e.description, "timestamp": e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp)}
        for e in event_list.events
    ]
    serialized_events = json.dumps(events_for_llm, indent=2)

    # Attempt 1: standard prompt
    result = await _attempt_rca(serialized_events, incident, extra_instructions="", attempt=1)
    if result is not None:
        return result

    # Attempt 2: stricter prompt with explicit retry instructions
    logger.warning("analyze_root_cause.retry incident_id=%s", incident.incident_id)
    result = await _attempt_rca(serialized_events, incident, extra_instructions=_RETRY_EXTRA, attempt=2)
    if result is not None:
        return result

    # Both attempts failed — return fallback
    logger.error("analyze_root_cause.both_attempts_failed incident_id=%s", incident.incident_id)
    return _fallback_hypothesis("Both RCA attempts failed validation. Manual investigation required.")


async def _attempt_rca(
    serialized_events: str,
    incident: Incident,
    extra_instructions: str,
    attempt: int,
) -> HypothesisList | None:
    """Single RCA attempt. Returns HypothesisList on success, None on validation/LLM failure."""
    try:
        prompt = _BASE_PROMPT.format(
            title=incident.title,
            service=incident.service,
            severity=incident.severity,
            extra_instructions=extra_instructions,
            serialized_events=serialized_events,
        )
        prompt = enforce_token_budget(prompt)
        response_dict = await generate(prompt)

        if not isinstance(response_dict, dict):
            raise ValueError("RCA LLM response is not a JSON object.")

        # Ensure LLM hasn't hallucinated missing keys
        if "insufficient_data" not in response_dict:
            response_dict["insufficient_data"] = False

        result = HypothesisList(**response_dict)

        # Rejection logic if LLM decides insufficient data internally
        if result.insufficient_data or not result.hypotheses:
            return _fallback_hypothesis("LLM returned no hypotheses or deemed data insufficient.")

        # Note: sorting is handled by Pydantic model validator

        logger.info(
            "analyze_root_cause.complete attempt=%s incident_id=%s hypotheses=%s",
            attempt, incident.incident_id, len(result.hypotheses),
        )
        return result

    except ValidationError as e:
        logger.error(
            "analyze_root_cause.validation_failed attempt=%s incident_id=%s error=%s",
            attempt, incident.incident_id, e,
        )
        return None

    except Exception as e:
        logger.exception("analyze_root_cause.failed attempt=%s incident_id=%s", attempt, incident.incident_id)
        return None


def _fallback_hypothesis(note: str) -> HypothesisList:
    """Return an empty hypothesis list marking insufficient data."""
    logger.warning("analyze_root_cause.fallback note=%s", note)
    return HypothesisList(
        hypotheses=[],
        insufficient_data=True
    )
