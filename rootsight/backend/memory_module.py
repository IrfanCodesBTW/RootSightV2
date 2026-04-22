import logging
from .schemas.incident import Incident
from .schemas.hypothesis import HypothesisList
from .schemas.similar_incident import SimilarIncident, SimilarIncidentList
from .storage.vector_store import vector_store
from .llm_clients.gemini_client import generate

logger = logging.getLogger(__name__)

async def find_similar_incidents(incident: Incident, hypothesis_list: HypothesisList) -> SimilarIncidentList:
    """
    Finds similar historical incidents using FAISS and asks Gemini to explain the similarity.
    """
    logger.info(
        "find_similar_incidents.start incident_id=%s hypotheses=%s",
        incident.incident_id,
        len(hypothesis_list.hypotheses),
    )
    try:
        top_hypothesis = hypothesis_list.hypotheses[0].statement if hypothesis_list.hypotheses else "Unknown cause"
        search_query = f"{incident.title} {incident.service} {top_hypothesis}"

        raw_matches = vector_store.search_similar(search_query, top_k=3)
        if not isinstance(raw_matches, list):
            logger.error("find_similar_incidents.invalid_search_results incident_id=%s", incident.incident_id)
            return SimilarIncidentList(matches=[])

        if not raw_matches:
            return SimilarIncidentList(matches=[])

        similar_incidents = []

        for match in raw_matches:
            if not isinstance(match, dict):
                logger.warning("find_similar_incidents.invalid_match_shape incident_id=%s match=%s", incident.incident_id, match)
                continue
            prompt = f"""
            Compare these two incidents and explain briefly why they are similar.
            Keep it to 1 sentence.

            Current Incident: {incident.title} (Cause: {top_hypothesis})
            Past Incident Text: {match['text']}
            
            Return ONLY valid JSON:
            {{
                "why_similar": "1 sentence explanation"
            }}
            """
            try:
                response = await generate(prompt, max_retries=2)
                why_similar = response.get("why_similar", "Shares similar patterns.") if isinstance(response, dict) else "Shares similar patterns."
            except Exception:
                logger.exception("find_similar_incidents.explanation_failed incident_id=%s", incident.incident_id)
                why_similar = "Shares similar patterns."

            similar_incidents.append(SimilarIncident(
                incident_id=incident.incident_id,
                similar_to_id=match.get("incident_id", "unknown"),
                similarity_score=match.get("similarity_score", 0.0),
                why_similar=why_similar,
                previous_fix=match.get("previous_fix", "No fix recorded")
            ))

        result = SimilarIncidentList(matches=similar_incidents)
        logger.info("find_similar_incidents.complete incident_id=%s matches=%s", incident.incident_id, len(result.matches))
        return result

    except Exception:
        logger.exception("find_similar_incidents.failed incident_id=%s", incident.incident_id)
        return SimilarIncidentList(matches=[])
