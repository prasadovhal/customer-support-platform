from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.features import CATEGORIES, PRIORITIES, SENTIMENTS, TEAMS

ModelType = Literal["logistic_regression", "random_forest", "gradient_boosting"]

ALL_MODEL_TYPES: list[ModelType] = [
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
]


@dataclass
class TaskConfig:
    name: str
    label_column: str
    class_names: list[str]
    # For imbalanced tasks (priority, escalation) use balanced weights
    use_class_weight: bool = False
    description: str = ""


TASK_CONFIGS: dict[str, TaskConfig] = {
    "category": TaskConfig(
        name="category",
        label_column="category",
        class_names=CATEGORIES,
        description="Classify ticket into one of 10 support categories",
    ),
    "priority": TaskConfig(
        name="priority",
        label_column="priority",
        class_names=PRIORITIES,
        use_class_weight=True,
        description="Predict ticket priority P0–P3 (P0 is most urgent)",
    ),
    "sentiment": TaskConfig(
        name="sentiment",
        label_column="sentiment",
        class_names=SENTIMENTS,
        use_class_weight=True,
        description="Classify customer sentiment from ticket message",
    ),
    "escalation": TaskConfig(
        name="escalation",
        label_column="escalated",
        class_names=["false", "true"],
        use_class_weight=True,
        description="Predict whether the ticket will require escalation",
    ),
    "routing": TaskConfig(
        name="routing",
        label_column="assigned_team",
        class_names=TEAMS,
        description="Route ticket to the appropriate support team",
    ),
}

ALL_TASK_NAMES = list(TASK_CONFIGS.keys())


def _tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=10_000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        strip_accents="unicode",
        analyzer="word",
    )


def build_pipeline(model_type: ModelType, use_class_weight: bool = False) -> Pipeline:
    """Return a complete TF-IDF + classifier sklearn Pipeline."""
    weight = "balanced" if use_class_weight else None

    if model_type == "logistic_regression":
        clf = LogisticRegression(
            max_iter=1000,
            class_weight=weight,
            C=1.0,
            solver="lbfgs",
            random_state=42,
        )
    elif model_type == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=200,
            class_weight=weight,
            max_depth=None,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
    elif model_type == "gradient_boosting":
        # GradientBoostingClassifier doesn't support class_weight;
        # imbalance is handled via sampling in the trainer.
        clf = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    return Pipeline([("tfidf", _tfidf()), ("clf", clf)])
