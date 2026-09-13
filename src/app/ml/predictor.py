from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from loguru import logger

from app.ml.features import extract_text
from app.ml.registry import ModelRegistry


@dataclass
class CategoryPrediction:
    label: str
    confidence: float
    top3: list[dict[str, float]]


@dataclass
class PriorityPrediction:
    label: str
    confidence: float
    p0_prob: float
    p1_prob: float


@dataclass
class SentimentPrediction:
    label: str
    confidence: float


@dataclass
class EscalationPrediction:
    escalation_risk: float
    will_escalate: bool


@dataclass
class RoutingPrediction:
    team: str
    confidence: float


@dataclass
class AllPredictions:
    category: CategoryPrediction
    priority: PriorityPrediction
    sentiment: SentimentPrediction
    escalation: EscalationPrediction
    routing: RoutingPrediction


class TicketPredictor:
    """Inference interface — lazy-loads best models from registry on first call."""

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self._registry = registry or ModelRegistry()
        self._models: dict[str, Any] = {}

    def _model(self, task: str) -> Any:
        if task not in self._models:
            try:
                self._models[task] = self._registry.load_model(task)
            except FileNotFoundError:
                logger.warning(f"No trained model found for task '{task}'")
                raise
        return self._models[task]

    def _text(self, message: str, subject: str = "") -> str:
        import pandas as pd
        row = pd.Series({"message": message, "subject": subject})
        return extract_text(row)

    def predict_category(self, message: str, subject: str = "") -> CategoryPrediction:
        pipeline = self._model("category")
        text = self._text(message, subject)
        proba = pipeline.predict_proba([text])[0]
        classes = pipeline.classes_

        idx = int(np.argmax(proba))
        top3 = sorted(
            [{"label": c, "probability": float(p)} for c, p in zip(classes, proba)],
            key=lambda x: x["probability"],
            reverse=True,
        )[:3]
        return CategoryPrediction(
            label=str(classes[idx]),
            confidence=float(proba[idx]),
            top3=top3,
        )

    def predict_priority(self, message: str, subject: str = "") -> PriorityPrediction:
        pipeline = self._model("priority")
        text = self._text(message, subject)
        proba = pipeline.predict_proba([text])[0]
        classes = list(pipeline.classes_)

        idx = int(np.argmax(proba))
        p0_prob = float(proba[classes.index("P0")]) if "P0" in classes else 0.0
        p1_prob = float(proba[classes.index("P1")]) if "P1" in classes else 0.0
        return PriorityPrediction(
            label=str(classes[idx]),
            confidence=float(proba[idx]),
            p0_prob=p0_prob,
            p1_prob=p1_prob,
        )

    def predict_sentiment(self, message: str, subject: str = "") -> SentimentPrediction:
        pipeline = self._model("sentiment")
        text = self._text(message, subject)
        proba = pipeline.predict_proba([text])[0]
        classes = pipeline.classes_
        idx = int(np.argmax(proba))
        return SentimentPrediction(
            label=str(classes[idx]),
            confidence=float(proba[idx]),
        )

    def predict_escalation(self, message: str, subject: str = "") -> EscalationPrediction:
        pipeline = self._model("escalation")
        text = self._text(message, subject)
        proba = pipeline.predict_proba([text])[0]
        classes = list(pipeline.classes_)
        true_prob = float(proba[classes.index("true")]) if "true" in classes else 0.0
        return EscalationPrediction(
            escalation_risk=true_prob,
            will_escalate=true_prob >= 0.5,
        )

    def predict_routing(self, message: str, subject: str = "") -> RoutingPrediction:
        pipeline = self._model("routing")
        text = self._text(message, subject)
        proba = pipeline.predict_proba([text])[0]
        classes = pipeline.classes_
        idx = int(np.argmax(proba))
        return RoutingPrediction(
            team=str(classes[idx]),
            confidence=float(proba[idx]),
        )

    def predict_all(self, message: str, subject: str = "") -> AllPredictions:
        return AllPredictions(
            category=self.predict_category(message, subject),
            priority=self.predict_priority(message, subject),
            sentiment=self.predict_sentiment(message, subject),
            escalation=self.predict_escalation(message, subject),
            routing=self.predict_routing(message, subject),
        )
