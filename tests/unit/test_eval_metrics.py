from __future__ import annotations

import pytest

from app.evaluation.groundedness import (
    _context_coverage,
    _token_f1,
    aggregate_groundedness,
    score_groundedness,
)
from app.evaluation.metrics import (
    EvaluationGate,
    RetrievalMetrics,
    compute_retrieval_metrics,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


# ── Recall@K ─────────────────────────────────────────────────────────────────


def test_recall_perfect():
    assert recall_at_k(["a", "b", "c"], ["a", "b"], k=3) == 1.0


def test_recall_partial():
    assert recall_at_k(["a", "x", "y"], ["a", "b"], k=3) == 0.5


def test_recall_zero():
    assert recall_at_k(["x", "y"], ["a", "b"], k=5) == 0.0


def test_recall_empty_relevant():
    assert recall_at_k(["a"], [], k=5) == 0.0


def test_recall_k_cuts_retrieved():
    # Only top-2 considered, "b" is at position 3 — not counted
    assert recall_at_k(["a", "x", "b"], ["a", "b"], k=2) == 0.5


# ── Precision@K ──────────────────────────────────────────────────────────────


def test_precision_perfect():
    assert precision_at_k(["a", "b"], ["a", "b", "c"], k=2) == 1.0


def test_precision_half():
    assert precision_at_k(["a", "x"], ["a", "b"], k=2) == 0.5


def test_precision_k_zero():
    assert precision_at_k(["a"], ["a"], k=0) == 0.0


# ── MRR ──────────────────────────────────────────────────────────────────────


def test_mrr_first_rank():
    assert mrr(["a", "b", "c"], ["a"]) == 1.0


def test_mrr_third_rank():
    assert abs(mrr(["x", "y", "a"], ["a"]) - 1 / 3) < 1e-9


def test_mrr_no_hit():
    assert mrr(["x", "y"], ["a", "b"]) == 0.0


def test_mrr_first_of_multiple_relevant():
    # "b" is at rank 1, "a" at rank 3 — MRR should use rank 1
    assert mrr(["b", "x", "a"], ["a", "b"]) == 1.0


# ── nDCG@K ───────────────────────────────────────────────────────────────────


def test_ndcg_perfect():
    assert ndcg_at_k(["a", "b"], ["a", "b"], k=2) == pytest.approx(1.0)


def test_ndcg_zero():
    assert ndcg_at_k(["x", "y"], ["a", "b"], k=2) == 0.0


def test_ndcg_partial_order_matters():
    # Relevant doc at rank 1 should score higher than at rank 2
    score_rank1 = ndcg_at_k(["a", "x"], ["a"], k=2)
    score_rank2 = ndcg_at_k(["x", "a"], ["a"], k=2)
    assert score_rank1 > score_rank2


# ── Aggregate ────────────────────────────────────────────────────────────────


def test_compute_retrieval_metrics_empty():
    m = compute_retrieval_metrics([])
    assert m.n_queries == 0
    assert m.recall_at_5 == 0.0


def test_compute_retrieval_metrics_two_queries():
    pairs = [
        (["a", "b", "c", "d", "e"], ["a", "b"]),  # perfect recall@2
        (["x", "y", "a", "z", "w"], ["a"]),  # recall@5=1.0, recall@3=0.0
    ]
    m = compute_retrieval_metrics(pairs)
    assert m.n_queries == 2
    assert m.recall_at_5 == 1.0


# ── Regression Gate ──────────────────────────────────────────────────────────


def test_gate_passes_no_regression():
    baseline = RetrievalMetrics(
        recall_at_5=0.80, ndcg_at_5=0.75, mrr=0.70, n_queries=70
    )
    current = RetrievalMetrics(recall_at_5=0.80, ndcg_at_5=0.75, mrr=0.70, n_queries=70)
    gate = EvaluationGate()
    passed, violations = gate.check(baseline, current)
    assert passed
    assert violations == []


def test_gate_fails_recall_regression():
    baseline = RetrievalMetrics(
        recall_at_5=0.80, ndcg_at_5=0.75, mrr=0.70, n_queries=70
    )
    # 10% recall regression — beyond 5% threshold
    current = RetrievalMetrics(recall_at_5=0.72, ndcg_at_5=0.75, mrr=0.70, n_queries=70)
    gate = EvaluationGate()
    passed, violations = gate.check(baseline, current)
    assert not passed
    assert any(v.metric == "recall_at_5" for v in violations)


def test_gate_allows_small_regression():
    baseline = RetrievalMetrics(
        recall_at_5=0.80, ndcg_at_5=0.75, mrr=0.70, n_queries=70
    )
    # 3% regression — within 5% threshold
    current = RetrievalMetrics(
        recall_at_5=0.776, ndcg_at_5=0.75, mrr=0.70, n_queries=70
    )
    gate = EvaluationGate()
    passed, violations = gate.check(baseline, current)
    assert passed


# ── Groundedness ─────────────────────────────────────────────────────────────


def test_context_coverage_full():
    assert _context_coverage(
        "return within 30 days", "you can return within 30 days of purchase"
    ) == pytest.approx(1.0)


def test_context_coverage_zero():
    assert (
        _context_coverage("laptop battery warranty", "shipping address update policy")
        == 0.0
    )


def test_token_f1_identical():
    tokens = ["return", "policy", "30", "days"]
    assert _token_f1(tokens, tokens) == pytest.approx(1.0)


def test_score_groundedness_doc_hit():
    result = score_groundedness(
        qa_id="QA-001",
        question="What is the return policy?",
        expected_answer="You can return within 30 days.",
        context="Standard return policy allows returns within 30 days.",
        expected_doc_ids=["KB-RET-001"],
        retrieved_doc_ids=["KB-RET-001", "KB-SHP-001"],
    )
    assert result.doc_id_hit is True
    assert result.context_coverage > 0.5


def test_aggregate_groundedness_grounded_rate():
    r1 = score_groundedness(
        "a",
        "q",
        "return within 30 days",
        "return within 30 days of purchase",
        ["KB-RET-001"],
        ["KB-RET-001"],
    )
    r2 = score_groundedness(
        "b",
        "q",
        "laptop warranty two years",
        "unrelated text here",
        ["KB-WAR-001"],
        ["KB-SHP-001"],
    )
    agg = aggregate_groundedness([r1, r2])
    assert agg["n_queries"] == 2
    assert 0.0 <= agg["grounded_rate"] <= 1.0
