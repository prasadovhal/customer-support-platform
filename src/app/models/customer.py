from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, server_default=text("'US'")
    )
    customer_segment: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # standard, premium, enterprise
    account_status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'active'")
    )  # active, suspended, closed
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="customer", lazy="select"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="customer", lazy="select"
    )
    tickets: Mapped[list["SupportTicket"]] = relationship(  # noqa: F821
        "SupportTicket", back_populates="customer", lazy="select"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(  # noqa: F821
        "ApprovalRequest", back_populates="customer", lazy="select"
    )
    verification_requests: Mapped[list["VerificationRequest"]] = relationship(  # noqa: F821
        "VerificationRequest", back_populates="customer", lazy="select"
    )
