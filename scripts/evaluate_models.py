#!/usr/bin/env python
"""Evaluate registered ML models against the held-out classification evaluation set.

Usage:
    python scripts/evaluate_models.py
    python scripts/evaluate_models.py --task category
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from loguru import logger

from app.ml.evaluator import ModelEvaluator
from app.ml.models import ALL_TASK_NAMES, TASK_CONFIGS
from app.ml.registry import ModelRegistry

EVAL_PATH = Path("data/evaluation/classification_eval.csv")
RESULTS_PATH = Path("data/evaluation/ml_evaluation_results.json")

# Map evaluation CSV columns to task label columns
EVAL_COLUMN_MAP = {
    "category": "true_category",
    "priority": "true_priority",
    # sentiment and routing are not in the eval CSV
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ML models on holdout set")
    parser.add_argument(
        "--task",
        default="all",
        choices=["all"] + list(EVAL_COLUMN_MAP.keys()),
        help="Task to evaluate (default: all available in eval CSV)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(EVAL_PATH)
    logger.info(f"Loaded {len(df)} holdout evaluation records from {EVAL_PATH}")

    registry = ModelRegistry()
    evaluator = ModelEvaluator()
    all_results: list[dict] = []

    tasks_to_eval = (
        list(EVAL_COLUMN_MAP.keys())
        if args.task == "all"
        else [args.task]
    )

    print(f"\n{'='*80}")
    print(f"{'Task':<20} {'Model':<25} {'Accuracy':>9} {'Macro F1':>9} {'Weighted F1':>12}")
    print(f"{'-'*80}")

    for task_name in tasks_to_eval:
        label_col = EVAL_COLUMN_MAP[task_name]
        if label_col not in df.columns:
            logger.warning(f"Column '{label_col}' not in eval CSV; skipping {task_name}")
            continue

        texts = df["message"].astype(str).str.strip().str.lower().tolist()
        y_true = df[label_col].astype(str).tolist()

        versions = registry.list_versions(task_name)
        if not versions:
            logger.warning(f"No registered models for task '{task_name}'; skipping")
            continue

        for entry in versions:
            model_type = entry["model_type"]
            try:
                pipeline = registry.load_model(task_name, model_type=model_type)
            except FileNotFoundError:
                logger.warning(f"Model file missing for {task_name}/{model_type}")
                continue

            report = evaluator.evaluate(
                pipeline, texts, y_true,
                task_name=task_name,
                model_type=model_type,
                dataset="holdout",
            )

            special_str = ""
            if report.special_metrics:
                special_str = "  " + "  ".join(
                    f"{k}={v:.3f}" for k, v in report.special_metrics.items()
                )

            print(
                f"{task_name:<20} {model_type:<25} "
                f"{report.accuracy:>9.4f} {report.macro_f1:>9.4f} {report.weighted_f1:>12.4f}"
                + special_str
            )
            all_results.append(report.to_dict())

    print(f"{'='*80}\n")

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
