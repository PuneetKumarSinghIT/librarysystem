"""BookRepository implementation backed by SQLAlchemy/PostgreSQL."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from library.core.commands import BookCreate
from library.core.entities import Book, BookCopy
from library.core.enums import CopyCondition, CopyStatus
from library.core.errors import AlreadyExistsError
from library.models.book import Book as BookModel
from library.models.book_copy import BookCopy as BookCopyModel

# Count of copies per book and how many are available — reused by get/list.
_AVAILABLE = CopyStatus.AVAILABLE


def _to_copy(row: BookCopyModel) -> BookCopy:
    return BookCopy(
        id=row.id,
        book_id=row.book_id,
        barcode=row.barcode,
        condition=row.condition,
        status=row.status,
        created_at=row.created_at,
    )


def _to_book(row: BookModel, total: int = 0, available: int = 0) -> Book:
    return Book(
        id=row.id,
        title=row.title,
        author=row.author,
        isbn=row.isbn,
        publisher=row.publisher,
        published_year=row.published_year,
        category=row.category,
        description=row.description,
        total_copies=total,
        available_copies=available,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: BookCreate) -> Book:
        row = BookModel(
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            publisher=data.publisher,
            published_year=data.published_year,
            category=data.category,
            description=data.description,
        )
        self._session.add(row)
        await self._flush_unique("A book with this ISBN already exists")
        return _to_book(row)

    async def update(self, book_id: uuid.UUID, changes: Mapping[str, Any]) -> Book | None:
        row = await self._session.get(BookModel, book_id)
        if row is None or row.deleted_at is not None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._flush_unique("A book with this ISBN already exists")
        total, available = await self._counts(book_id)
        return _to_book(row, total, available)

    async def get(self, book_id: uuid.UUID) -> Book | None:
        row = await self._session.get(BookModel, book_id)
        if row is None or row.deleted_at is not None:
            return None
        total, available = await self._counts(book_id)
        return _to_book(row, total, available)

    async def list(
        self, search: str | None, limit: int, offset: int
    ) -> tuple[list[Book], int]:
        # Per-book copy counts computed once via a grouped subquery (avoids N+1).
        counts = (
            select(
                BookCopyModel.book_id.label("book_id"),
                func.count().label("total"),
                func.count().filter(BookCopyModel.status == _AVAILABLE).label("available"),
            )
            .group_by(BookCopyModel.book_id)
            .subquery()
        )

        filters = [BookModel.deleted_at.is_(None)]
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(BookModel.title.ilike(pattern), BookModel.author.ilike(pattern))
            )

        total_rows = await self._session.scalar(
            select(func.count()).select_from(BookModel).where(*filters)
        )

        rows = await self._session.execute(
            select(
                BookModel,
                func.coalesce(counts.c.total, 0),
                func.coalesce(counts.c.available, 0),
            )
            .outerjoin(counts, counts.c.book_id == BookModel.id)
            .where(*filters)
            .order_by(BookModel.title)
            .limit(limit)
            .offset(offset)
        )
        books = [_to_book(b, t, a) for b, t, a in rows.all()]
        return books, int(total_rows or 0)

    async def book_exists(self, book_id: uuid.UUID) -> bool:
        found = await self._session.scalar(
            select(func.count())
            .select_from(BookModel)
            .where(BookModel.id == book_id, BookModel.deleted_at.is_(None))
        )
        return bool(found)

    async def add_copy(
        self, book_id: uuid.UUID, barcode: str, condition: CopyCondition
    ) -> BookCopy:
        row = BookCopyModel(
            book_id=book_id,
            barcode=barcode,
            condition=condition,
            status=CopyStatus.AVAILABLE,
        )
        self._session.add(row)
        await self._flush_unique("A copy with this barcode already exists")
        return _to_copy(row)

    async def list_copies(self, book_id: uuid.UUID) -> list[BookCopy]:
        rows = await self._session.scalars(
            select(BookCopyModel)
            .where(BookCopyModel.book_id == book_id)
            .order_by(BookCopyModel.barcode)
        )
        return [_to_copy(r) for r in rows]

    # ── helpers ──
    async def _counts(self, book_id: uuid.UUID) -> tuple[int, int]:
        row = await self._session.execute(
            select(
                func.count(),
                func.count().filter(BookCopyModel.status == _AVAILABLE),
            ).where(BookCopyModel.book_id == book_id)
        )
        total, available = row.one()
        return int(total), int(available)

    async def _flush_unique(self, conflict_message: str) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AlreadyExistsError(conflict_message) from exc
