from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


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
    requested_at: datetime
    sla_deadline: datetime
    decided_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
