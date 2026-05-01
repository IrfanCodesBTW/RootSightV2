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

    def _rebuild_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        for item in self.metadata:
            embedding = self.get_embedding(item["text"])
            self.index.add(np.expand_dims(embedding, axis=0))

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding with token budget enforcement."""
        text = enforce_token_budget(text, max_tokens=2000)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL, content=text, task_type="retrieval_document"
        )
        return np.array(result["embedding"], dtype="float32")

    def add_incident(self, incident_id: str, text: str, previous_fix: str, **metadata):
        if self.index is None:
            self._create_new_index()
        embedding = self.get_embedding(text)
        self.index.add(np.expand_dims(embedding, axis=0))
        self.metadata.append({"incident_id": incident_id, "text": text, "previous_fix": previous_fix, **metadata})
        self._save_index()
        logger.info("[VECTOR_STORE] Added incident %s, total=%d", incident_id, self.index.ntotal)

    def upsert_resolved_incident(
        self,
        incident_id: str,
        text: str,
        previous_fix: str,
        correct_hypothesis_id: str | None = None,
        root_cause: str | None = None,
        resolution_notes: str | None = None,
        mttr_minutes: int | None = None,
    ):
        resolved_text = f"{text} | resolved_by: {root_cause}" if root_cause else text
        resolved_metadata = {
            "incident_id": incident_id,
            "text": resolved_text,
            "previous_fix": previous_fix,
            "correct_hypothesis_id": correct_hypothesis_id,
            "root_cause": root_cause,
            "resolution_notes": resolution_notes,
            "mttr_minutes": mttr_minutes,
        }

        existing_idx = next(
            (idx for idx, item in enumerate(self.metadata) if item.get("incident_id") == incident_id),
            None,
        )
        if existing_idx is None:
            self.add_incident(**resolved_metadata)
            return

        self.metadata[existing_idx] = resolved_metadata
        self._rebuild_index()
        self._save_index()
        logger.info("[VECTOR_STORE] Updated resolved incident %s", incident_id)

    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.get_embedding(query)
        candidate_count = min(max(top_k * 4, top_k), self.index.ntotal)
        distances, indices = self.index.search(np.expand_dims(query_embedding, axis=0), candidate_count)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                match = self.metadata[idx].copy()
                embedding_similarity = float(1.0 / (1.0 + distances[0][i]))
                resolution_confirmed = 1.0 if match.get("correct_hypothesis_id") else 0.0
                match["embedding_similarity"] = embedding_similarity
                match["resolution_confirmed"] = bool(resolution_confirmed)
                match["similarity_score"] = (0.7 * embedding_similarity) + (0.3 * resolution_confirmed)
                results.append(match)
        return sorted(results, key=lambda item: item.get("similarity_score", 0.0), reverse=True)[:top_k]


vector_store = VectorStore()
