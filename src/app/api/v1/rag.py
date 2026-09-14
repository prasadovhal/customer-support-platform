from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.knowledge import EmbeddingMetadata, KnowledgeChunk, KnowledgeDocument
from app.rag.bm25_index import BM25Index
from app.rag.embedder import EmbeddingService
from app.rag.pipeline import RAGPipeline
from app.rag.reranker import CrossEncoderReranker
from app.rag.retriever import RAGRetriever

router = APIRouter(prefix="/rag", tags=["rag"])

# Module-level singletons — initialised on first request
_embedder: Optional[EmbeddingService] = None
_bm25: Optional[BM25Index] = None
_retriever: Optional[RAGRetriever] = None
_pipeline: Optional[RAGPipeline] = None
_bm25_built = False


def _get_embedder() -> EmbeddingService:
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingService()
    return _embedder


def _get_bm25() -> BM25Index:
    global _bm25
    if _bm25 is None:
        _bm25 = BM25Index()
    return _bm25


def _get_pipeline() -> RAGPipeline:
    global _retriever, _pipeline
    if _pipeline is None:
        _retriever = RAGRetriever(embedder=_get_embedder(), bm25=_get_bm25())
        _pipeline = RAGPipeline(retriever=_retriever, reranker=CrossEncoderReranker())
    return _pipeline


# ---------- Request / Response schemas ----------


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    use_dense: bool = True
    use_bm25: bool = True
    use_reranker: bool = True


class ChunkResult(BaseModel):
    chunk_id: str
    chunk_index: int
    text: str
    doc_title: str
    doc_category: str
    doc_version: str
    rrf_score: float
    rerank_score: Optional[float] = None
    bm25_rank: Optional[int] = None
    dense_rank: Optional[int] = None


class SourceResult(BaseModel):
    doc_title: str
    doc_category: str
    doc_path: str
    doc_version: str
    chunk_index: int


class SearchResponse(BaseModel):
    query: str
    chunks: list[ChunkResult]
    sources: list[SourceResult]
    retrieval_strategy: str
    n_candidates_retrieved: int


class IndexStats(BaseModel):
    total_documents: int
    active_documents: int
    total_chunks: int
    embedded_chunks: int
    embedding_coverage_pct: float
    bm25_index_size: int


# ---------- Endpoints ----------


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Retrieve relevant knowledge base chunks for a query using hybrid RAG."""
    pipeline = _get_pipeline()

    # Build BM25 index on first request (warm-up)
    global _bm25_built
    if not _bm25_built:
        retriever = pipeline._retriever
        await retriever.build_bm25_from_db(db)
        _bm25_built = True

    try:
        result = await pipeline.query(
            db=db,
            query=request.query,
            use_dense=request.use_dense,
            use_bm25=request.use_bm25,
            use_reranker=request.use_reranker,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG retrieval failed: {exc}",
        )

    return SearchResponse(
        query=result.query,
        chunks=[
            ChunkResult(
                chunk_id=c.chunk_id,
                chunk_index=c.chunk_index,
                text=c.text,
                doc_title=c.doc_title,
                doc_category=c.doc_category,
                doc_version=c.doc_version,
                rrf_score=c.rrf_score,
                rerank_score=c.rerank_score,
                bm25_rank=c.bm25_rank,
                dense_rank=c.dense_rank,
            )
            for c in result.chunks
        ],
        sources=[
            SourceResult(
                doc_title=s.doc_title,
                doc_category=s.doc_category,
                doc_path=s.doc_path,
                doc_version=s.doc_version,
                chunk_index=s.chunk_index,
            )
            for s in result.sources
        ],
        retrieval_strategy=result.retrieval_strategy,
        n_candidates_retrieved=result.n_candidates_retrieved,
    )


@router.get("/stats", response_model=IndexStats)
async def index_stats(db: AsyncSession = Depends(get_db)) -> IndexStats:
    """Return knowledge base index statistics."""
    total_docs = (
        await db.execute(select(func.count(KnowledgeDocument.id)))
    ).scalar_one()
    active_docs = (
        await db.execute(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.is_active.is_(True)
            )
        )
    ).scalar_one()
    total_chunks = (
        await db.execute(select(func.count(KnowledgeChunk.id)))
    ).scalar_one()
    embedded_chunks = (
        await db.execute(
            select(func.count(EmbeddingMetadata.id)).where(
                EmbeddingMetadata.embedding.is_not(None)
            )
        )
    ).scalar_one()

    coverage = (embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0.0
    bm25 = _get_bm25()

    return IndexStats(
        total_documents=total_docs,
        active_documents=active_docs,
        total_chunks=total_chunks,
        embedded_chunks=embedded_chunks,
        embedding_coverage_pct=round(coverage, 1),
        bm25_index_size=bm25.size,
    )
