from __future__ import annotations

from typing import Callable, Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.schemas.auth import TokenPayload
from app.security.jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_current_token(
    token: Optional[str] = Depends(oauth2_scheme),
) -> TokenPayload:
    """Extract and validate the Bearer token from the Authorization header.

    Raises:
        AuthenticationError: If no token is provided or the token is invalid.
    """
    if not token:
        raise AuthenticationError(message="Missing authentication token.")
    return decode_token(token)


def get_current_customer(
    payload: TokenPayload = Depends(get_current_token),
) -> TokenPayload:
    """Require a token whose type is 'customer'.

    Raises:
        AuthorizationError: If the token is not a customer token.
    """
    if payload.type != "customer":
        raise AuthorizationError(message="This endpoint requires a customer token.")
    return payload


def get_current_agent(
    payload: TokenPayload = Depends(get_current_token),
) -> TokenPayload:
    """Require a token whose type is 'agent'.

    Raises:
        AuthorizationError: If the token is not an agent token.
    """
    if payload.type != "agent":
        raise AuthorizationError(message="This endpoint requires an agent token.")
    return payload


def require_scope(scope: str) -> Callable[..., TokenPayload]:
    """Return a FastAPI dependency that verifies the token has the given scope.

    Usage::

        @router.post("/approve")
        async def approve(token=Depends(require_scope("approve:refunds"))):
            ...
    """

    def _check(payload: TokenPayload = Depends(get_current_token)) -> TokenPayload:
        if scope not in payload.scopes:
            raise AuthorizationError(message=f"Missing required scope: '{scope}'.")
        return payload

    return _check


def get_optional_customer(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[TokenPayload]:
    """Return the decoded customer payload, or None if no token is present.

    Use this for endpoints that accept both authenticated and anonymous requests.
    An invalid token still raises AuthenticationError so callers cannot pass
    garbage and silently fall through as unauthenticated.
    """
    if not token:
        return None
    payload = decode_token(token)
    if payload.type != "customer":
        raise AuthorizationError(message="This endpoint requires a customer token.")
    return payload
