from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str
    password: str
    grant_type: str = Field(default="password")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # subject (customer_id or agent_id)
    type: str  # "customer" | "agent"
    scopes: list[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None
    iss: Optional[str] = None
