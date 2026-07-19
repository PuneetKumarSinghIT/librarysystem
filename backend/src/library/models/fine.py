"""Fine ORM model — a charge assessed against a member for an overdue/lost loan."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from library.adapter.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from library.core.enums import FineStatus


class Fine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Monetary charge linked to a loan. Amount stored as exact NUMERIC, never float."""

    __tablename__ = "fines"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[FineStatus] = mapped_column(
        str_enum(FineStatus), nullable=False, default=FineStatus.PENDING, index=True
    )
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
