from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    channel: str  # api, web, mobile


class ConversationResponse(BaseModel):
    id: uuid.UUID
    customer_id: Optional[uuid.UUID]
    channel: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
