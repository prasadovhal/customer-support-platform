from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import ApprovalAuditLog, ApprovalRequest
from app.models.conversation import ConversationWorkflowState
from app.models.customer import Customer
from app.models.order import Order
from app.models.ticket import SupportTicket
from app.policy.engine import PolicyContext, PolicyEngine

_policy_engine = PolicyEngine()


async def get_customer(customer_id: str, db: AsyncSession) -> Optional[dict[str, Any]]:
    """Fetch customer profile for a given UUID string."""
    result = await db.execute(
        select(Customer).where(Customer.id == uuid.UUID(customer_id))
    )
    customer = result.scalar_one_or_none()
    if customer is None:
        return None
    return {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email,
        "customer_segment": customer.customer_segment,
        "account_status": customer.account_status,
    }


async def get_order(order_id: str, db: AsyncSession) -> Optional[dict[str, Any]]:
    """Fetch order details for a given UUID string."""
    result = await db.execute(
        select(Order).where(Order.id == uuid.UUID(order_id))
    )
    order = result.scalar_one_or_none()
    if order is None:
        return None
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": str(order.total_amount),
        "currency": order.currency,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
    }


async def request_approval(
    action: str,
    conversation_id: str,
    customer_id: str,
    db: AsyncSession,
    order_id: Optional[str] = None,
    amount: Optional[float] = None,
    currency: str = "USD",
    summary: Optional[str] = None,
) -> dict[str, Any]:
    """Evaluate policy and create an ApprovalRequest if warranted.

    Returns a dict with keys: outcome, approval_id, status, reason.
    outcome is one of: auto_approve | approval_required | denied
    """
    # Load order context for policy evaluation
    order_status: Optional[str] = None
    order_age_days: Optional[int] = None
    if order_id:
        order_result = await db.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        )
        order = order_result.scalar_one_or_none()
        if order:
            order_status = order.status
            if order.created_at:
                order_age_days = (
                    datetime.now(timezone.utc) - order.created_at.replace(tzinfo=timezone.utc)
                ).days

    # Load customer segment
    cust_result = await db.execute(
        select(Customer.customer_segment).where(Customer.id == uuid.UUID(customer_id))
    )
    customer_segment: str = cust_result.scalar_one_or_none() or "standard"

    ctx = PolicyContext(
        action=action,
        amount=Decimal(str(amount)) if amount is not None else None,
        currency=currency,
        order_status=order_status,
        customer_segment=customer_segment,
        order_age_days=order_age_days,
    )
    decision = _policy_engine.evaluate(ctx)

    if decision.outcome == "denied":
        return {
            "outcome": "denied",
            "approval_id": None,
            "status": "denied",
            "reason": decision.reason,
        }

    # Create approval record
    from app.core.config import get_settings
    from datetime import timedelta
    sla_deadline = datetime.now(timezone.utc) + timedelta(
        hours=get_settings().APPROVAL_SLA_HOURS
    )
    approval_status = "approved" if decision.outcome == "auto_approve" else "pending_approval"
    now = datetime.now(timezone.utc)

    approval = ApprovalRequest(
        id=uuid.uuid4(),
        action=action,
        status=approval_status,
        customer_id=uuid.UUID(customer_id),
        conversation_id=uuid.UUID(conversation_id),
        order_id=uuid.UUID(order_id) if order_id else None,
        amount=Decimal(str(amount)) if amount is not None else None,
        currency=currency,
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        eligibility_basis=decision.eligibility_basis,
        requested_at=now,
        sla_deadline=sla_deadline,
        idempotency_key=str(uuid.uuid4()),
        decided_by="agent_ai" if decision.outcome == "auto_approve" else None,
        decided_at=now if decision.outcome == "auto_approve" else None,
        decision_reason=decision.reason if decision.outcome == "auto_approve" else None,
    )
    db.add(approval)

    db.add(ApprovalAuditLog(
        id=uuid.uuid4(),
        approval_id=approval.id,
        event="requested" if decision.outcome == "approval_required" else "auto_approved",
        actor_id="agent_ai",
        actor_role="assistant",
        reason=decision.reason,
        policy_version=decision.policy_version,
    ))

    # Update workflow state if pending
    if decision.outcome == "approval_required":
        wf_result = await db.execute(
            select(ConversationWorkflowState).where(
                ConversationWorkflowState.conversation_id == uuid.UUID(conversation_id)
            )
        )
        wf = wf_result.scalar_one_or_none()
        if wf:
            wf.state = "awaiting_approval"
            wf.pending_approval_id = approval.id
        else:
            db.add(ConversationWorkflowState(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                state="awaiting_approval",
                pending_approval_id=approval.id,
            ))

    await db.flush()

    return {
        "outcome": decision.outcome,
        "approval_id": str(approval.id),
        "status": approval_status,
        "reason": decision.reason,
    }


async def create_ticket(
    customer_id: str,
    conversation_id: str,
    category: str,
    priority: str,
    summary: str,
    db: AsyncSession,
) -> dict[str, str]:
    """Create a support ticket and return its number and status."""
    ticket_number = "TK-" + uuid.uuid4().hex[:5].upper()
    ticket = SupportTicket(
        id=uuid.uuid4(),
        ticket_number=ticket_number,
        customer_id=uuid.UUID(customer_id),
        conversation_id=uuid.UUID(conversation_id),
        category=category,
        priority=priority,
        status="open",
        escalation_reason=summary[:500] if summary else None,
    )
    db.add(ticket)
    await db.flush()
    return {"ticket_number": ticket_number, "status": "open"}
