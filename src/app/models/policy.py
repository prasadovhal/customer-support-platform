from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint("type", "key", "version", name="uq_policy_type_key_version"),
        Index(
            "ix_policy_type_key_effective",
            "type",
            "key",
            "effective_from",
            "effective_to",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # cancellation_threshold, return_window, high_risk_categories, etc.
    key: Mapped[str] = mapped_column(
        String, nullable=False
    )  # specific key within type
    value: Mapped[Any] = mapped_column(
        JSONB, nullable=False
    )  # the policy value (numeric, list, etc.)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    effective_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_by: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    audit_logs: Mapped[list["PolicyAuditLog"]] = relationship(
        "PolicyAuditLog",
        back_populates="policy",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="PolicyAuditLog.created_at",
    )


class PolicyAuditLog(Base):
    __tablename__ = "policy_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(
        String, nullable=False
    )  # created, updated, deactivated
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    old_value: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="audit_logs")
