from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import TokenPayload

_ISSUER = "customer-support-api"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    token_type: str,
    scopes: list[str],
    expire_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The token subject (customer_id or agent_id as string).
        token_type: "customer" or "agent".
        scopes: List of scope strings granted to this token.
        expire_minutes: Override default expiry; uses settings value if None.

    Returns:
        Signed JWT string.
    """
    settings = get_settings()
    if expire_minutes is None:
        expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    now = _now_utc()
    expire = now + timedelta(minutes=expire_minutes)
    session_id = str(uuid.uuid4())

    payload: dict = {
        "sub": subject,
        "type": token_type,
        "scopes": scopes,
        "session_id": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": _ISSUER,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, token_type: str) -> str:
    """Create a signed JWT refresh token with a longer expiry and no scopes.

    Args:
        subject: The token subject.
        token_type: "customer" or "agent".

    Returns:
        Signed JWT string.
    """
    settings = get_settings()
    now = _now_utc()
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    session_id = str(uuid.uuid4())

    payload: dict = {
        "sub": subject,
        "type": token_type,
        "scopes": [],
        "token_class": "refresh",
        "session_id": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": _ISSUER,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Parsed TokenPayload.

    Raises:
        AuthenticationError: If the token is invalid, expired, or malformed.
    """
    settings = get_settings()
    try:
        raw = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(message="Token has expired.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(message=f"Invalid token: {exc}")

    return TokenPayload(
        sub=raw["sub"],
        type=raw.get("type", ""),
        scopes=raw.get("scopes", []),
        session_id=raw.get("session_id"),
        iat=raw.get("iat"),
        exp=raw.get("exp"),
        iss=raw.get("iss"),
    )
