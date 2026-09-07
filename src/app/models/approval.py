from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ApprovalRequest(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    action: Mapped[str] = mapped_column(
        String, nullable=False
    )  # issue_refund, cancel_order, email_change, address_change, etc.
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'pending_approval'"), index=True
    )  # action_requested, policy_check, approval_required, pending_approval, approved, denied, timeout, executed
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, server_default=text("'USD'")
    )
    change_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_value_hash: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # hashed new value for account changes
    policy_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    eligibility_basis: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    sla_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    decided_by: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # agent_id
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="approval_requests"
    )
    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        "Conversation", back_populates="approval_requests"
    )
    order: Mapped[Optional["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="approval_requests"
    )
    audit_logs: Mapped[list["ApprovalAuditLog"]] = relationship(
        "ApprovalAuditLog",
        back_populates="approval",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="ApprovalAuditLog.created_at",
    )


class ApprovalAuditLog(Base):
    __tablename__ = "approval_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(
        String, nullable=False
    )  # requested, approved, denied, timeout, executed
    actor_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    approval: Mapped["ApprovalRequest"] = relationship(
        "ApprovalRequest", back_populates="audit_logs"
    )


class VerificationRequest(Base, TimestampMixin):
    __tablename__ = "verification_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    change_type: Mapped[str] = mapped_column(String, nullable=False)
    requested_value_hash: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)  # email, sms
    code_hash: Mapped[str] = mapped_column(
        String, nullable=False
    )  # bcrypt hash of the 6-digit code
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'pending'")
    )  # pending, verified, expired, failed
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("3")
    )
    code_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="verification_requests"
    )
    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        "Conversation", back_populates="verification_requests"
    )
