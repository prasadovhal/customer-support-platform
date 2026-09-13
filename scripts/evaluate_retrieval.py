#!/usr/bin/env python
"""Evaluate retrieval quality against the golden QA and retrieval evaluation sets.

Offline mode (default): builds BM25 index from KB files — no DB required.
Online mode (--online):  runs full hybrid retrieval via the database.

Usage:
    python scripts/evaluate_retrieval.py                     # offline BM25
    python scripts/evaluate_retrieval.py --eval-set retrieval_eval
    python scripts/evaluate_retrieval.py --save-baseline     # save as new baseline
    python scripts/evaluate_retrieval.py --check-gate        # compare vs baseline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

GOLDEN_QA_PATH = Path("data/evaluation/golden_qa.jsonl")
RETRIEVAL_EVAL_PATH = Path("data/evaluation/retrieval_eval.jsonl")
RESULTS_DIR = Path("data/evaluation/results")
BASELINE_PATH = Path("data/evaluation/baselines/retrieval_baseline.json")
KB_DIR = Path("data/raw/knowledge_base")


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality")
    parser.add_argument(
        "--eval-set",
        default="golden_qa",
        choices=["golden_qa", "retrieval_eval", "both"],
        help="Evaluation dataset to use (default: golden_qa)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Retrieve top-K chunks per query (default: 10)",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current results as the regression baseline",
    )
    parser.add_argument(
        "--check-gate",
        action="store_true",
        help="Compare against baseline and exit non-zero if gate fails",
    )
    return parser.parse_args()


def run_eval(eval_set: str, top_k: int) -> "RetrievalEvalReport":
    from app.evaluation.retrieval_eval import evaluate_bm25_offline

    if eval_set == "golden_qa":
        records = load_jsonl(GOLDEN_QA_PATH)
        name = "golden_qa"
    elif eval_set == "retrieval_eval":
        records = load_jsonl(RETRIEVAL_EVAL_PATH)
        name = "retrieval_eval"
    else:
        records = load_jsonl(GOLDEN_QA_PATH) + load_jsonl(RETRIEVAL_EVAL_PATH)
        name = "combined"

    logger.info(f"Running offline BM25 evaluation on {name} ({len(records)} records)")
    return evaluate_bm25_offline(records, KB_DIR, top_k=top_k, eval_set_name=name)


def save_baseline(report: "RetrievalEvalReport") -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(report.metrics.to_dict(), f, indent=2)
    logger.info(f"Baseline saved → {BASELINE_PATH}")


def check_gate(report: "RetrievalEvalReport") -> bool:
    from app.evaluation.metrics import EvaluationGate, RetrievalMetrics

    if not BASELINE_PATH.exists():
        logger.warning(f"No baseline found at {BASELINE_PATH}; skipping gate check")
        return True

    with open(BASELINE_PATH) as f:
        baseline_data = json.load(f)

    baseline = RetrievalMetrics(**{
        k: v for k, v in baseline_data.items() if k != "n_queries"
    })
    baseline.n_queries = baseline_data.get("n_queries", 0)

    gate = EvaluationGate()
    passed, violations = gate.check(baseline, report.metrics)

    if violations:
        print(f"\n{'!'*65}")
        print("GATE FAILED — Retrieval quality regression detected:")
        for v in violations:
            print(
                f"  {v.metric}: baseline={v.baseline:.4f}  current={v.current:.4f}"
                f"  regression={v.regression_pct:.1f}%  (threshold={v.threshold_pct}%)"
            )
        print("!" * 65)
    else:
        print("\n✓ Gate passed — no regression beyond threshold")

    return passed


def main() -> None:
    args = parse_args()

    eval_sets = ["golden_qa", "retrieval_eval"] if args.eval_set == "both" else [args.eval_set]

    all_passed = True
    for eval_set in eval_sets:
        report = run_eval(eval_set, top_k=args.top_k)
        report.print_summary()

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = RESULTS_DIR / f"retrieval_{eval_set}.json"
        report.save(out_path)
        logger.info(f"Results saved → {out_path}")

        if args.save_baseline and eval_set == "golden_qa":
            save_baseline(report)

        if args.check_gate and eval_set == "golden_qa":
            if not check_gate(report):
                all_passed = False

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
