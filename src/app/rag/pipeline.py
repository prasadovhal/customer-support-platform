from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.reranker import CrossEncoderReranker
from app.rag.retriever import RAGRetriever, RetrievalResult

MAX_CONTEXT_CHARS = 6000  # ~1500 tokens; leaves room for prompt + generation


@dataclass
class SourceAttribution:
    doc_title: str
    doc_category: str
    doc_path: str
    doc_version: str
    chunk_index: int


@dataclass
class RAGResult:
    query: str
    chunks: list[RetrievalResult]
    context_text: str
    sources: list[SourceAttribution]
    retrieval_strategy: str
    n_candidates_retrieved: int


def _build_context(chunks: list[RetrievalResult], max_chars: int) -> str:
    """Concatenate chunk texts into a context block, respecting the char budget."""
    parts: list[str] = []
    total = 0
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}: {chunk.doc_title} — {chunk.doc_category}]\n"
        block = header + chunk.text + "\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


class RAGPipeline:
    """End-to-end RAG pipeline: query → retrieve → rerank → context."""

    def __init__(
        self,
        retriever: RAGRetriever,
        reranker: Optional[CrossEncoderReranker] = None,
        candidate_k: int = 20,
        top_k: int = 5,
        use_reranker: bool = True,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker or CrossEncoderReranker()
        self.candidate_k = candidate_k
        self.top_k = top_k
        self.use_reranker = use_reranker

    async def query(
        self,
        db: AsyncSession,
        query: str,
        use_dense: bool = True,
        use_bm25: bool = True,
        use_reranker: Optional[bool] = None,
    ) -> RAGResult:
        """Retrieve, optionally rerank, and build context for an LLM prompt."""
        apply_reranker = self.use_reranker if use_reranker is None else use_reranker

        strategy_parts = []
        if use_dense:
            strategy_parts.append("dense")
        if use_bm25:
            strategy_parts.append("bm25")
        if apply_reranker:
            strategy_parts.append("reranked")
        strategy = "+".join(strategy_parts) or "none"

        candidates = await self._retriever.search(
            db=db,
            query=query,
            top_k=self.candidate_k if apply_reranker else self.top_k,
            candidate_k=self.candidate_k,
            use_dense=use_dense,
            use_bm25=use_bm25,
        )
        n_candidates = len(candidates)

        if apply_reranker and candidates:
            final = self._reranker.rerank(query, candidates, top_k=self.top_k)
        else:
            final = candidates[: self.top_k]

        context_text = _build_context(final, MAX_CONTEXT_CHARS)
        sources = [
            SourceAttribution(
                doc_title=c.doc_title,
                doc_category=c.doc_category,
                doc_path=c.doc_path,
                doc_version=c.doc_version,
                chunk_index=c.chunk_index,
            )
            for c in final
        ]

        return RAGResult(
            query=query,
            chunks=final,
            context_text=context_text,
            sources=sources,
            retrieval_strategy=strategy,
            n_candidates_retrieved=n_candidates,
        )
