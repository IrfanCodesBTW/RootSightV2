import json
import logging
from ...schemas.incident import Incident
from ...schemas.event import EventList
from ...schemas.hypothesis import HypothesisList
from ...schemas.impact import Impact, SeverityBand
from pydantic import ValidationError
from ..llm_clients.gemini_client import generate, enforce_token_budget

logger = logging.getLogger(__name__)


async def analyze_impact(incident: Incident, event_list: EventList, hypothesis_list: HypothesisList) -> Impact:
    """
    Calls Gemini to estimate the business and user impact of the incident.
    """
    logger.info(
        "analyze_impact.start incident_id=%s events=%s hypotheses=%s",
        incident.incident_id,
        len(event_list.events),
        len(hypothesis_list.hypotheses),
    )
    try:
        top_hypothesis = hypothesis_list.hypotheses[0] if hypothesis_list.hypotheses else None
        top_3_events = [e.model_dump(mode="json") for e in event_list.events[:3]]

        prompt = f"""
        Estimate the business and user impact of this incident.
        Service: {incident.service}
        Severity: {incident.severity}
        Top cause: {top_hypothesis.statement if top_hypothesis else "Unknown"} ({top_hypothesis.confidence_score if top_hypothesis else 0}% confidence)
        Key events: {json.dumps(top_3_events, indent=2)}

        Return ONLY valid JSON:
        {{
          "affected_services": ["list"],
          "severity_band": "critical|high|medium|low",
          "estimated_duration_minutes": number or null,
          "probable_user_impact": "plain English description",
          "estimated_requests_affected": "estimate or null",
          "business_impact_summary": "1-2 sentence summary"
        }}
        """

        prompt = enforce_token_budget(prompt)
        response_dict = await generate(prompt)

        if not isinstance(response_dict, dict):
            raise ValueError("Impact LLM response is not a JSON object.")

        # Inject mandatory fields for Pydantic validation
        if "incident_id" not in response_dict:
            response_dict["incident_id"] = incident.incident_id

        # Validate severity_band
        raw_band = str(response_dict.get("severity_band", "medium")).lower()
        if raw_band not in [s.value for s in SeverityBand]:
            response_dict["severity_band"] = "medium"

        try:
            result = Impact(**response_dict)
            logger.info(
                "analyze_impact.complete incident_id=%s severity_band=%s", incident.incident_id, result.severity_band
            )
            return result
        except ValidationError as e:
            logger.error(f"[IMPACT] LLM output invalid: {e}")
            return _fallback_impact(incident)

    except Exception:
        logger.exception("analyze_impact.failed incident_id=%s", incident.incident_id)
        return _fallback_impact(incident)


def _fallback_impact(incident: Incident) -> Impact:
    # Map incident severity to severity band
    band_map = {
        "P0": SeverityBand.CRITICAL,
        "P1": SeverityBand.CRITICAL,
        "P2": SeverityBand.HIGH,
        "P3": SeverityBand.MEDIUM,
        "P4": SeverityBand.LOW,
    }
    fallback = Impact(
        incident_id=incident.incident_id,
        affected_services=[incident.service],
        severity_band=band_map.get(incident.severity.value, SeverityBand.MEDIUM),
        estimated_duration_minutes=None,
        probable_user_impact="Impact assessment failed. Treating as undetermined.",
        estimated_requests_affected=None,
        business_impact_summary="System failed to automatically assess business impact.",
    )
    logger.warning(
        "analyze_impact.fallback incident_id=%s severity_band=%s", incident.incident_id, fallback.severity_band
    )
    return fallback
