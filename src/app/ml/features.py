from __future__ import annotations

import pandas as pd


# Canonical category values from the training data
CATEGORIES = [
    "account", "orders", "payments", "products", "refunds",
    "returns", "security", "shipping", "technical", "warranty",
]

PRIORITIES = ["P0", "P1", "P2", "P3"]

SENTIMENTS = ["angry", "negative", "neutral", "positive"]

TEAMS = [
    "account_support", "billing_support", "orders_support",
    "returns_support", "security_support", "shipping_support",
    "technical_support",
]

FEATURE_VERSION = "1.0.0"


def extract_text(row: pd.Series) -> str:
    """Combine subject and message into a single lowercased string."""
    subject = str(row.get("subject", "") or "")
    message = str(row.get("message", "") or "")
    return f"{subject} {message}".strip().lower()


def extract_texts(df: pd.DataFrame) -> list[str]:
    """Vectorised text extraction for a DataFrame."""
    subjects = df.get("subject", pd.Series([""] * len(df), index=df.index)).fillna("")
    messages = df.get("message", pd.Series([""] * len(df), index=df.index)).fillna("")
    return (subjects + " " + messages).str.strip().str.lower().tolist()


def texts_from_messages(messages: list[str]) -> list[str]:
    """Normalise a plain list of message strings (no subject)."""
    return [m.strip().lower() for m in messages]
