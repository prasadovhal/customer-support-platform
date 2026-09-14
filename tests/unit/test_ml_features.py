from __future__ import annotations

import pandas as pd

from app.ml.features import extract_text, extract_texts, texts_from_messages


def test_extract_text_combines_subject_and_message() -> None:
    row = pd.Series({"subject": "Order Issue", "message": "My order is late."})
    result = extract_text(row)
    assert "order issue" in result
    assert "my order is late" in result


def test_extract_text_lowercase() -> None:
    row = pd.Series({"subject": "URGENT", "message": "Call Me"})
    assert extract_text(row) == "urgent call me"


def test_extract_text_handles_none_subject() -> None:
    row = pd.Series({"subject": None, "message": "Just a message."})
    result = extract_text(row)
    assert result == "just a message."


def test_extract_text_handles_missing_subject() -> None:
    row = pd.Series({"message": "Hello world"})
    result = extract_text(row)
    assert result == "hello world"


def test_extract_texts_returns_list() -> None:
    df = pd.DataFrame(
        [
            {"subject": "Refund", "message": "I need a refund."},
            {"subject": None, "message": "Order tracking?"},
        ]
    )
    texts = extract_texts(df)
    assert len(texts) == 2
    assert "refund" in texts[0]
    assert "order tracking" in texts[1]


def test_texts_from_messages_normalises() -> None:
    messages = ["Hello World", "  URGENT  "]
    result = texts_from_messages(messages)
    assert result == ["hello world", "urgent"]
