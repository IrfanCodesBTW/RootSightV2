import json
import logging
from .schemas.incident import Incident
from .schemas.event import EventList
from .schemas.hypothesis import HypothesisList
from .schemas.impact import Impact, SeverityBand
from .llm_clients.gemini_client import generate

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
        top_3_events = [e.model_dump() for e in event_list.events[:3]]

        prompt = f"""
        Estimate the business and user impact of this incident.
        Service: {incident.service}
        Severity: {incident.severity}
        Top cause: {top_hypothesis.statement if top_hypothesis else 'Unknown'} ({top_hypothesis.confidence_score if top_hypothesis else 0}% confidence)
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

        response_dict = await generate(prompt)
        if not isinstance(response_dict, dict):
            raise ValueError("Impact LLM response is not a JSON object.")

        raw_band = str(response_dict.get("severity_band", "medium")).lower()
        if raw_band not in [s.value for s in SeverityBand]:
            raw_band = "medium"

        affected_services = response_dict.get("affected_services", [incident.service])
        if not isinstance(affected_services, list) or not affected_services:
            affected_services = [incident.service]
        affected_services = [str(item) for item in affected_services if str(item).strip()]
        if not affected_services:
            affected_services = [incident.service]

        result = Impact(
            incident_id=incident.incident_id,
            affected_services=affected_services,
            severity_band=SeverityBand(raw_band),
            estimated_duration_minutes=response_dict.get("estimated_duration_minutes"),
            probable_user_impact=response_dict.get("probable_user_impact", "Unknown impact based on current data."),
            estimated_requests_affected=response_dict.get("estimated_requests_affected"),
            business_impact_summary=response_dict.get("business_impact_summary")
        )
        logger.info("analyze_impact.complete incident_id=%s severity_band=%s", incident.incident_id, result.severity_band)
        return result

    except Exception:
        logger.exception("analyze_impact.failed incident_id=%s", incident.incident_id)
        return _fallback_impact(incident)

def _fallback_impact(incident: Incident) -> Impact:
    # Map incident severity to severity band
    band_map = {
        "P1": SeverityBand.CRITICAL,
        "P2": SeverityBand.HIGH,
        "P3": SeverityBand.MEDIUM,
        "P4": SeverityBand.LOW
    }
    fallback = Impact(
        incident_id=incident.incident_id,
        affected_services=[incident.service],
        severity_band=band_map.get(incident.severity.value, SeverityBand.MEDIUM),
        estimated_duration_minutes=None,
        probable_user_impact="Impact assessment failed. Treating as undetermined.",
        estimated_requests_affected=None,
        business_impact_summary="System failed to automatically assess business impact."
    )
    logger.warning("analyze_impact.fallback incident_id=%s severity_band=%s", incident.incident_id, fallback.severity_band)
    return fallback
