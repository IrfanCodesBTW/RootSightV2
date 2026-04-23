import logging
from ...schemas.incident import Incident
from ...schemas.hypothesis import HypothesisList
from ...schemas.similar_incident import SimilarIncident, SimilarIncidentList
from .vector_store import vector_store
from ..llm_clients.gemini_client import generate
from ..llm_clients.errors import LLMClientError, enforce_token_budget

logger = logging.getLogger(__name__)

SEED_INCIDENTS = [
    {
        "incident_id": "HIST-001",
        "title": "CDN Cache Purge 502 Storm",
        "service": "cdn",
        "severity": "P1",
        "summary": "Full cache purge triggered thundering herd on origin servers. "
        "CPU hit 98%. Fix: staged regional purge with rate limiting.",
        "fix_applied": "Implemented staged CDN purge with 10% rollout per region.",
    },
    {
        "incident_id": "HIST-002",
        "title": "Payment API CPU Spike",
        "service": "payment-api",
        "severity": "P1",
        "summary": "Traffic spike exhausted DB connection pool causing payment timeouts. "
        "Fix: raised connection pool limit and added circuit breaker.",
        "fix_applied": "Raised max_connections 50→200. Added circuit breaker on payment service.",
    },
    {
        "incident_id": "HIST-003",
        "title": "DB Connection Pool Exhausted",
        "service": "user-service",
        "severity": "P2",
        "summary": "Slow migration query held connections during deploy. Fix: query timeout enforced at 30s.",
        "fix_applied": "Added statement_timeout=30000ms. Migrations now run in maintenance window.",
    },
]


async def seed_historical_incidents():
    if vector_store.index is None:
        logger.warning("[MEMORY] Vector store index is None, skipping seed.")
        return

    if vector_store.index.ntotal > 0:
        logger.info("[MEMORY] Vector store not empty (count=%s). Skipping seed.", vector_store.index.ntotal)
        return

    logger.info("[MEMORY] Seeding historical incidents...")
    for item in SEED_INCIDENTS:
        embed_text = f"{item['title']} {item['service']} {item['summary']}"
        try:
            vector_store.add_incident(
                incident_id=item["incident_id"], text=embed_text, previous_fix=item["fix_applied"]
            )
        except Exception as e:
            logger.error("[MEMORY] Seed failed for %s: %s", item["incident_id"], e)
    logger.info("[MEMORY] Seeded %d historical incidents", len(SEED_INCIDENTS))


async def find_similar_incidents(incident: Incident, hypothesis_list: HypothesisList) -> SimilarIncidentList:
    """
    Finds similar historical incidents using FAISS and asks Gemini to explain the similarity.
    Returns empty list on any failure (never raises FileNotFoundError).
    """
    logger.info(
        "find_similar_incidents.start incident_id=%s hypotheses=%s",
        incident.incident_id,
        len(hypothesis_list.hypotheses),
    )

    if vector_store.index is None:
        logger.warning("find_similar_incidents.vector_store_none incident_id=%s", incident.incident_id)
        return SimilarIncidentList(matches=[])

    if vector_store.index.ntotal == 0:
        logger.warning("find_similar_incidents.empty_index incident_id=%s", incident.incident_id)
        return SimilarIncidentList(matches=[])

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
                logger.warning(
                    "find_similar_incidents.invalid_match_shape incident_id=%s match=%s", incident.incident_id, match
                )
                continue
            prompt = f"""
            Compare these two incidents and explain briefly why they are similar.
            Keep it to 1 sentence.

            Current Incident: {incident.title} (Cause: {top_hypothesis})
            Past Incident Text: {match["text"]}
            
            Return ONLY valid JSON:
            {{
                "why_similar": "1 sentence explanation"
            }}
            """
            try:
                prompt = enforce_token_budget(prompt)
                response = await generate(prompt, max_retries=2)
                why_similar = (
                    response.get("why_similar", "Shares similar patterns.")
                    if isinstance(response, dict)
                    else "Shares similar patterns."
                )
            except (LLMClientError, Exception):
                logger.exception("find_similar_incidents.explanation_failed incident_id=%s", incident.incident_id)
                why_similar = "Shares similar patterns."

            similar_incidents.append(
                SimilarIncident(
                    incident_id=incident.incident_id,
                    similar_to_id=match.get("incident_id", "unknown"),
                    similarity_score=match.get("similarity_score", 0.0),
                    why_similar=why_similar,
                    previous_fix=match.get("previous_fix", "No fix recorded"),
                )
            )

        result = SimilarIncidentList(matches=similar_incidents)
        logger.info(
            "find_similar_incidents.complete incident_id=%s matches=%s", incident.incident_id, len(result.matches)
        )
        return result

    except Exception:
        logger.exception("find_similar_incidents.failed incident_id=%s", incident.incident_id)
        return SimilarIncidentList(matches=[])
