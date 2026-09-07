from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.session import get_db
from app.models.order import Order
from app.schemas.auth import TokenPayload
from app.schemas.order import OrderItemResponse, OrderResponse
from app.security.dependencies import get_current_token

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> OrderResponse:
    """Retrieve an order.

    - Customers can only retrieve their own orders (double enforcement).
    - Agents can retrieve any order.
    """
    if token.type == "customer":
        # DB-level WHERE customer_id = token.sub as well as the order ID.
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.id == order_id,
                Order.customer_id == uuid.UUID(token.sub),
            )
        )
    elif token.type == "agent":
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
    else:
        raise AuthorizationError(message="Unsupported token type.")

    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError(message=f"Order {order_id} not found.")

    items = [
        OrderItemResponse(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        )
        for item in order.items
    ]

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        currency=order.currency,
        items=items,
        tracking_number=order.tracking_number,
        carrier=order.carrier,
        estimated_delivery=order.delivered_at,
        created_at=order.created_at,
    )
