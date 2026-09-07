from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError
from app.db.base import get_async_session_factory

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
async def health() -> dict[str, Any]:
    """Liveness probe — returns 200 if the process is running."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/ready", response_model=dict)
async def ready() -> dict[str, Any]:
    """Readiness probe — checks DB and Redis connectivity.

    Returns 200 when all dependencies are reachable, 503 otherwise.
    """
    settings = get_settings()
    errors: list[str] = []

    # Check database
    try:
        session_factory = get_async_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        errors.append(f"database: {exc}")

    # Check Redis
    try:
        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await client.ping()
        await client.aclose()
    except Exception as exc:
        errors.append(f"redis: {exc}")

    if errors:
        raise ServiceUnavailableError(
            message="One or more dependencies are unavailable.",
            detail=errors,
        )

    return {
        "status": "ready",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
