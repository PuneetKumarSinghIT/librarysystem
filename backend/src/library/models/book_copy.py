"""Physical copy of a book. Lending happens against a copy, not a title."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from library.adapter.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from library.core.enums import CopyCondition, CopyStatus

if TYPE_CHECKING:
    from library.models.book import Book


class BookCopy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single physical copy of a book. Loans are made against a copy, not a title."""

    __tablename__ = "book_copies"

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    barcode: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    condition: Mapped[CopyCondition] = mapped_column(
        str_enum(CopyCondition), nullable=False, default=CopyCondition.GOOD
    )
    status: Mapped[CopyStatus] = mapped_column(
        str_enum(CopyStatus), nullable=False, default=CopyStatus.AVAILABLE, index=True
    )
    acquired_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    book: Mapped[Book] = relationship(back_populates="copies")
