from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.db.session import get_db
from app.models.conversation import Conversation, ConversationMessage
from app.models.idempotency import IdempotencyKey
from app.schemas.auth import TokenPayload
from app.schemas.message import MessageCreate, MessageResponse
from app.security.dependencies import get_current_token

router = APIRouter(tags=["messages"])

_AGENT_STUB_RESPONSE = (
    "Thank you for your message. Agent processing is not yet implemented. "
    "A support representative will follow up shortly."
)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
async def post_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> MessageResponse:
    """Submit a message to a conversation and receive an agent reply stub.

    - Reads the Idempotency-Key header to prevent duplicate submissions.
    - Writes both the customer message and the assistant stub to the DB.
    - Returns the assistant MessageResponse.
    """
    # 1. Verify conversation exists.
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError(message=f"Conversation {conversation_id} not found.")

    # 2. Scope check: customers can only write to their own conversations.
    if token.type == "customer":
        if conv.customer_id is None or str(conv.customer_id) != token.sub:
            raise AuthorizationError(
                message="You do not have access to this conversation."
            )
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    # 3. Idempotency check.
    if idempotency_key:
        existing = await db.execute(
            select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
        )
        idem_row = existing.scalar_one_or_none()
        if idem_row is not None:
            if idem_row.status == "completed" and idem_row.result_ref:
                # Return the previously created assistant message.
                msg_result = await db.execute(
                    select(ConversationMessage).where(
                        ConversationMessage.id == uuid.UUID(idem_row.result_ref)
                    )
                )
                cached_msg = msg_result.scalar_one_or_none()
                if cached_msg:
                    return MessageResponse(
                        id=cached_msg.id,
                        conversation_id=cached_msg.conversation_id,
                        role=cached_msg.role,
                        content=cached_msg.content,
                        intent=cached_msg.intent,
                        sources=[],
                        created_at=cached_msg.created_at,
                    )
            # Still processing or result missing — treat as conflict.
            raise ConflictError(
                message="A request with this Idempotency-Key is already being processed."
            )

        # Record the key as processing before we do any work.
        idem_record = IdempotencyKey(
            id=uuid.uuid4(),
            key=idempotency_key,
            status="processing",
        )
        db.add(idem_record)
        await db.flush()

    # 4. Persist the customer message.
    customer_msg = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="customer",
        content=body.message,
    )
    db.add(customer_msg)

    # 5. Produce the stub assistant reply.
    assistant_msg = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content=_AGENT_STUB_RESPONSE,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    # 6. Mark idempotency key as completed.
    if idempotency_key:
        idem_record.status = "completed"
        idem_record.result_ref = str(assistant_msg.id)
        idem_record.completed_at = datetime.now(timezone.utc)

    return MessageResponse(
        id=assistant_msg.id,
        conversation_id=assistant_msg.conversation_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        intent=None,
        sources=[],
        created_at=assistant_msg.created_at,
    )
