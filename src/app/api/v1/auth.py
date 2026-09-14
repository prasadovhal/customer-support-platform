from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.db.session import get_db
from app.models.customer import Customer
from app.schemas.auth import RefreshRequest, TokenRequest, TokenResponse
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(
    form: TokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Password grant — authenticate with username (email) and password.

    Returns access and refresh tokens on success.
    """
    result = await db.execute(select(Customer).where(Customer.email == form.username))
    customer = result.scalar_one_or_none()

    if customer is None or not verify_password(form.password, customer.hashed_password):
        raise AuthenticationError(message="Invalid email or password.")

    if customer.account_status != "active":
        raise AuthenticationError(
            message=f"Account is {customer.account_status}. Please contact support."
        )

    settings = get_settings()
    subject = str(customer.id)

    access_token = create_access_token(
        subject=subject,
        token_type="customer",
        scopes=["customer:read", "customer:write"],
        expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh_token = create_refresh_token(subject=subject, token_type="customer")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh grant — exchange a valid refresh token for new tokens."""
    payload = decode_token(body.refresh_token)

    # Make sure the referenced subject still exists and is active.
    import uuid as _uuid

    result = await db.execute(
        select(Customer).where(Customer.id == _uuid.UUID(payload.sub))
    )
    customer = result.scalar_one_or_none()

    if customer is None:
        raise AuthenticationError(message="Token subject no longer exists.")

    if customer.account_status != "active":
        raise AuthenticationError(message=f"Account is {customer.account_status}.")

    settings = get_settings()
    subject = str(customer.id)

    access_token = create_access_token(
        subject=subject,
        token_type=payload.type,
        scopes=["customer:read", "customer:write"],
        expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    new_refresh = create_refresh_token(subject=subject, token_type=payload.type)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
