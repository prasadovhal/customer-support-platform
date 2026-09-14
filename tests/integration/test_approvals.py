"""Integration tests for /approvals endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.conftest import _agent_token, _customer_token

pytestmark = pytest.mark.asyncio


class TestCreateApproval:
    async def test_small_refund_is_auto_approved(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        """Refund below the standard segment threshold should auto-approve."""
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "25.00",
                "currency": "USD",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["policy_outcome"] == "auto_approve"
        assert body["status"] == "approved"

    async def test_large_refund_requires_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        """Refund above the standard segment threshold should require human approval."""
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "200.00",
                "currency": "USD",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["policy_outcome"] == "approval_required"
        assert body["status"] == "pending_approval"
        assert body["sla_deadline"] is not None

    async def test_idempotency_key_prevents_duplicate_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))
        key = str(uuid.uuid4())

        payload = {
            "action": "issue_refund",
            "conversation_id": str(conv.id),
            "amount": "10.00",
            "currency": "USD",
            "idempotency_key": key,
        }
        r1 = await async_client.post(
            "/api/v1/approvals",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        r2 = await async_client.post(
            "/api/v1/approvals",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 201
        assert r2.status_code == 409

    async def test_invalid_action_returns_422(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer()
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        resp = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "teleport_customer",
                "conversation_id": str(conv.id),
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_unauthenticated_create_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(uuid.uuid4()),
                "idempotency_key": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 401


class TestGetApproval:
    async def test_customer_gets_own_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        create = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "10.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        approval_id = create.json()["id"]

        resp = await async_client.get(
            f"/api/v1/approvals/{approval_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == approval_id

    async def test_get_nonexistent_approval_returns_404(
        self, async_client: AsyncClient, make_customer
    ):
        token = _agent_token()
        resp = await async_client.get(
            f"/api/v1/approvals/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestDecideApproval:
    async def test_agent_approves_pending_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        customer_token = _customer_token(str(customer.id))
        agent_tok = _agent_token()

        # Create a pending approval (large refund)
        create = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "500.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        assert create.json()["status"] == "pending_approval"
        approval_id = create.json()["id"]

        resp = await async_client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "approved", "reason": "Verified — valid refund claim."},
            headers={"Authorization": f"Bearer {agent_tok}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "approved"
        assert body["decided_by"] is not None

    async def test_agent_denies_pending_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        customer_token = _customer_token(str(customer.id))
        agent_tok = _agent_token()

        create = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "500.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        approval_id = create.json()["id"]

        resp = await async_client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "denied", "reason": "Policy not met."},
            headers={"Authorization": f"Bearer {agent_tok}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "denied"

    async def test_customer_cannot_decide_approval(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        token = _customer_token(str(customer.id))

        create = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "500.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        approval_id = create.json()["id"]

        resp = await async_client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "approved", "reason": "self-approve"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_decide_already_decided_approval_returns_422(
        self, async_client: AsyncClient, make_customer, make_conversation
    ):
        customer = await make_customer(segment="standard")
        conv = await make_conversation(customer.id)
        customer_token = _customer_token(str(customer.id))
        agent_tok = _agent_token()

        create = await async_client.post(
            "/api/v1/approvals",
            json={
                "action": "issue_refund",
                "conversation_id": str(conv.id),
                "amount": "500.00",
                "idempotency_key": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        approval_id = create.json()["id"]

        # First decision
        await async_client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "approved", "reason": "ok"},
            headers={"Authorization": f"Bearer {agent_tok}"},
        )
        # Second decision on already-decided approval
        resp = await async_client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "denied", "reason": "changed mind"},
            headers={"Authorization": f"Bearer {agent_tok}"},
        )
        assert resp.status_code == 422
