from __future__ import annotations

import numpy as np
from loguru import logger

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIM = 768
EMBEDDING_VERSION = "1.5"
# BGE-base requires this prefix on query strings for best retrieval performance
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Wraps sentence-transformers BGE-base for chunk and query encoding.

    Model is loaded lazily on first call to avoid startup cost when embeddings
    are not needed (e.g., BM25-only retrieval paths).
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded (dim={EMBEDDING_DIM})")

    def embed_chunks(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode document chunks — no query prefix."""
        self._load()
        assert self._model is not None
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )

    def embed_query(self, query: str) -> np.ndarray:
        """Encode a single query with the BGE instruction prefix."""
        self._load()
        assert self._model is not None
        return self._model.encode(
            QUERY_PREFIX + query,
            normalize_embeddings=True,
        )

    @property
    def dim(self) -> int:
        return EMBEDDING_DIM

    @property
    def model_version(self) -> str:
        return EMBEDDING_VERSION
