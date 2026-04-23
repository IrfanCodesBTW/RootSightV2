import os
import faiss
import numpy as np
import pickle
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from ...utils.config import settings
from ..llm_clients.errors import enforce_token_budget

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.index_path = os.path.join(storage_path, "incident_index.faiss")
        self.metadata_path = os.path.join(storage_path, "incident_index.faiss.meta")
        self.dimension = 768  # Gemini embedding dimension
        self.index = None
        self.metadata = []

        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        self._initialize_index()

    def _initialize_index(self):
        """Load existing index from disk, or create a new one."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info("[VECTOR_STORE] Loaded index with %d items", self.index.ntotal)
            except FileNotFoundError:
                logger.warning("[VECTOR_STORE] Index files not found, creating new index")
                self._create_new_index()
            except Exception as e:
                logger.error("[VECTOR_STORE] Failed to load index: %s", e)
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        logger.info("[VECTOR_STORE] Created new FAISS index")

    def _save_index(self):
        """Persist index to disk immediately after modification."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
        except Exception as e:
            logger.error("[VECTOR_STORE] Failed to save index: %s", e)

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding with token budget enforcement."""
        text = enforce_token_budget(text, max_tokens=2000)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL, content=text, task_type="retrieval_document"
        )
        return np.array(result["embedding"], dtype="float32")

    def add_incident(self, incident_id: str, text: str, previous_fix: str):
        if self.index is None:
            self._create_new_index()
        embedding = self.get_embedding(text)
        self.index.add(np.expand_dims(embedding, axis=0))
        self.metadata.append({"incident_id": incident_id, "text": text, "previous_fix": previous_fix})
        self._save_index()
        logger.info("[VECTOR_STORE] Added incident %s, total=%d", incident_id, self.index.ntotal)

    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.get_embedding(query)
        distances, indices = self.index.search(np.expand_dims(query_embedding, axis=0), top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                match = self.metadata[idx].copy()
                match["similarity_score"] = float(1.0 / (1.0 + distances[0][i]))
                results.append(match)
        return results


vector_store = VectorStore()
