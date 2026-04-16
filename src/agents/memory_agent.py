"""
RootSight — Memory Agent

Retrieves similar past incidents from the FAISS vector store.
No LLM required (uses embeddings only).
"""

from __future__ import annotations

from src.schemas.incident import IncidentHeader
from src.schemas.rca import RCAHypotheses
from src.schemas.memory import SimilarIncidents, SimilarIncident
from src.services.vector_store import vector_store
from src.integrations.embedding_client import embedding_client
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("agents.memory")


def run(header: IncidentHeader, hypotheses: RCAHypotheses) -> SimilarIncidents:
    """
    Search for similar past incidents using vector similarity.

    Creates an embedding from the current incident summary and
    queries the FAISS index for matches.

    Args:
        header: Current incident header.
        hypotheses: RCA hypotheses (top hypothesis used for embedding).

    Returns:
        SimilarIncidents with matches or a no-match message.
    """
    logger.info(f"Memory Agent — searching for similar incidents to {header.incident_id}")

    # Load the vector store if not already loaded
    if not vector_store.is_loaded:
        loaded = vector_store.load()
        if not loaded:
            logger.warning("Vector store not available — no historical data")
            return SimilarIncidents(
                incident_id=header.incident_id,
                matches=[],
                no_match_message="No historical incident data available. Run build_memory_index.py to seed the database.",
            )

    # Build a search query from incident context
    top_hypothesis = ""
    if hypotheses.hypotheses:
        top_hypothesis = hypotheses.hypotheses[0].statement

    search_text = (
        f"Service: {header.service}. "
        f"Alert: {header.alert_title}. "
        f"Description: {header.description}. "
        f"Hypothesis: {top_hypothesis}"
    )

    try:
        embedding = embedding_client.embed(search_text)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return SimilarIncidents(
            incident_id=header.incident_id,
            matches=[],
            no_match_message="Embedding generation failed — cannot search historical incidents.",
        )

    # Query the vector store
    matches = vector_store.query(
        embedding=embedding,
        top_k=3,
        threshold=settings.SIMILARITY_THRESHOLD,
    )

    if not matches:
        logger.info("No similar incidents found above threshold")
        return SimilarIncidents(
            incident_id=header.incident_id,
            matches=[],
            no_match_message="No strong historical match found.",
        )

    # Convert to schema
    similar_list = []
    for match in matches:
        meta = match.metadata
        similar_list.append(SimilarIncident(
            matched_incident_id=match.incident_id,
            title=meta.get("title", ""),
            similarity_score=round(match.score, 2),
            similarity_reason=meta.get("similarity_reason", ""),
            previous_root_cause=meta.get("root_cause", ""),
            previous_resolution=meta.get("resolution", ""),
            pattern_applies=match.score >= 0.7,
        ))

    logger.info(f"Memory Agent — complete: {len(similar_list)} matches found")
    return SimilarIncidents(
        incident_id=header.incident_id,
        matches=similar_list,
        no_match_message=None,
    )
