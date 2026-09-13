from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.ml.predictor import (
    AllPredictions,
    CategoryPrediction,
    EscalationPrediction,
    PriorityPrediction,
    RoutingPrediction,
    SentimentPrediction,
    TicketPredictor,
)
from app.ml.registry import ModelRegistry

router = APIRouter(prefix="/ml", tags=["ml"])

# Module-level singletons — loaded once on first request
_registry: Optional[ModelRegistry] = None
_predictor: Optional[TicketPredictor] = None


def _get_predictor() -> TicketPredictor:
    global _registry, _predictor
    if _predictor is None:
        _registry = ModelRegistry()
        _predictor = TicketPredictor(registry=_registry)
    return _predictor


# ---------- Request / Response schemas ----------

class PredictRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    subject: Optional[str] = Field(None, max_length=500)


class ClassProbability(BaseModel):
    label: str
    probability: float


class CategoryResponse(BaseModel):
    label: str
    confidence: float
    top3: list[ClassProbability]


class PriorityResponse(BaseModel):
    label: str
    confidence: float
    p0_prob: float
    p1_prob: float


class SentimentResponse(BaseModel):
    label: str
    confidence: float


class EscalationResponse(BaseModel):
    escalation_risk: float
    will_escalate: bool


class RoutingResponse(BaseModel):
    team: str
    confidence: float


class PredictResponse(BaseModel):
    category: CategoryResponse
    priority: PriorityResponse
    sentiment: SentimentResponse
    escalation: EscalationResponse
    routing: RoutingResponse


class ModelVersionInfo(BaseModel):
    model_type: str
    val_macro_f1: Optional[float]
    registered_at: Optional[str]
    model_path: Optional[str]


class ModelsResponse(BaseModel):
    tasks: dict[str, list[ModelVersionInfo]]


# ---------- Helpers ----------

def _to_category_response(p: CategoryPrediction) -> CategoryResponse:
    return CategoryResponse(
        label=p.label,
        confidence=p.confidence,
        top3=[ClassProbability(label=t["label"], probability=t["probability"]) for t in p.top3],
    )


# ---------- Endpoints ----------

@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Run all ML classifiers on a support message and return predictions."""
    predictor = _get_predictor()
    try:
        result = predictor.predict_all(
            message=request.message,
            subject=request.subject or "",
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML models not available: {exc}. Run train_models.py first.",
        )
    return PredictResponse(
        category=_to_category_response(result.category),
        priority=PriorityResponse(
            label=result.priority.label,
            confidence=result.priority.confidence,
            p0_prob=result.priority.p0_prob,
            p1_prob=result.priority.p1_prob,
        ),
        sentiment=SentimentResponse(
            label=result.sentiment.label,
            confidence=result.sentiment.confidence,
        ),
        escalation=EscalationResponse(
            escalation_risk=result.escalation.escalation_risk,
            will_escalate=result.escalation.will_escalate,
        ),
        routing=RoutingResponse(
            team=result.routing.team,
            confidence=result.routing.confidence,
        ),
    )


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    """List all registered ML models and their validation metrics."""
    predictor = _get_predictor()
    summary = predictor._registry.summary()
    tasks_out: dict[str, list[ModelVersionInfo]] = {}
    for task, versions in summary.items():
        tasks_out[task] = [
            ModelVersionInfo(
                model_type=v["model_type"],
                val_macro_f1=v.get("val_macro_f1"),
                registered_at=v.get("registered_at"),
                model_path=v.get("model_path"),
            )
            for v in versions
        ]
    return ModelsResponse(tasks=tasks_out)
