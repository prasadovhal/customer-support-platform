from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_number: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )  # TK-XXXXX format
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )  # P0, P1, P2, P3
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'open'"), index=True
    )  # open, in_progress, resolved, closed
    escalation_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_queue: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    ml_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ml_priority: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ml_model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    context_ref: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # reference to conversation/approval context
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="tickets"
    )
    conversation: Mapped[Optional["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="tickets"
    )
