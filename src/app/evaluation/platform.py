from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from app.evaluation.groundedness import aggregate_groundedness, score_groundedness
from app.evaluation.metrics import (
    EvaluationGate,
    RetrievalMetrics,
    compute_retrieval_metrics,
)


@dataclass
class QAPair:
    eval_id: str
    question: str
    expected_answer: str
    relevant_doc_ids: list[str]
    difficulty: str = "medium"
    query_type: str = "general"


@dataclass
class AgentEvalScenario:
    scenario_id: str
    message: str
    expected_intent: str
    expected_outcome: str


@dataclass
class AgentEvalResult:
    scenario_id: str
    expected_intent: str
    actual_intent: Optional[str]
    expected_outcome: str
    actual_outcome: str
    intent_correct: bool
    outcome_correct: bool


@dataclass
class EvaluationReport:
    timestamp: str
    retrieval_metrics: dict
    groundedness_metrics: dict
    agent_metrics: dict
    gate_passed: bool = True
    gate_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "retrieval_metrics": self.retrieval_metrics,
            "groundedness_metrics": self.groundedness_metrics,
            "agent_metrics": self.agent_metrics,
            "gate_passed": self.gate_passed,
            "gate_violations": self.gate_violations,
        }

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def print_summary(self) -> None:
        print(f"Evaluation Report [{self.timestamp}]")
        print(f"  Gate passed: {self.gate_passed}")
        if self.gate_violations:
            print(f"  Gate violations: {', '.join(self.gate_violations)}")
        rm = self.retrieval_metrics
        if rm:
            print(
                f"  Retrieval — recall@5={rm.get('recall_at_5', 'n/a')}"
                f"  ndcg@5={rm.get('ndcg_at_5', 'n/a')}"
                f"  mrr={rm.get('mrr', 'n/a')}"
            )
        gm = self.groundedness_metrics
        if gm:
            print(
                f"  Groundedness — coverage={gm.get('mean_context_coverage', 'n/a')}"
                f"  grounded_rate={gm.get('grounded_rate', 'n/a')}"
            )
        am = self.agent_metrics
        if am:
            print(
                f"  Agent — intent_accuracy={am.get('intent_accuracy', 'n/a')}"
                f"  outcome_accuracy={am.get('outcome_accuracy', 'n/a')}"
            )


class EvaluationPlatform:
    def __init__(self, gate: EvaluationGate | None = None) -> None:
        self._gate = gate if gate is not None else EvaluationGate()

    def evaluate_retrieval(
        self,
        qa_pairs: list[QAPair],
        retrieve_fn: Callable[[str], list[str]],
    ) -> RetrievalMetrics:
        per_query: list[tuple[list[str], list[str]]] = []
        for pair in qa_pairs:
            retrieved = retrieve_fn(pair.question)
            per_query.append((retrieved, pair.relevant_doc_ids))
        return compute_retrieval_metrics(per_query)

    def evaluate_groundedness(
        self,
        qa_pairs: list[QAPair],
        context_fn: Callable[[str], tuple[str, list[str]]],
    ) -> dict:
        results = []
        for pair in qa_pairs:
            context_text, retrieved_doc_ids = context_fn(pair.question)
            result = score_groundedness(
                qa_id=pair.eval_id,
                question=pair.question,
                expected_answer=pair.expected_answer,
                context=context_text,
                expected_doc_ids=pair.relevant_doc_ids,
                retrieved_doc_ids=retrieved_doc_ids,
            )
            results.append(result)
        return aggregate_groundedness(results)

    def evaluate_agent(
        self,
        scenarios: list[AgentEvalScenario],
        agent_fn: Callable[[str], tuple[Optional[str], str]],
    ) -> dict:
        results: list[AgentEvalResult] = []
        for scenario in scenarios:
            actual_intent, actual_outcome = agent_fn(scenario.message)
            results.append(
                AgentEvalResult(
                    scenario_id=scenario.scenario_id,
                    expected_intent=scenario.expected_intent,
                    actual_intent=actual_intent,
                    expected_outcome=scenario.expected_outcome,
                    actual_outcome=actual_outcome,
                    intent_correct=actual_intent == scenario.expected_intent,
                    outcome_correct=actual_outcome == scenario.expected_outcome,
                )
            )
        n = len(results)
        if n == 0:
            return {"n_scenarios": 0, "intent_accuracy": 0.0, "outcome_accuracy": 0.0}
        return {
            "n_scenarios": n,
            "intent_accuracy": round(sum(r.intent_correct for r in results) / n, 4),
            "outcome_accuracy": round(sum(r.outcome_correct for r in results) / n, 4),
        }

    def run(
        self,
        qa_pairs: list[QAPair],
        retrieve_fn: Callable[[str], list[str]],
        context_fn: Callable[[str], tuple[str, list[str]]],
        scenarios: list[AgentEvalScenario] | None = None,
        agent_fn: Callable[[str], tuple[Optional[str], str]] | None = None,
        baseline: RetrievalMetrics | None = None,
    ) -> EvaluationReport:
        retrieval_metrics = self.evaluate_retrieval(qa_pairs, retrieve_fn)
        groundedness_metrics = self.evaluate_groundedness(qa_pairs, context_fn)

        agent_metrics: dict = {}
        if scenarios is not None and agent_fn is not None:
            agent_metrics = self.evaluate_agent(scenarios, agent_fn)

        gate_passed = True
        gate_violations: list[str] = []
        if baseline is not None:
            gate_passed, violations = self._gate.check(baseline, retrieval_metrics)
            gate_violations = [
                f"{v.metric}: {v.regression_pct}% regression (threshold {v.threshold_pct}%)"
                for v in violations
            ]

        return EvaluationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            retrieval_metrics=retrieval_metrics.to_dict(),
            groundedness_metrics=groundedness_metrics,
            agent_metrics=agent_metrics,
            gate_passed=gate_passed,
            gate_violations=gate_violations,
        )
