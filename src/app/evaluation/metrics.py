from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field


@dataclass
class RetrievalMetrics:
    """Per-query and aggregate retrieval metrics."""

    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    precision_at_5: float = 0.0
    mrr: float = 0.0
    ndcg_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    n_queries: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of relevant documents found in the top-k retrieved set."""
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of top-k retrieved documents that are relevant."""
    if k == 0:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / k


def mrr(retrieved: list[str], relevant: list[str]) -> float:
    """Mean Reciprocal Rank: reciprocal of the rank of the first relevant document."""
    relevant_set = set(relevant)
    for rank, doc_id in enumerate(retrieved, 1):
        if doc_id in relevant_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """nDCG@K with binary relevance (1 if relevant, 0 otherwise)."""
    relevant_set = set(relevant)
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(retrieved[:k], 1)
        if doc_id in relevant_set
    )
    # Ideal DCG: relevant docs ranked first
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0.0 else 0.0


def compute_retrieval_metrics(
    per_query_results: list[tuple[list[str], list[str]]],
) -> RetrievalMetrics:
    """Aggregate metrics over a list of (retrieved_ids, relevant_ids) pairs."""
    n = len(per_query_results)
    if n == 0:
        return RetrievalMetrics()

    def _mean(fn, k=None):
        if k is not None:
            return sum(fn(r, g, k) for r, g in per_query_results) / n
        return sum(fn(r, g) for r, g in per_query_results) / n

    return RetrievalMetrics(
        recall_at_1=_mean(recall_at_k, 1),
        recall_at_3=_mean(recall_at_k, 3),
        recall_at_5=_mean(recall_at_k, 5),
        recall_at_10=_mean(recall_at_k, 10),
        precision_at_1=_mean(precision_at_k, 1),
        precision_at_3=_mean(precision_at_k, 3),
        precision_at_5=_mean(precision_at_k, 5),
        mrr=_mean(mrr),
        ndcg_at_5=_mean(ndcg_at_k, 5),
        ndcg_at_10=_mean(ndcg_at_k, 10),
        n_queries=n,
    )


# ── Regression Gate (EVAL-006) ──────────────────────────────────────────────


@dataclass
class GateViolation:
    metric: str
    baseline: float
    current: float
    regression_pct: float
    threshold_pct: float


@dataclass
class EvaluationGate:
    """Quality gate: blocks promotion if metrics regress beyond thresholds.

    Thresholds per EVAL-006:
      - Recall@5 relative regression > 5% → block
      - nDCG@5  relative regression > 5% → block
      - MRR     relative regression > 5% → block
    """

    THRESHOLDS: dict[str, float] = field(
        default_factory=lambda: {
            "recall_at_5": 0.05,
            "ndcg_at_5": 0.05,
            "mrr": 0.05,
        }
    )

    def check(
        self,
        baseline: RetrievalMetrics,
        current: RetrievalMetrics,
    ) -> tuple[bool, list[GateViolation]]:
        """Return (passed, violations). passed=True means no blocking regressions."""
        violations: list[GateViolation] = []
        for metric, threshold in self.THRESHOLDS.items():
            base_val = getattr(baseline, metric, None)
            curr_val = getattr(current, metric, None)
            if base_val is None or curr_val is None or base_val == 0.0:
                continue
            regression = (base_val - curr_val) / base_val
            if regression > threshold:
                violations.append(
                    GateViolation(
                        metric=metric,
                        baseline=base_val,
                        current=curr_val,
                        regression_pct=round(regression * 100, 2),
                        threshold_pct=round(threshold * 100, 1),
                    )
                )
        return len(violations) == 0, violations
