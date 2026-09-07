from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: str
    total_amount: Decimal
    currency: str
    items: list[OrderItemResponse] = []
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
