from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd
from loguru import logger
from sklearn.model_selection import train_test_split

from app.ml.evaluator import ModelEvaluator
from app.ml.features import FEATURE_VERSION, extract_texts
from app.ml.models import (
    ALL_MODEL_TYPES,
    ALL_TASK_NAMES,
    TASK_CONFIGS,
    ModelType,
    TaskConfig,
    build_pipeline,
)
from app.ml.registry import ModelRegistry

MODELS_DIR = Path("models")
DATA_PATH = Path("data/structured/tickets/support_tickets.csv")


def _load_training_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalise boolean escalated column → string labels
    df["escalated"] = df["escalated"].astype(str).str.lower().str.strip()
    # Drop rows with null labels for any task
    df = df.dropna(subset=["category", "priority", "sentiment", "assigned_team"])
    df = df[df["message"].notna() & (df["message"].str.strip() != "")]
    return df.reset_index(drop=True)


def _model_dir(task: str, model_type: str) -> Path:
    return MODELS_DIR / task / model_type


class ModelTrainer:
    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        models_dir: Path = MODELS_DIR,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.models_dir = models_dir
        self.evaluator = ModelEvaluator()

    def train_task(
        self,
        df: pd.DataFrame,
        config: TaskConfig,
        model_type: ModelType,
    ) -> dict[str, Any]:
        texts = extract_texts(df)
        y = df[config.label_column].astype(str).str.strip().tolist()

        # Stratified 60/20/20 split
        X_train, X_tmp, y_train, y_tmp = train_test_split(
            texts, y, test_size=0.40, stratify=y, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=42
        )

        pipeline = build_pipeline(model_type, use_class_weight=config.use_class_weight)
        pipeline.fit(X_train, y_train)

        val_report = self.evaluator.evaluate(
            pipeline,
            X_val,
            y_val,
            task_name=config.name,
            model_type=model_type,
            dataset="val",
        )
        test_report = self.evaluator.evaluate(
            pipeline,
            X_test,
            y_test,
            task_name=config.name,
            model_type=model_type,
            dataset="test",
        )

        # Persist model
        out_dir = self.models_dir / config.name / model_type
        out_dir.mkdir(parents=True, exist_ok=True)
        model_path = out_dir / "model.joblib"
        joblib.dump(pipeline, model_path)

        metadata = {
            "feature_version": FEATURE_VERSION,
            "training_size": len(X_train),
            "val_size": len(X_val),
            "test_size": len(X_test),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "label_column": config.label_column,
            "class_names": config.class_names,
            "val_metrics": {
                "accuracy": val_report.accuracy,
                "macro_f1": val_report.macro_f1,
                "weighted_f1": val_report.weighted_f1,
                **val_report.special_metrics,
            },
            "test_metrics": {
                "accuracy": test_report.accuracy,
                "macro_f1": test_report.macro_f1,
                "weighted_f1": test_report.weighted_f1,
                **test_report.special_metrics,
            },
        }

        # Save metadata JSON alongside model
        with open(out_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Save evaluation reports
        self.evaluator.save_report(val_report, out_dir / "val_report.json")
        self.evaluator.save_report(test_report, out_dir / "test_report.json")

        self.registry.register(
            task=config.name,
            model_type=model_type,
            model_path=str(model_path),
            metadata=metadata,
        )

        logger.info(
            f"[{config.name}/{model_type}] val macro_f1={val_report.macro_f1:.4f}"
            f" test macro_f1={test_report.macro_f1:.4f}"
        )
        return {
            "task": config.name,
            "model_type": model_type,
            "model_path": str(model_path),
            "val_report": val_report,
            "test_report": test_report,
        }

    def train_all(
        self,
        tasks: Optional[list[str]] = None,
        model_types: Optional[list[ModelType]] = None,
    ) -> list[dict[str, Any]]:
        df = _load_training_data()
        logger.info(f"Loaded {len(df)} training records from {DATA_PATH}")

        tasks = tasks or ALL_TASK_NAMES
        model_types = model_types or ALL_MODEL_TYPES
        results = []

        for task_name in tasks:
            config = TASK_CONFIGS[task_name]
            for model_type in model_types:
                logger.info(f"Training {task_name} / {model_type} ...")
                result = self.train_task(df, config, model_type)
                results.append(result)

        return results
