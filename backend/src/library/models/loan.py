"""Loan ORM model — a borrow/return event linking a copy, a member, and staff.

The DB enforces "a copy can only be on loan once at a time" via a partial unique index
on (copy_id) WHERE returned_at IS NULL — see the migration. This makes double-borrow
impossible even under concurrency.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from library.adapter.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from library.core.enums import LoanStatus


class Loan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A borrow/return event. Open loans (returned_at IS NULL) are unique per copy."""

    __tablename__ = "loans"

    copy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("book_copies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    staff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        str_enum(LoanStatus), nullable=False, default=LoanStatus.ACTIVE, index=True
    )
    renewed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # A copy can have at most ONE open (not-yet-returned) loan. Enforced by the DB.
        Index(
            "uq_active_loan_per_copy",
            "copy_id",
            unique=True,
            postgresql_where=text("returned_at IS NULL"),
        ),
        # Fast "what does this member currently have out?" lookups.
        Index(
            "ix_active_loans_by_member",
            "member_id",
            postgresql_where=text("returned_at IS NULL"),
        ),
    )
