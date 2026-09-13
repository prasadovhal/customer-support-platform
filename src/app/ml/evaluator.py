from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


@dataclass
class ClassMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvaluationReport:
    task_name: str
    model_type: str
    dataset: str
    n_samples: int
    accuracy: float
    macro_f1: float
    weighted_f1: float
    per_class: list[ClassMetrics]
    confusion_matrix: list[list[int]]
    special_metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["per_class"] = [asdict(c) for c in self.per_class]
        return d


class ModelEvaluator:
    def evaluate(
        self,
        pipeline: Any,
        texts: list[str],
        y_true: list[str],
        task_name: str,
        model_type: str,
        dataset: str = "unknown",
    ) -> EvaluationReport:
        y_pred = pipeline.predict(texts)
        labels = sorted(set(y_true) | set(y_pred))

        acc = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

        precisions, recalls, f1s, supports = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, zero_division=0
        )
        per_class = [
            ClassMetrics(
                label=labels[i],
                precision=float(precisions[i]),
                recall=float(recalls[i]),
                f1=float(f1s[i]),
                support=int(supports[i]),
            )
            for i in range(len(labels))
        ]

        cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

        special: dict[str, float] = {}
        if task_name == "priority":
            p0_recall = _class_recall(y_true, y_pred, "P0")
            p1_recall = _class_recall(y_true, y_pred, "P1")
            special["P0_recall"] = p0_recall
            special["P1_recall"] = p1_recall

        if task_name == "escalation":
            escalation_recall = _class_recall(y_true, y_pred, "true")
            special["escalation_recall"] = escalation_recall

        return EvaluationReport(
            task_name=task_name,
            model_type=model_type,
            dataset=dataset,
            n_samples=len(y_true),
            accuracy=float(acc),
            macro_f1=float(macro_f1),
            weighted_f1=float(weighted_f1),
            per_class=per_class,
            confusion_matrix=cm,
            special_metrics=special,
        )

    def format_report(self, report: EvaluationReport) -> str:
        lines = [
            f"\n{'='*60}",
            f"Task:        {report.task_name}",
            f"Model:       {report.model_type}",
            f"Dataset:     {report.dataset}  (n={report.n_samples})",
            f"Accuracy:    {report.accuracy:.4f}",
            f"Macro F1:    {report.macro_f1:.4f}",
            f"Weighted F1: {report.weighted_f1:.4f}",
        ]
        if report.special_metrics:
            for k, v in report.special_metrics.items():
                lines.append(f"{k:<12}: {v:.4f}")
        lines.append("")
        lines.append(f"{'Class':<30} {'Prec':>6} {'Rec':>6} {'F1':>6} {'N':>6}")
        lines.append("-" * 60)
        for cm in report.per_class:
            lines.append(
                f"{cm.label:<30} {cm.precision:>6.3f} {cm.recall:>6.3f} {cm.f1:>6.3f} {cm.support:>6}"
            )
        lines.append("=" * 60)
        return "\n".join(lines)

    def save_report(self, report: EvaluationReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)


def _class_recall(y_true: list[str], y_pred: list[str], label: str) -> float:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0
