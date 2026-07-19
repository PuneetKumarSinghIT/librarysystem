"""Book (title-level) ORM model. Physical copies live in book_copies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from library.adapter.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from library.models.book_copy import BookCopy


class Book(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A catalog title. One book has many physical copies (book_copies)."""

    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    publisher: Mapped[str | None] = mapped_column(String(300), nullable=True)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    copies: Mapped[list[BookCopy]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
