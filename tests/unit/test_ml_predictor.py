from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.ml.predictor import TicketPredictor


def _make_mock_pipeline(classes: list[str], proba: list[float]) -> MagicMock:
    pipeline = MagicMock()
    pipeline.classes_ = np.array(classes)
    pipeline.predict_proba.return_value = np.array([proba])
    return pipeline


@pytest.fixture
def predictor() -> TicketPredictor:
    registry = MagicMock()
    return TicketPredictor(registry=registry)


def test_predict_category_returns_highest_prob_label(predictor: TicketPredictor) -> None:
    pipeline = _make_mock_pipeline(
        ["account", "returns", "shipping"],
        [0.1, 0.7, 0.2],
    )
    predictor._models["category"] = pipeline
    result = predictor.predict_category("I want to return my item")
    assert result.label == "returns"
    assert abs(result.confidence - 0.7) < 1e-6
    assert len(result.top3) == 3


def test_predict_priority_extracts_p0_p1_probs(predictor: TicketPredictor) -> None:
    pipeline = _make_mock_pipeline(
        ["P0", "P1", "P2", "P3"],
        [0.05, 0.15, 0.50, 0.30],
    )
    predictor._models["priority"] = pipeline
    result = predictor.predict_priority("My account was hacked")
    assert result.label == "P2"
    assert abs(result.p0_prob - 0.05) < 1e-6
    assert abs(result.p1_prob - 0.15) < 1e-6


def test_predict_escalation_uses_true_class_prob(predictor: TicketPredictor) -> None:
    pipeline = _make_mock_pipeline(["false", "true"], [0.3, 0.7])
    predictor._models["escalation"] = pipeline
    result = predictor.predict_escalation("This is unacceptable!")
    assert result.will_escalate is True
    assert abs(result.escalation_risk - 0.7) < 1e-6


def test_predict_escalation_below_threshold(predictor: TicketPredictor) -> None:
    pipeline = _make_mock_pipeline(["false", "true"], [0.8, 0.2])
    predictor._models["escalation"] = pipeline
    result = predictor.predict_escalation("Where is my package?")
    assert result.will_escalate is False


def test_predict_all_calls_all_tasks(predictor: TicketPredictor) -> None:
    for task, classes, proba in [
        ("category", ["shipping", "returns"], [0.6, 0.4]),
        ("priority", ["P0", "P1", "P2", "P3"], [0.1, 0.1, 0.6, 0.2]),
        ("sentiment", ["neutral", "negative"], [0.7, 0.3]),
        ("escalation", ["false", "true"], [0.9, 0.1]),
        ("routing", ["shipping_support", "returns_support"], [0.8, 0.2]),
    ]:
        predictor._models[task] = _make_mock_pipeline(classes, proba)

    result = predictor.predict_all("Where is my shipment?")
    assert result.category.label in ["shipping", "returns"]
    assert result.priority.label in ["P0", "P1", "P2", "P3"]
    assert result.sentiment.label in ["neutral", "negative"]
    assert isinstance(result.escalation.will_escalate, bool)
    assert result.routing.team in ["shipping_support", "returns_support"]
