from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import Optional


@dataclass
class GroundednessResult:
    qa_id: str
    question: str
    expected_answer: str
    context: str
    # Fraction of expected-answer tokens found in retrieved context
    context_coverage: float
    # Token-level F1 between expected answer and context
    answer_context_f1: float
    # Whether retrieved doc IDs intersect with expected doc IDs
    doc_id_hit: bool
    expected_doc_ids: list[str]
    retrieved_doc_ids: list[str]

    @property
    def grounded(self) -> bool:
        """Proxy for groundedness: context covers ≥70% of expected answer tokens."""
        return self.context_coverage >= 0.70


def _normalize(text: str) -> list[str]:
    """Lowercase, remove punctuation, split into tokens."""
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    return [t for t in text.split() if t]


_STOP = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "being have has had do does did will would shall should may might can could "
    "it its this that these those i you he she we they my your his her our them".split()
)


def _content_tokens(text: str) -> list[str]:
    return [t for t in _normalize(text) if t not in _STOP]


def _token_f1(pred_tokens: list[str], gold_tokens: list[str]) -> float:
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = set(pred_tokens) & set(gold_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def _context_coverage(expected_answer: str, context: str) -> float:
    """Fraction of expected-answer content tokens present in context."""
    answer_tokens = _content_tokens(expected_answer)
    if not answer_tokens:
        return 0.0
    context_set = set(_content_tokens(context))
    return len(set(answer_tokens) & context_set) / len(answer_tokens)


def score_groundedness(
    qa_id: str,
    question: str,
    expected_answer: str,
    context: str,
    expected_doc_ids: list[str],
    retrieved_doc_ids: list[str],
) -> GroundednessResult:
    """Compute lexical groundedness metrics for a single QA pair."""
    coverage = _context_coverage(expected_answer, context)
    ctx_tokens = _content_tokens(context)
    ans_tokens = _content_tokens(expected_answer)
    f1 = _token_f1(ctx_tokens, ans_tokens)
    doc_hit = bool(set(expected_doc_ids) & set(retrieved_doc_ids))
    return GroundednessResult(
        qa_id=qa_id,
        question=question,
        expected_answer=expected_answer,
        context=context[:500],  # truncate for storage
        context_coverage=round(coverage, 4),
        answer_context_f1=round(f1, 4),
        doc_id_hit=doc_hit,
        expected_doc_ids=expected_doc_ids,
        retrieved_doc_ids=retrieved_doc_ids,
    )


def aggregate_groundedness(results: list[GroundednessResult]) -> dict:
    if not results:
        return {}
    n = len(results)
    return {
        "n_queries": n,
        "mean_context_coverage": round(sum(r.context_coverage for r in results) / n, 4),
        "mean_answer_context_f1": round(sum(r.answer_context_f1 for r in results) / n, 4),
        "doc_id_hit_rate": round(sum(r.doc_id_hit for r in results) / n, 4),
        "grounded_rate": round(sum(r.grounded for r in results) / n, 4),
    }
