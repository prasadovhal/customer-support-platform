from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.workflow import run_agent
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.db.session import get_db
from app.models.conversation import Conversation, ConversationMessage
from app.models.idempotency import IdempotencyKey
from app.schemas.auth import TokenPayload
from app.schemas.message import MessageCreate, MessageResponse
from app.security.dependencies import get_current_token

router = APIRouter(tags=["messages"])


async def _load_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 10,
) -> list[dict[str, str]]:
    """Load recent messages as role/content dicts for LLM context."""
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    # Reverse to chronological order and strip system messages
    return [
        {"role": m.role, "content": m.content}
        for m in reversed(rows)
        if m.role in ("customer", "assistant")
    ]


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
    """Submit a message to a conversation and receive an AI agent reply.

    - Idempotency-Key header prevents duplicate submissions.
    - Calls the LangGraph support agent (classify → retrieve → generate).
    - Persists metadata: intent, retrieved doc IDs, groundedness, latency.
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

    # 4. Persist the customer message.
    customer_msg = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="customer",
        content=body.message,
    )
    db.add(customer_msg)
    await db.flush()

    # 5. Load conversation history for LLM context.
    history = await _load_history(db, conversation_id)

    # 6. Run the agent workflow.
    customer_id = str(conv.customer_id) if conv.customer_id else None
    try:
        agent_result = await run_agent(
            message=body.message,
            conversation_id=str(conversation_id),
            customer_id=customer_id,
            db=db,
            history=history,
        )
    except Exception as exc:
        logger.error(f"Agent failed for conversation {conversation_id}: {exc}")
        from app.agent.workflow import _FALLBACK_RESPONSE
        from app.agent.schemas import AgentResult
        agent_result = AgentResult(response=_FALLBACK_RESPONSE)

    # 7. Persist the assistant reply with all metadata.
    assistant_msg = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content=agent_result.response,
        intent=agent_result.intent,
        intent_confidence=agent_result.intent_confidence,
        retrieved_doc_ids=agent_result.retrieved_doc_ids or None,
        tool_calls=agent_result.tool_calls or None,
        groundedness_score=agent_result.groundedness_score,
        latency_ms=agent_result.latency_ms,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    # 8. Mark idempotency key as completed.
    if idempotency_key:
        idem_record.status = "completed"
        idem_record.result_ref = str(assistant_msg.id)
        idem_record.completed_at = datetime.now(timezone.utc)

    return MessageResponse(
        id=assistant_msg.id,
        conversation_id=assistant_msg.conversation_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        intent=assistant_msg.intent,
        sources=[],
        created_at=assistant_msg.created_at,
    )
