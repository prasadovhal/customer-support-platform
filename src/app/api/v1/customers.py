from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import TokenPayload
from app.schemas.customer import CustomerResponse
from app.security.dependencies import get_current_token

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> CustomerResponse:
    """Retrieve a customer profile.

    - Customers can only retrieve their own profile.
    - Agents can retrieve any customer profile.
    """
    if token.type == "customer":
        # Double enforcement: scope check + DB-level filter by token.sub.
        if str(customer_id) != token.sub:
            raise AuthorizationError(
                message="You do not have permission to view this profile."
            )
        result = await db.execute(
            select(Customer).where(
                Customer.id == customer_id,
                Customer.id == uuid.UUID(token.sub),  # DB-level enforcement
            )
        )
    elif token.type == "agent":
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
    else:
        raise AuthorizationError(message="Unsupported token type.")

    customer = result.scalar_one_or_none()
    if customer is None:
        raise NotFoundError(message=f"Customer {customer_id} not found.")

    return CustomerResponse.model_validate(customer)
