from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.rag.bm25_index import BM25Index, BM25Result, _tokenize
from app.rag.pipeline import _build_context
from app.rag.retriever import RetrievalResult, _rrf_score


# ---------- RRF scoring ----------

def test_rrf_score_single_retriever() -> None:
    score = _rrf_score([1])
    assert abs(score - 1 / (60 + 1)) < 1e-9


def test_rrf_score_two_retrievers_same_rank() -> None:
    score = _rrf_score([1, 1])
    assert abs(score - 2 / (60 + 1)) < 1e-9


def test_rrf_score_higher_rank_gives_higher_score() -> None:
    score_rank1 = _rrf_score([1])
    score_rank10 = _rrf_score([10])
    assert score_rank1 > score_rank10


def test_rrf_score_only_non_none_ranks_counted() -> None:
    score_both = _rrf_score([1, 1])
    score_one = _rrf_score([1])
    assert score_both > score_one


# ---------- BM25 index ----------

def _make_records(texts: list[str]) -> list[BM25Result]:
    return [
        BM25Result(
            chunk_id=str(i),
            score=0.0,
            text=text,
            doc_title=f"Doc {i}",
            doc_category="test",
            doc_path=f"doc{i}.md",
            chunk_index=0,
        )
        for i, text in enumerate(texts)
    ]


def test_bm25_build_and_search() -> None:
    records = _make_records([
        "return policy 30 days refund",
        "shipping tracking delivery",
        "account password reset security",
    ])
    index = BM25Index()
    index.build(records)
    results = index.search("return refund policy", top_k=3)
    assert len(results) >= 1
    assert results[0][0].chunk_id == "0"  # first doc should rank highest


def test_bm25_empty_corpus_returns_empty() -> None:
    index = BM25Index()
    index.build([])
    results = index.search("anything", top_k=5)
    assert results == []


def test_bm25_no_matching_query_returns_empty() -> None:
    index = BM25Index()
    index.build(_make_records(["cat dog bird"]))
    results = index.search("zzz qqq", top_k=5)
    assert results == []


def test_tokenize_removes_stopwords() -> None:
    tokens = _tokenize("I want to return my item")
    assert "i" not in tokens
    assert "to" not in tokens
    assert "return" in tokens
    assert "item" in tokens


# ---------- Context building ----------

def _make_result(text: str, title: str = "Doc", category: str = "returns") -> RetrievalResult:
    return RetrievalResult(
        chunk_id="x",
        chunk_index=0,
        text=text,
        doc_id="y",
        doc_title=title,
        doc_category=category,
        doc_path="test.md",
        doc_version="1.0",
        rrf_score=1.0,
    )


def test_build_context_includes_source_header() -> None:
    results = [_make_result("Some policy text.", "Return Policy", "returns")]
    ctx = _build_context(results, max_chars=5000)
    assert "Return Policy" in ctx
    assert "returns" in ctx
    assert "Some policy text." in ctx


def test_build_context_respects_max_chars() -> None:
    results = [_make_result("x" * 3000, "Doc A"), _make_result("y" * 3000, "Doc B")]
    ctx = _build_context(results, max_chars=4000)
    assert "Doc B" not in ctx or len(ctx) <= 4200  # second doc may be truncated
