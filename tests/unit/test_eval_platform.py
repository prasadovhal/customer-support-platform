from __future__ import annotations

import pytest

from app.evaluation.metrics import RetrievalMetrics
from app.evaluation.platform import (
    AgentEvalScenario,
    EvaluationPlatform,
    EvaluationReport,
    QAPair,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _qa(eval_id: str, relevant: list[str]) -> QAPair:
    return QAPair(
        eval_id=eval_id,
        question=f"question {eval_id}",
        expected_answer="The answer contains important information about the topic.",
        relevant_doc_ids=relevant,
    )


def _scenario(scenario_id: str, intent: str, outcome: str) -> AgentEvalScenario:
    return AgentEvalScenario(
        scenario_id=scenario_id,
        message=f"message {scenario_id}",
        expected_intent=intent,
        expected_outcome=outcome,
    )


# ── evaluate_retrieval ────────────────────────────────────────────────────────


def test_evaluate_retrieval_perfect():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1", "doc2"]), _qa("q2", ["doc3"])]

    def retrieve_fn(question: str) -> list[str]:
        if "q1" in question:
            return ["doc1", "doc2", "x", "y", "z"]
        return ["doc3", "a", "b", "c", "d"]

    metrics = platform.evaluate_retrieval(pairs, retrieve_fn)
    assert metrics.recall_at_5 == 1.0


def test_evaluate_retrieval_empty_results():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1", "doc2"])]

    metrics = platform.evaluate_retrieval(pairs, lambda q: [])
    assert metrics.recall_at_5 == 0.0
    assert metrics.mrr == 0.0


def test_evaluate_retrieval_partial():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1", "doc2"])]

    # only doc1 returned, not doc2
    metrics = platform.evaluate_retrieval(pairs, lambda q: ["doc1", "x", "y", "z", "w"])
    assert 0.0 < metrics.recall_at_5 < 1.0
    assert metrics.recall_at_5 == pytest.approx(0.5)


# ── evaluate_groundedness ─────────────────────────────────────────────────────


def test_evaluate_groundedness_high_coverage():
    platform = EvaluationPlatform()
    pairs = [
        QAPair(
            eval_id="q1",
            question="What is the topic?",
            expected_answer="important information topic answer",
            relevant_doc_ids=["doc1"],
        )
    ]

    # Context that directly contains the expected answer text
    def context_fn(q: str) -> tuple[str, list[str]]:
        return "important information topic answer found here", ["doc1"]

    result = platform.evaluate_groundedness(pairs, context_fn)
    assert result["mean_context_coverage"] > 0.7
    assert result["grounded_rate"] == 1.0


def test_evaluate_groundedness_empty_context():
    platform = EvaluationPlatform()
    pairs = [
        QAPair(
            eval_id="q1",
            question="What is the answer?",
            expected_answer="specific answer with unique tokens",
            relevant_doc_ids=["doc1"],
        )
    ]

    def context_fn(q: str) -> tuple[str, list[str]]:
        return "", ["doc1"]

    result = platform.evaluate_groundedness(pairs, context_fn)
    assert result["mean_context_coverage"] == 0.0
    assert result["grounded_rate"] == 0.0


# ── evaluate_agent ────────────────────────────────────────────────────────────


def test_evaluate_agent_intent_accuracy():
    platform = EvaluationPlatform()
    scenarios = [
        _scenario("s1", "billing", "resolved"),
        _scenario("s2", "technical", "escalated"),
        _scenario("s3", "general", "resolved"),
    ]

    def agent_fn(message: str) -> tuple[str, str]:
        # correctly predict intent for s1, s2; wrong for s3
        if "s1" in message:
            return "billing", "resolved"
        if "s2" in message:
            return "technical", "escalated"
        return "wrong_intent", "resolved"

    result = platform.evaluate_agent(scenarios, agent_fn)
    assert result["intent_accuracy"] == pytest.approx(2 / 3, abs=1e-4)


def test_evaluate_agent_outcome_accuracy():
    platform = EvaluationPlatform()
    scenarios = [
        _scenario("s1", "billing", "resolved"),
        _scenario("s2", "billing", "escalated"),
    ]

    # always returns correct outcome, wrong intent
    def agent_fn(message: str) -> tuple[str, str]:
        if "s1" in message:
            return "wrong", "resolved"
        return "wrong", "escalated"

    result = platform.evaluate_agent(scenarios, agent_fn)
    assert result["outcome_accuracy"] == 1.0
    assert result["intent_accuracy"] == 0.0


# ── run ───────────────────────────────────────────────────────────────────────


def test_run_produces_full_report():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1"])]
    scenarios = [_scenario("s1", "billing", "resolved")]

    report = platform.run(
        qa_pairs=pairs,
        retrieve_fn=lambda q: ["doc1"],
        context_fn=lambda q: ("doc1 content information", ["doc1"]),
        scenarios=scenarios,
        agent_fn=lambda m: ("billing", "resolved"),
    )

    assert isinstance(report, EvaluationReport)
    assert report.timestamp != ""
    assert "recall_at_5" in report.retrieval_metrics
    assert "mean_context_coverage" in report.groundedness_metrics
    assert "intent_accuracy" in report.agent_metrics
    assert report.gate_passed is True
    assert report.gate_violations == []


def test_run_gate_passes_with_no_regression():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1", "doc2"]), _qa("q2", ["doc3"])]

    # baseline with good metrics
    baseline = RetrievalMetrics(
        recall_at_5=0.8,
        ndcg_at_5=0.8,
        mrr=0.8,
    )

    # current retrieve returns all relevant docs → same or better metrics
    def retrieve_fn(q: str) -> list[str]:
        if "q1" in q:
            return ["doc1", "doc2", "x", "y", "z"]
        return ["doc3", "a", "b", "c", "d"]

    report = platform.run(
        qa_pairs=pairs,
        retrieve_fn=retrieve_fn,
        context_fn=lambda q: ("context text", []),
        baseline=baseline,
    )

    assert report.gate_passed is True
    assert report.gate_violations == []


def test_run_gate_fails_with_regression():
    platform = EvaluationPlatform()
    pairs = [_qa("q1", ["doc1", "doc2"]), _qa("q2", ["doc3", "doc4"])]

    # baseline with very high metrics
    baseline = RetrievalMetrics(
        recall_at_5=1.0,
        ndcg_at_5=1.0,
        mrr=1.0,
    )

    # current retrieve returns nothing → 0 metrics → severe regression
    report = platform.run(
        qa_pairs=pairs,
        retrieve_fn=lambda q: [],
        context_fn=lambda q: ("", []),
        baseline=baseline,
    )

    assert report.gate_passed is False
    assert len(report.gate_violations) > 0
