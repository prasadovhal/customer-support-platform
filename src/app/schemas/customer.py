from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CustomerResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    customer_segment: Optional[str]
    account_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
