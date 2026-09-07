from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1)
    order_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank or whitespace only")
        return v


class SourceAttribution(BaseModel):
    doc_id: uuid.UUID
    title: str
    version: str
    relevance_score: float


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    intent: Optional[str] = None
    sources: list[SourceAttribution] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
