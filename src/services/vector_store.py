"""
RootSight — FAISS Vector Store

Manages the FAISS index for incident similarity search.
Supports building from seed data, querying, and adding new incidents.
"""

from __future__ import annotations
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("services.vector_store")

# Lazy import faiss to avoid import errors when not installed
_faiss = None


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


class IncidentMatch:
    """A single match result from the vector store."""

    def __init__(self, incident_id: str, metadata: dict, score: float):
        self.incident_id = incident_id
        self.metadata = metadata
        self.score = score


class VectorStore:
    """
    FAISS-based vector store for incident similarity search.

    Stores embeddings alongside incident metadata for retrieval.
    Persists to disk as .faiss + .pkl files.
    """

    def __init__(self):
        self._index = None
        self._metadata: list[dict] = []
        self._dimension: Optional[int] = None

    @property
    def is_loaded(self) -> bool:
        return self._index is not None and len(self._metadata) > 0

    @property
    def count(self) -> int:
        return len(self._metadata)

    def build_index(self, embeddings: list[list[float]], metadata: list[dict]) -> None:
        """
        Build a new FAISS index from embeddings and metadata.

        Args:
            embeddings: List of embedding vectors.
            metadata: List of metadata dicts (must be same length as embeddings).
        """
        faiss = _get_faiss()

        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")

        if not embeddings:
            logger.warning("No embeddings provided — creating empty index")
            return

        vectors = np.array(embeddings, dtype=np.float32)
        self._dimension = vectors.shape[1]

        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        vectors = vectors / norms

        # Use Inner Product (equivalent to cosine similarity after normalization)
        self._index = faiss.IndexFlatIP(self._dimension)
        self._index.add(vectors)
        self._metadata = metadata

        logger.info(f"Built FAISS index with {len(metadata)} incidents (dim={self._dimension})")

    def query(
        self,
        embedding: list[float],
        top_k: int = 1,
        threshold: float = None,
    ) -> list[IncidentMatch]:
        """
        Query the index for similar incidents.

        Args:
            embedding: Query embedding vector.
            top_k: Number of results to return.
            threshold: Minimum similarity score (default from settings).

        Returns:
            List of IncidentMatch objects, sorted by score descending.
        """
        if not self.is_loaded:
            logger.warning("Vector store not loaded — returning empty results")
            return []

        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD

        faiss = _get_faiss()

        query_vec = np.array([embedding], dtype=np.float32)
        # Normalize query
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm

        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_vec, k)

        matches = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            if score >= threshold:
                meta = self._metadata[idx]
                matches.append(IncidentMatch(
                    incident_id=meta.get("incident_id", "unknown"),
                    metadata=meta,
                    score=float(score),
                ))

        logger.info(f"Vector query returned {len(matches)} matches above threshold {threshold}")
        return matches

    def add(self, embedding: list[float], metadata: dict) -> None:
        """Add a single incident to the index."""
        faiss = _get_faiss()

        vec = np.array([embedding], dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        if self._index is None:
            self._dimension = len(embedding)
            self._index = faiss.IndexFlatIP(self._dimension)

        self._index.add(vec)
        self._metadata.append(metadata)
        logger.info(f"Added incident {metadata.get('incident_id', 'unknown')} to vector store")

    def save(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> None:
        """Persist index and metadata to disk."""
        faiss = _get_faiss()

        index_path = index_path or settings.FAISS_INDEX_PATH
        metadata_path = metadata_path or settings.FAISS_METADATA_PATH

        if self._index is None:
            logger.warning("No index to save")
            return

        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_path))
        with open(metadata_path, "wb") as f:
            pickle.dump(self._metadata, f)

        logger.info(f"Saved vector store: {self.count} incidents → {index_path}")

    def load(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> bool:
        """Load index and metadata from disk. Returns True if successful."""
        faiss = _get_faiss()

        index_path = index_path or settings.FAISS_INDEX_PATH
        metadata_path = metadata_path or settings.FAISS_METADATA_PATH

        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"Vector store files not found at {index_path}")
            return False

        try:
            self._index = faiss.read_index(str(index_path))
            with open(metadata_path, "rb") as f:
                self._metadata = pickle.load(f)
            self._dimension = self._index.d
            logger.info(f"Loaded vector store: {self.count} incidents (dim={self._dimension})")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False


# Module-level singleton
vector_store = VectorStore()
