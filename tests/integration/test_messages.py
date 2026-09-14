"""Integration tests for POST /conversations/{id}/messages."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.agent.schemas import AgentResult
from tests.integration.conftest import _agent_token, _customer_token

pytestmark = pytest.mark.asyncio

# Stable mock result returned by all run_agent patches in this module
_MOCK_RESULT = AgentResult(
    response="Here is the answer to your question.",
    intent="order_status",
    intent_confidence=0.92,
    sources=[],
    retrieved_doc_ids=[],
    tool_calls=[],
    groundedness_score=0.85,
    latency_ms=120,
)


class TestPostMessage:
    async def test_customer_posts_message_and_gets_reply(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        with patch(
            "app.api.v1.messages.run_agent", new=AsyncMock(return_value=_MOCK_RESULT)
        ):
            resp = await async_client.post(
                f"/api/v1/conversations/{conv.id}/messages",
                json={"message": "Where is my order?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["role"] == "assistant"
        assert body["content"] == _MOCK_RESULT.response
        assert body["intent"] == "order_status"
        assert body["conversation_id"] == str(conv.id)

    async def test_agent_token_can_post_to_any_conversation(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _agent_token()

        with patch(
            "app.api.v1.messages.run_agent", new=AsyncMock(return_value=_MOCK_RESULT)
        ):
            resp = await async_client.post(
                f"/api/v1/conversations/{conv.id}/messages",
                json={"message": "Checking on behalf of customer"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 201

    async def test_customer_cannot_post_to_another_customers_conversation(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        owner = await make_customer()
        intruder = await make_customer()
        conv = await make_conversation(owner.id)
        token = _customer_token(str(intruder.id))

        with patch(
            "app.api.v1.messages.run_agent", new=AsyncMock(return_value=_MOCK_RESULT)
        ):
            resp = await async_client.post(
                f"/api/v1/conversations/{conv.id}/messages",
                json={"message": "snoop"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 403

    async def test_post_to_nonexistent_conversation_returns_404(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer()
        token = _customer_token(str(customer.id))

        with patch(
            "app.api.v1.messages.run_agent", new=AsyncMock(return_value=_MOCK_RESULT)
        ):
            resp = await async_client.post(
                f"/api/v1/conversations/{uuid.uuid4()}/messages",
                json={"message": "hello"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404

    async def test_blank_message_returns_422(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            f"/api/v1/conversations/{conv.id}/messages",
            json={"message": "   "},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_idempotency_key_prevents_duplicate(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))
        key = str(uuid.uuid4())

        with patch(
            "app.api.v1.messages.run_agent", new=AsyncMock(return_value=_MOCK_RESULT)
        ):
            r1 = await async_client.post(
                f"/api/v1/conversations/{conv.id}/messages",
                json={"message": "Hello"},
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            )
            r2 = await async_client.post(
                f"/api/v1/conversations/{conv.id}/messages",
                json={"message": "Hello"},
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
            )

        assert r1.status_code == 201
        assert r2.status_code == 409
