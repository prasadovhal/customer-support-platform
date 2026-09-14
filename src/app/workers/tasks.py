"""Celery task definitions for the customer support platform.

Tasks are discovered automatically via celery_app.conf include=["app.workers.tasks"].
"""
from __future__ import annotations

from typing import Any

from loguru import logger

from app.workers.celery_app import celery_app


@celery_app.task(
    name="app.workers.tasks.process_order_event",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_order_event(self, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Process an inbound order lifecycle webhook event.

    Receives the raw payload from the webhook endpoint, validates the event
    type, and dispatches to the appropriate handler.

    Retries up to 3 times with a 30-second delay on transient failures.
    """
    event_type: str = payload.get("event_type", "unknown")
    order_id: str = payload.get("order_id", "")

    logger.info(
        "Processing order event",
        event_id=event_id,
        event_type=event_type,
        order_id=order_id,
    )

    try:
        _dispatch_order_event(event_type, order_id, payload)
        logger.info("Order event processed", event_id=event_id, event_type=event_type)
        return {"status": "processed", "event_id": event_id}
    except Exception as exc:
        logger.warning(f"Order event processing failed, retrying: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.expire_stale_approvals",
    bind=True,
)
def expire_stale_approvals(self) -> dict[str, Any]:
    """Mark pending approvals that have passed their SLA deadline as 'timeout'.

    Intended to run on a schedule (e.g., every 15 minutes via Celery Beat).
    Uses a synchronous SQLAlchemy session since Celery workers are sync.
    """
    import asyncio
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.db.base import get_engine
    from app.models.approval import ApprovalAuditLog, ApprovalRequest

    async def _run() -> int:
        from sqlalchemy.ext.asyncio import AsyncSession

        engine = get_engine()
        async with AsyncSession(engine) as session:
            async with session.begin():
                now = datetime.now(timezone.utc)
                result = await session.execute(
                    select(ApprovalRequest).where(
                        ApprovalRequest.status == "pending_approval",
                        ApprovalRequest.sla_deadline < now,
                    )
                )
                expired = result.scalars().all()
                for approval in expired:
                    approval.status = "timeout"
                    session.add(
                        ApprovalAuditLog(
                            approval_id=approval.id,
                            event="timeout",
                            actor_id="system",
                            actor_role="system",
                            reason="SLA deadline exceeded",
                            policy_version=approval.policy_version,
                        )
                    )
                return len(expired)

    count = asyncio.run(_run())
    logger.info(f"Expired {count} stale approval(s)")
    return {"expired_count": count}


def _dispatch_order_event(
    event_type: str, order_id: str, payload: dict[str, Any]
) -> None:
    """Route an order event to the appropriate handler."""
    handlers = {
        "order.shipped": _on_order_shipped,
        "order.delivered": _on_order_delivered,
        "order.cancelled": _on_order_cancelled,
        "order.refunded": _on_order_refunded,
    }
    handler = handlers.get(event_type)
    if handler:
        handler(order_id, payload)
    else:
        logger.debug(f"No handler for order event type '{event_type}' — skipping")


def _on_order_shipped(order_id: str, payload: dict[str, Any]) -> None:
    logger.info(
        "Order shipped", order_id=order_id, tracking=payload.get("tracking_number")
    )


def _on_order_delivered(order_id: str, payload: dict[str, Any]) -> None:
    logger.info("Order delivered", order_id=order_id)


def _on_order_cancelled(order_id: str, payload: dict[str, Any]) -> None:
    logger.info(
        "Order cancelled", order_id=order_id, reason=payload.get("cancellation_reason")
    )


def _on_order_refunded(order_id: str, payload: dict[str, Any]) -> None:
    logger.info(
        "Order refunded", order_id=order_id, amount=payload.get("refund_amount")
    )
