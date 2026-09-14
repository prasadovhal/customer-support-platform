from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.db.session import get_db
from app.models.idempotency import IdempotencyKey
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _validate_hmac_signature(body: bytes, signature: str) -> None:
    """Validate HMAC-SHA256 signature from the X-Signature header.

    Uses hmac.compare_digest to prevent timing attacks.

    Raises:
        AuthenticationError: If WEBHOOK_SECRET is not configured or the
                             signature does not match.
    """
    settings = get_settings()
    if not settings.WEBHOOK_SECRET:
        raise AuthenticationError(
            message="Webhook secret is not configured on the server."
        )

    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Normalise — some senders prefix with "sha256="
    incoming = signature.removeprefix("sha256=")

    if not hmac.compare_digest(expected, incoming):
        raise AuthenticationError(message="Invalid webhook signature.")


@router.post("/orders", status_code=200)
async def receive_order_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str = Header(alias="X-Signature"),
) -> dict[str, str]:
    """Receive an order lifecycle event from the upstream system.

    Processing steps:
    1. Read raw body and validate HMAC-SHA256 signature.
    2. Parse payload and extract event_id for idempotency.
    3. If event_id is new: record in idempotency_keys and enqueue Celery task.
    4. Return 200 immediately — processing is asynchronous.
    """
    raw_body = await request.body()
    await _validate_hmac_signature(raw_body, x_signature)

    payload: dict[str, Any] = await request.json()
    event_id: str = payload.get("event_id") or str(uuid.uuid4())

    # Idempotency check.
    existing = await db.execute(
        select(IdempotencyKey).where(IdempotencyKey.key == event_id)
    )
    if existing.scalar_one_or_none() is not None:
        # Already seen — acknowledge without re-processing.
        return {"status": "already_processed", "event_id": event_id}

    # Record the event before enqueuing so we never process twice.
    idem = IdempotencyKey(
        id=uuid.uuid4(),
        key=event_id,
        status="processing",
    )
    db.add(idem)
    await db.flush()

    # Enqueue the background task (fire-and-forget from the HTTP perspective).
    celery_app.send_task(
        "app.workers.tasks.process_order_event",
        kwargs={"event_id": event_id, "payload": payload},
    )

    return {"status": "accepted", "event_id": event_id}
