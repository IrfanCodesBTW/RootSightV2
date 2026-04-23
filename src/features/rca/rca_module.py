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


async def analyze_root_cause(event_list: EventList, incident: Incident) -> HypothesisList:
    """
    Calls Gemini to generate root cause hypotheses based ONLY on the compressed timeline.
    """
    logger.info("analyze_root_cause.start incident_id=%s events=%s", incident.incident_id, len(event_list.events))
    if not event_list.events:
        logger.warning("analyze_root_cause.empty_input incident_id=%s", incident.incident_id)
        return _fallback_hypothesis(incident.incident_id, "No events available for analysis.")

    try:
        serialized_events = json.dumps([e.model_dump(mode="json") for e in event_list.events], indent=2)
        prompt = f"""
        You are an expert SRE performing root cause analysis.
        Incident: {incident.title} on {incident.service}
        Severity: {incident.severity}

        Incident Timeline:
        {serialized_events}

        Generate 2-3 ranked root cause hypotheses.
        IMPORTANT:
        - Do NOT claim certainty. Use "likely", "possibly", "suggests"
        - If confidence < 30%, say so clearly
        - Rank by confidence (highest first)

        Return ONLY valid JSON:
        {{
          "hypotheses": [
            {{
              "rank": 1,
              "statement": "specific hypothesis statement",
              "confidence_score": 0-100,
              "supporting_evidence": ["list of supporting observations"],
              "contradicting_evidence": ["list of contradicting observations"],
              "missing_information": ["what data would help confirm this"],
              "recommended_check": "next diagnostic step"
            }}
          ],
          "analysis_confidence": 0-100,
          "is_low_confidence": true/false,
          "analysis_note": "optional note"
        }}
        """

        prompt = enforce_token_budget(prompt)
        response_dict = await generate(prompt)

        if not isinstance(response_dict, dict):
            raise ValueError("RCA LLM response is not a JSON object.")

        # Inject mandatory fields for Pydantic validation
        raw_hypotheses = response_dict.get("hypotheses", [])
        if isinstance(raw_hypotheses, list):
            for h in raw_hypotheses:
                if isinstance(h, dict):
                    if "hypothesis_id" not in h:
                        h["hypothesis_id"] = str(uuid.uuid4())[:8]
                    if "incident_id" not in h:
                        h["incident_id"] = incident.incident_id

        try:
            result = HypothesisList(**response_dict)

            # Ensure at least 1 hypothesis
            if not result.hypotheses:
                return _fallback_hypothesis(incident.incident_id, "LLM returned no hypotheses.")

            # Sort hypotheses by confidence_score descending
            result.hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)

            # Re-assign ranks based on sorted order
            for i, h in enumerate(result.hypotheses):
                h.rank = i + 1

            # Post-validation low confidence check
            if result.hypotheses and result.hypotheses[0].confidence_score < 30:
                result.is_low_confidence = True

            logger.info(
                "analyze_root_cause.complete incident_id=%s hypotheses=%s", incident.incident_id, len(result.hypotheses)
            )
            return result
        except ValidationError as e:
            logger.error("analyze_root_cause.validation_failed incident_id=%s error=%s", incident.incident_id, e)
            return _fallback_hypothesis(incident.incident_id, f"Validation failed: {e}")

    except Exception as e:
        logger.exception("analyze_root_cause.failed incident_id=%s", incident.incident_id)
        return _fallback_hypothesis(incident.incident_id, f"LLM failure: {e}")


def _fallback_hypothesis(incident_id: str, note: str) -> HypothesisList:
    """Return a single 'Manual investigation required' hypothesis as fallback."""
    logger.warning("analyze_root_cause.fallback incident_id=%s note=%s", incident_id, note)
    fallback = Hypothesis(
        hypothesis_id=str(uuid.uuid4())[:8],
        incident_id=incident_id,
        rank=1,
        statement="Manual investigation required",
        confidence_score=0,
        supporting_evidence=[],
        contradicting_evidence=[],
        missing_information=["Full system logs", "Metrics dashboard access"],
        severity_band="low",
    )
    return HypothesisList(
        hypotheses=[fallback],
        analysis_confidence=0,
        is_low_confidence=True,
        analysis_note=note,
    )
