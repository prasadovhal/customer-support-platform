"""Integration tests for /tickets endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.conftest import _agent_token, _customer_token

pytestmark = pytest.mark.asyncio


class TestCreateTicket:
    async def test_customer_creates_ticket(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            "/api/v1/tickets",
            json={
                "category": "billing",
                "priority": "P2",
                "description": "I was charged twice for my order.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["customer_id"] == str(customer.id)
        assert body["category"] == "billing"
        assert body["priority"] == "P2"
        assert body["status"] == "open"
        assert body["ticket_number"].startswith("TK-")

    async def test_ticket_number_is_unique(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))

        resp1 = await async_client.post(
            "/api/v1/tickets",
            json={"category": "shipping", "priority": "P3", "description": "Late."},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp2 = await async_client.post(
            "/api/v1/tickets",
            json={"category": "returns", "priority": "P2", "description": "Broken."},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.json()["ticket_number"] != resp2.json()["ticket_number"]

    async def test_unauthenticated_create_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/tickets",
            json={"category": "billing", "priority": "P2", "description": "Help."},
        )
        assert resp.status_code == 401

    async def test_idempotency_key_prevents_duplicate_ticket(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))
        key = str(uuid.uuid4())

        r1 = await async_client.post(
            "/api/v1/tickets",
            json={"category": "billing", "priority": "P1", "description": "Urgent."},
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
        )
        r2 = await async_client.post(
            "/api/v1/tickets",
            json={"category": "billing", "priority": "P1", "description": "Urgent."},
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
        )
        assert r1.status_code == 201
        assert r2.status_code == 409


class TestGetTicket:
    async def test_customer_gets_own_ticket(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))

        create = await async_client.post(
            "/api/v1/tickets",
            json={"category": "returns", "priority": "P2", "description": "Return."},
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket_id = create.json()["id"]

        resp = await async_client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == ticket_id

    async def test_get_nonexistent_ticket_returns_404(
        self, async_client: AsyncClient, make_customer
    ):
        token = _customer_token(str(uuid.uuid4()))
        resp = await async_client.get(
            f"/api/v1/tickets/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestUpdateTicket:
    async def test_agent_updates_ticket_status(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        customer_token = _customer_token(str(customer.id))
        agent_tok = _agent_token()

        create = await async_client.post(
            "/api/v1/tickets",
            json={"category": "billing", "priority": "P2", "description": "Issue."},
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        ticket_id = create.json()["id"]

        resp = await async_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {agent_tok}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"
