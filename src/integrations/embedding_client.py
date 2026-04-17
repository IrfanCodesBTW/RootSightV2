"""
RootSight — Embedding Client

Generates text embeddings via Google's text-embedding model
for the Memory Agent's vector similarity search.
"""

from __future__ import annotations
from typing import Optional

from google import genai
from google.genai import types

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("integrations.embedding")

EMBEDDING_MODEL = "gemini-embedding-001"


class EmbeddingClient:
    """
    Wrapper for Google's text embedding API.

    Provides single-text and batch embedding generation.
    """

    def __init__(self):
        if not settings.has_gemini_key:
            logger.warning("No Gemini API key — embeddings unavailable")
            self._client = None
        else:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        if not self.is_available:
            raise RuntimeError("Embedding client not initialized — check GEMINI_API_KEY")

        result = self._client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return result.embeddings[0].values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self.is_available:
            raise RuntimeError("Embedding client not initialized — check GEMINI_API_KEY")

        embeddings = []
        # Process in batches to avoid API limits
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                result = self._client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text,
                )
                embeddings.append(result.embeddings[0].values)
        return embeddings


# Module-level singleton
embedding_client = EmbeddingClient()
