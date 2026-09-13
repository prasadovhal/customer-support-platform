from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ApprovalCreate(BaseModel):
    action: str = Field(
        ...,
        description="Action to approve: issue_refund | cancel_order | email_change | address_change",
    )
    conversation_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = "USD"
    idempotency_key: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=500)

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"issue_refund", "cancel_order", "email_change", "address_change"}
        if v not in allowed:
            raise ValueError(f"action must be one of {sorted(allowed)}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "denied"]
    reason: str

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        if v not in ("approved", "denied"):
            raise ValueError("decision must be 'approved' or 'denied'")
        return v


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    action: str
    status: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    policy_outcome: Optional[str] = None  # auto_approve | approval_required | denied
    policy_id: Optional[str] = None
    reason: Optional[str] = None
    requested_at: datetime
    sla_deadline: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_reason: Optional[str] = None

    model_config = {"from_attributes": True}
