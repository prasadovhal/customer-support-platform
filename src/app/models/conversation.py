from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String, nullable=False)  # api, web, mobile
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'active'"), index=True
    )  # active, escalated, resolved, closed
    escalation_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship(  # noqa: F821
        "Customer", back_populates="conversations"
    )
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )
    workflow_state: Mapped[Optional["ConversationWorkflowState"]] = relationship(
        "ConversationWorkflowState",
        back_populates="conversation",
        uselist=False,
        lazy="select",
        cascade="all, delete-orphan",
    )
    tickets: Mapped[list["SupportTicket"]] = relationship(  # noqa: F821
        "SupportTicket", back_populates="conversation", lazy="select"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(  # noqa: F821
        "ApprovalRequest", back_populates="conversation", lazy="select"
    )
    verification_requests: Mapped[list["VerificationRequest"]] = relationship(  # noqa: F821
        "VerificationRequest", back_populates="conversation", lazy="select"
    )


class ConversationMessage(Base):
    """Conversation messages are immutable once written — no updated_at."""

    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String, nullable=False
    )  # customer, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    intent_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrieved_doc_ids: Mapped[Optional[list[Any]]] = mapped_column(
        JSONB, nullable=True
    )  # list of doc IDs used
    tool_calls: Mapped[Optional[list[Any]]] = mapped_column(
        JSONB, nullable=True
    )  # list of tool call records
    prompt_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    groundedness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


class ConversationWorkflowState(Base):
    """Tracks the multi-step workflow state for a conversation."""

    __tablename__ = "conversation_workflow_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    workflow_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'idle'")
    )
    pending_approval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    pending_verification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    context_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="workflow_state"
    )
