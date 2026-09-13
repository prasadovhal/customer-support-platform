from __future__ import annotations

import re
from dataclasses import dataclass

from loguru import logger
from rank_bm25 import BM25Okapi


_STOP_WORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would shall should may might must "
    "can could it its this that these those i you he she we they my your "
    "his her our their me him us them what which who whom how when where why".split()
)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


@dataclass
class BM25Result:
    chunk_id: str
    score: float
    text: str
    doc_title: str
    doc_category: str
    doc_path: str
    chunk_index: int


class BM25Index:
    """In-memory BM25 index over knowledge chunks.

    Rebuilt from the database at startup or when the knowledge base is re-indexed.
    At ~900 chunks this rebuild takes <100ms.
    """

    def __init__(self) -> None:
        self._index: BM25Okapi | None = None
        self._records: list[BM25Result] = []

    @property
    def size(self) -> int:
        return len(self._records)

    def build(self, records: list[BM25Result]) -> None:
        """Build the BM25 index from a list of chunk records."""
        if not records:
            logger.warning("BM25 build called with empty corpus")
            self._index = None
            self._records = []
            return

        corpus = [_tokenize(r.text) for r in records]
        self._index = BM25Okapi(corpus)
        self._records = records
        logger.info(f"BM25 index built: {len(records)} chunks")

    def search(self, query: str, top_k: int = 20) -> list[tuple[BM25Result, float]]:
        """Return (record, score) pairs for the top-k BM25 results."""
        if self._index is None or not self._records:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = self._index.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            (self._records[i], float(score))
            for i, score in ranked[:top_k]
            if score > 0.0
        ]
