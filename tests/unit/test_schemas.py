from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.approval import ApprovalDecision
from app.schemas.auth import TokenPayload
from app.schemas.message import MessageCreate


# ---------------------------------------------------------------------------
# MessageCreate
# ---------------------------------------------------------------------------
class TestMessageCreate:
    def test_valid_message(self) -> None:
        msg = MessageCreate(message="Hello, I need help.")
        assert msg.message == "Hello, I need help."

    def test_empty_message_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(message="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)

    def test_whitespace_only_message_is_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            MessageCreate(message="   ")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)

    def test_optional_order_id_defaults_to_none(self) -> None:
        msg = MessageCreate(message="Where is my order?")
        assert msg.order_id is None
        assert msg.product_id is None


# ---------------------------------------------------------------------------
# ApprovalDecision
# ---------------------------------------------------------------------------
class TestApprovalDecision:
    def test_approved_decision(self) -> None:
        decision = ApprovalDecision(decision="approved", reason="Within policy limits.")
        assert decision.decision == "approved"

    def test_denied_decision(self) -> None:
        decision = ApprovalDecision(decision="denied", reason="Exceeds threshold.")
        assert decision.decision == "denied"

    def test_invalid_decision_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApprovalDecision(decision="maybe", reason="Not sure.")

    def test_missing_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ApprovalDecision(decision="approved")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TokenPayload
# ---------------------------------------------------------------------------
class TestTokenPayload:
    def test_basic_payload(self) -> None:
        payload = TokenPayload(
            sub="abc-123",
            type="customer",
            scopes=["customer:read"],
            session_id="sess-1",
            iat=1700000000,
            exp=1700000900,
            iss="customer-support-api",
        )
        assert payload.sub == "abc-123"
        assert payload.type == "customer"
        assert "customer:read" in payload.scopes
        assert payload.exp == 1700000900

    def test_optional_fields_default_to_none(self) -> None:
        payload = TokenPayload(sub="xyz", type="agent")
        assert payload.session_id is None
        assert payload.iat is None
        assert payload.exp is None
        assert payload.iss is None

    def test_scopes_default_to_empty_list(self) -> None:
        payload = TokenPayload(sub="xyz", type="agent")
        assert payload.scopes == []
