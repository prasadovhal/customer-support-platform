from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.session import get_db
from app.models.conversation import Conversation
from app.schemas.auth import TokenPayload
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.security.dependencies import get_current_token, get_optional_customer

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    token: Optional[TokenPayload] = Depends(get_optional_customer),
) -> ConversationResponse:
    """Create a new conversation. Auth is optional.

    If a customer token is provided, the conversation is bound to that customer.
    Unauthenticated sessions are allowed (e.g., pre-login chat widget).
    """
    customer_id: Optional[uuid.UUID] = None
    if token is not None:
        customer_id = uuid.UUID(token.sub)
    elif body.customer_id is not None:
        # Only accept explicit customer_id from the body when there is no token.
        customer_id = body.customer_id

    conv = Conversation(
        id=uuid.uuid4(),
        customer_id=customer_id,
        channel=body.channel,
        status="active",
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(get_current_token),
) -> ConversationResponse:
    """Retrieve a conversation by ID.

    - Customers can only access their own conversations.
    - Agents can access any conversation.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise NotFoundError(message=f"Conversation {conversation_id} not found.")

    if token.type == "customer":
        if conv.customer_id is None or str(conv.customer_id) != token.sub:
            raise AuthorizationError(
                message="You do not have access to this conversation."
            )
    elif token.type != "agent":
        raise AuthorizationError(message="Unsupported token type.")

    return ConversationResponse.model_validate(conv)
