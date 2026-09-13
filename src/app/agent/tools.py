from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import Order
from app.models.ticket import SupportTicket


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
