from __future__ import annotations

from loguru import logger

from app.rag.retriever import RetrievalResult

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Cross-encoder reranking using ms-marco-MiniLM-L-6-v2.

    Loaded lazily; runs on CPU in-process at ~50ms for 20 candidates.
    """

    def __init__(self, model_name: str = RERANKER_MODEL) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading cross-encoder: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-encoder loaded")

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Score each candidate against the query and return top_k by score."""
        if not candidates:
            return []
        self._load()
        pairs = [[query, c.text] for c in candidates]
        scores = self._model.predict(pairs, show_progress_bar=False)
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = float(score)
        reranked = sorted(candidates, key=lambda c: c.rerank_score or 0.0, reverse=True)
        return reranked[:top_k]
