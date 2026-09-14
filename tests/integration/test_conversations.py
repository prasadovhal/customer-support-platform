"""Integration tests for /conversations endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import _customer_token

pytestmark = pytest.mark.asyncio


class TestCreateConversation:
    async def test_create_anonymous_conversation(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/conversations", json={"channel": "api"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["channel"] == "api"
        assert body["status"] == "active"
        assert body["customer_id"] is None

    async def test_create_authenticated_conversation(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            "/api/v1/conversations",
            json={"channel": "web"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["customer_id"] == str(customer.id)
        assert body["channel"] == "web"

    async def test_create_conversation_invalid_channel_returns_422(
        self, async_client: AsyncClient
    ):
        # channel is a free-form string; the schema accepts anything,
        # but an empty value is rejected by Pydantic min-length if enforced.
        # Here we just verify a missing required field fails.
        resp = await async_client.post("/api/v1/conversations", json={})
        assert resp.status_code == 422


class TestGetConversation:
    async def test_customer_can_get_own_conversation(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        resp = await async_client.get(
            f"/api/v1/conversations/{conv.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(conv.id)

    async def test_customer_cannot_get_other_customers_conversation(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        owner = await make_customer()
        other = await make_customer()
        conv = await make_conversation(owner.id)
        token = _customer_token(str(other.id))

        resp = await async_client.get(
            f"/api/v1/conversations/{conv.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_get_nonexistent_conversation_returns_404(
        self, async_client: AsyncClient, make_customer
    ):
        import uuid

        customer = await make_customer()
        token = _customer_token(str(customer.id))

        resp = await async_client.get(
            f"/api/v1/conversations/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_unauthenticated_request_returns_401(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)

        resp = await async_client.get(f"/api/v1/conversations/{conv.id}")
        assert resp.status_code == 401
