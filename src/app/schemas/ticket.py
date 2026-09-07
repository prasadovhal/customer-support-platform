from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TicketCreate(BaseModel):
    category: str
    priority: str  # P0, P1, P2, P3
    description: str
    conversation_id: Optional[uuid.UUID] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_agent_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    ticket_number: str
    customer_id: uuid.UUID
    category: str
    priority: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
