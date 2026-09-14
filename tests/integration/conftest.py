"""Integration test fixtures — creates real DB rows and valid JWTs."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.customer import Customer
from app.security.jwt import create_access_token
from app.security.password import hash_password


# ── Customer factory ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def make_customer(db_session: AsyncSession):
    """Return a coroutine that inserts a Customer row and yields the ORM object."""
    created: list[Customer] = []

    async def _factory(
        email: str | None = None,
        password: str = "Test1234!",
        segment: str = "standard",
        status: str = "active",
    ) -> Customer:
        customer = Customer(
            id=uuid.uuid4(),
            email=email or f"user-{uuid.uuid4().hex[:8]}@test.com",
            name="Test User",
            hashed_password=hash_password(password),
            customer_segment=segment,
            account_status=status,
        )
        db_session.add(customer)
        await db_session.flush()
        await db_session.refresh(customer)
        created.append(customer)
        return customer

    return _factory


# ── Token helpers ─────────────────────────────────────────────────────────────

def _customer_token(customer_id: str) -> str:
    return create_access_token(
        subject=customer_id,
        token_type="customer",
        scopes=["customer:read", "customer:write"],
        expire_minutes=60,
    )


def _agent_token(
    agent_id: str | None = None,
    scopes: list[str] | None = None,
) -> str:
    return create_access_token(
        subject=agent_id or str(uuid.uuid4()),
        token_type="agent",
        scopes=scopes or [
            "approve:refunds",
            "approve:cancellations",
            "approve:account_changes",
        ],
        expire_minutes=60,
    )


# ── Conversation factory ──────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def make_conversation(db_session: AsyncSession):
    async def _factory(customer_id: uuid.UUID, channel: str = "api") -> Conversation:
        conv = Conversation(
            id=uuid.uuid4(),
            customer_id=customer_id,
            channel=channel,
            status="active",
        )
        db_session.add(conv)
        await db_session.flush()
        await db_session.refresh(conv)
        return conv

    return _factory
