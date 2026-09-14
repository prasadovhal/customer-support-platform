from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.rag.bm25_index import BM25Index, BM25Result
from app.rag.embedder import EmbeddingService

RRF_K = 60  # Standard RRF constant; robust across retrieval tasks


@dataclass
class RetrievalResult:
    chunk_id: str
    chunk_index: int
    text: str
    doc_id: str
    doc_title: str
    doc_category: str
    doc_path: str
    doc_version: str
    rrf_score: float
    bm25_rank: Optional[int] = None
    dense_rank: Optional[int] = None
    rerank_score: Optional[float] = None


def _rrf_score(ranks: list[Optional[int]]) -> float:
    """Compute Reciprocal Rank Fusion score from multiple rank lists."""
    return sum(1.0 / (RRF_K + r) for r in ranks if r is not None)


class RAGRetriever:
    """Hybrid BM25 + dense retrieval with RRF fusion.

    Designed for async use from FastAPI endpoints.
    """

    def __init__(
        self,
        embedder: EmbeddingService,
        bm25: BM25Index,
    ) -> None:
        self._embedder = embedder
        self._bm25 = bm25

    async def _dense_search(
        self,
        db: AsyncSession,
        query_vec: np.ndarray,
        top_k: int,
    ) -> list[tuple[str, int]]:
        """Return (chunk_id, rank) pairs from pgvector cosine ANN search."""
        vec_literal = "[" + ",".join(f"{v:.8f}" for v in query_vec.tolist()) + "]"
        stmt = text(
            """
            SELECT kc.id::text
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kc.doc_id = kd.id
            JOIN embedding_metadata em ON em.chunk_id = kc.id
            WHERE kd.is_active = TRUE AND em.embedding IS NOT NULL
            ORDER BY em.embedding <=> :vec::vector
            LIMIT :k
            """
        )
        result = await db.execute(stmt, {"vec": vec_literal, "k": top_k})
        rows = result.fetchall()
        return [(str(row[0]), rank + 1) for rank, row in enumerate(rows)]

    async def _fetch_chunks(
        self, db: AsyncSession, chunk_ids: list[str]
    ) -> dict[str, RetrievalResult]:
        """Load chunk + document metadata for a list of chunk IDs."""
        if not chunk_ids:
            return {}
        stmt = (
            select(
                KnowledgeChunk.id,
                KnowledgeChunk.chunk_index,
                KnowledgeChunk.text,
                KnowledgeDocument.id.label("doc_id"),
                KnowledgeDocument.title,
                KnowledgeDocument.category,
                KnowledgeDocument.path,
                KnowledgeDocument.version,
            )
            .join(KnowledgeDocument, KnowledgeChunk.doc_id == KnowledgeDocument.id)
            .where(KnowledgeChunk.id.in_(chunk_ids))
        )
        rows = (await db.execute(stmt)).fetchall()
        return {
            str(row.id): RetrievalResult(
                chunk_id=str(row.id),
                chunk_index=row.chunk_index,
                text=row.text,
                doc_id=str(row.doc_id),
                doc_title=row.title,
                doc_category=row.category,
                doc_path=row.path,
                doc_version=row.version,
                rrf_score=0.0,
            )
            for row in rows
        }

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        candidate_k: int = 20,
        use_dense: bool = True,
        use_bm25: bool = True,
    ) -> list[RetrievalResult]:
        """Return top_k chunks using hybrid RRF retrieval."""
        dense_ranks: dict[str, int] = {}
        bm25_ranks: dict[str, int] = {}
        all_chunk_ids: set[str] = set()

        if use_dense:
            query_vec = self._embedder.embed_query(query)
            dense_results = await self._dense_search(db, query_vec, candidate_k)
            for chunk_id, rank in dense_results:
                dense_ranks[chunk_id] = rank
                all_chunk_ids.add(chunk_id)

        if use_bm25 and self._bm25.size > 0:
            bm25_results = self._bm25.search(query, top_k=candidate_k)
            for record, _ in bm25_results:
                bm25_ranks[record.chunk_id] = len(bm25_ranks) + 1
                all_chunk_ids.add(record.chunk_id)

        if not all_chunk_ids:
            return []

        chunks = await self._fetch_chunks(db, list(all_chunk_ids))

        # Apply RRF scores
        for chunk_id, result in chunks.items():
            ranks = [dense_ranks.get(chunk_id), bm25_ranks.get(chunk_id)]
            result.rrf_score = _rrf_score([r for r in ranks if r is not None])
            result.dense_rank = dense_ranks.get(chunk_id)
            result.bm25_rank = bm25_ranks.get(chunk_id)

        ranked = sorted(chunks.values(), key=lambda r: r.rrf_score, reverse=True)
        return ranked[:top_k]

    async def build_bm25_from_db(self, db: AsyncSession) -> None:
        """Load all active chunks from DB and rebuild the BM25 index."""
        stmt = (
            select(
                KnowledgeChunk.id,
                KnowledgeChunk.chunk_index,
                KnowledgeChunk.text,
                KnowledgeDocument.title,
                KnowledgeDocument.category,
                KnowledgeDocument.path,
            )
            .join(KnowledgeDocument, KnowledgeChunk.doc_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.is_active.is_(True))
        )
        rows = (await db.execute(stmt)).fetchall()
        records = [
            BM25Result(
                chunk_id=str(row.id),
                score=0.0,
                text=row.text,
                doc_title=row.title,
                doc_category=row.category,
                doc_path=row.path,
                chunk_index=row.chunk_index,
            )
            for row in rows
        ]
        self._bm25.build(records)
        logger.info(f"BM25 index refreshed from DB: {len(records)} chunks")
