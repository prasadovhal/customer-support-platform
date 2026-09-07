from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.db.session import get_db
from app.models.idempotency import IdempotencyKey
from app.models.ticket import SupportTicket
from app.schemas.auth import TokenPayload
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.security.dependencies import get_current_agent, get_current_token

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _generate_ticket_number() -> str:
    """Generate a TK-XXXXX style ticket number."""
    import random
    import string
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TK-{suffix}"


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> TicketResponse:
    """Create a new support ticket.

    Customers create tickets on their own behalf. Agents may also create tickets.
    Idempotency-Key is honoured to prevent duplicates.
    """
    # Determine customer_id based on token type.
    if token.type == "customer":
        customer_id = uuid.UUID(token.sub)
    elif token.type == "agent":
        # Agents must supply customer_id via conversation_id resolution — for now
        # require a conversation_id from which we infer it, or reject if missing.
        raise AuthorizationError(
            message="Agents must create tickets on behalf of a customer via a conversation."
        )
    else:
        raise AuthorizationError(message="Unsupported token type.")

    # Idempotency check.
    if idempotency_key:
        existing = await db.execute(
            select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
        )
        idem_row = existing.scalar_one_or_none()
        if idem_row is not None:
            if idem_row.status == "completed" and idem_row.result_ref:
                ticket_result = await db.execute(
                    select(SupportTicket).where(
                        SupportTicket.id == uuid.UUID(idem_row.result_ref)
                    )
                )
                cached = ticket_result.scalar_one_or_none()
                if cached:
                    return TicketResponse.model_validate(cached)
            raise ConflictError(
                message="A request with this Idempotency-Key is already being processed."
            )

        idem_record = IdempotencyKey(
            id=uuid.uuid4(),
            key=idempotency_key,
            status="processing",
        )
        db.add(idem_record)
        await db.flush()

    ticket = SupportTicket(
        id=uuid.uuid4(),
        ticket_number=_generate_ticket_number(),
        customer_id=customer_id,
        conversation_id=body.conversation_id,
        category=body.category,
        priority=body.priority,
        status="open",
        idempotency_key=idempotency_key,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    if idempotency_key:
        idem_record.status = "completed"
        idem_record.result_ref = str(ticket.id)
        idem_record.completed_at = datetime.now(timezone.utc)

    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> TicketResponse:
    """Retrieve a ticket.

    - Customers can only retrieve their own tickets.
    - Agents can retrieve any ticket.
    """
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise NotFoundError(message=f"Ticket {ticket_id} not found.")

    if token.type == "customer":
        if str(ticket.customer_id) != token.sub:
            raise AuthorizationError(
                message="You do not have access to this ticket."
            )
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    body: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_agent),
) -> TicketResponse:
    """Update a ticket's status or assignment. Agent only."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise NotFoundError(message=f"Ticket {ticket_id} not found.")

    if body.status is not None:
        ticket.status = body.status
        if body.status == "resolved" and ticket.resolved_at is None:
            ticket.resolved_at = datetime.now(timezone.utc)
    if body.assigned_agent_id is not None:
        ticket.assigned_agent_id = body.assigned_agent_id

    await db.flush()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)
