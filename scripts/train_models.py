#!/usr/bin/env python
"""Train classical ML models for ticket intelligence.

Usage:
    python scripts/train_models.py
    python scripts/train_models.py --task category --model-type logistic_regression
    python scripts/train_models.py --task all --model-type all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src/ is on the path when running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from app.ml.models import ALL_MODEL_TYPES, ALL_TASK_NAMES, ModelType
from app.ml.registry import ModelRegistry
from app.ml.trainer import ModelTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train ticket ML models")
    parser.add_argument(
        "--task",
        default="all",
        choices=["all"] + ALL_TASK_NAMES,
        help="Task to train (default: all)",
    )
    parser.add_argument(
        "--model-type",
        default="all",
        dest="model_type",
        choices=["all"] + list(ALL_MODEL_TYPES),
        help="Model type to train (default: all)",
    )
    return parser.parse_args()


def print_summary(results: list[dict]) -> None:
    print(f"\n{'='*72}")
    print(f"{'Task':<20} {'Model':<25} {'Val Macro F1':>12} {'Test Macro F1':>13}")
    print(f"{'-'*72}")
    for r in results:
        val_f1 = r["val_report"].macro_f1
        test_f1 = r["test_report"].macro_f1
        special = r["val_report"].special_metrics
        line = f"{r['task']:<20} {r['model_type']:<25} {val_f1:>12.4f} {test_f1:>13.4f}"
        if special:
            extras = "  " + "  ".join(f"{k}={v:.3f}" for k, v in special.items())
            line += extras
        print(line)
    print(f"{'='*72}\n")


def main() -> None:
    args = parse_args()
    tasks = ALL_TASK_NAMES if args.task == "all" else [args.task]
    model_types: list[ModelType] = (
        list(ALL_MODEL_TYPES) if args.model_type == "all" else [args.model_type]
    )

    logger.info(f"Tasks: {tasks}")
    logger.info(f"Model types: {model_types}")

    trainer = ModelTrainer()
    results = trainer.train_all(tasks=tasks, model_types=model_types)

    print_summary(results)
    logger.info(f"Training complete. {len(results)} model(s) saved to models/")


if __name__ == "__main__":
    main()
