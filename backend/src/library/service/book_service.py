"""Book/copy use-cases: create, update, get, list (search + pagination), manage copies.

Business rules and validation live here. Depends only on the BookRepository port (DIP).
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from library.core.commands import BookCreate
from library.core.entities import Book, BookCopy
from library.core.enums import CopyCondition
from library.core.errors import NotFoundError, ValidationError
from library.core.ports.repositories import BookRepository
from library.utils.clock import utcnow
from library.utils.pagination import clamp_page

_MIN_YEAR = 1400
_UPDATABLE_FIELDS = {
    "title",
    "author",
    "isbn",
    "publisher",
    "published_year",
    "category",
    "description",
}


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    async def create_book(self, data: BookCreate) -> Book:
        """Validate and persist a new title. Raises ValidationError / AlreadyExistsError."""
        title = _require_text(data.title, "title")
        author = _require_text(data.author, "author")
        _validate_year(data.published_year)
        isbn = _normalize_isbn(data.isbn)
        return await self._repo.create(
            BookCreate(
                title=title,
                author=author,
                isbn=isbn,
                publisher=_clean(data.publisher),
                published_year=data.published_year,
                category=_clean(data.category),
                description=_clean(data.description),
            )
        )

    async def update_book(self, book_id: uuid.UUID, changes: Mapping[str, Any]) -> Book:
        """Partial update. Only known fields are applied; unknown keys are rejected."""
        unknown = set(changes) - _UPDATABLE_FIELDS
        if unknown:
            raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")

        cleaned: dict[str, Any] = dict(changes)
        if "title" in cleaned:
            cleaned["title"] = _require_text(cleaned["title"], "title")
        if "author" in cleaned:
            cleaned["author"] = _require_text(cleaned["author"], "author")
        if "published_year" in cleaned:
            _validate_year(cleaned["published_year"])
        if "isbn" in cleaned:
            cleaned["isbn"] = _normalize_isbn(cleaned["isbn"])

        book = await self._repo.update(book_id, cleaned)
        if book is None:
            raise NotFoundError("Book not found")
        return book

    async def get_book(self, book_id: uuid.UUID) -> Book:
        book = await self._repo.get(book_id)
        if book is None:
            raise NotFoundError("Book not found")
        return book

    async def list_books(
        self, search: str | None, limit: int | None, offset: int | None
    ) -> tuple[list[Book], int]:
        clamped_limit, clamped_offset = clamp_page(limit, offset)
        term = search.strip() if search else None
        return await self._repo.list(term or None, clamped_limit, clamped_offset)

    async def add_copy(
        self, book_id: uuid.UUID, barcode: str, condition: CopyCondition | None
    ) -> BookCopy:
        """Add a physical copy to an existing book. Raises NotFound / AlreadyExists."""
        code = _require_text(barcode, "barcode")
        if not await self._repo.book_exists(book_id):
            raise NotFoundError("Book not found")
        return await self._repo.add_copy(book_id, code, condition or CopyCondition.GOOD)

    async def list_copies(self, book_id: uuid.UUID) -> list[BookCopy]:
        if not await self._repo.book_exists(book_id):
            raise NotFoundError("Book not found")
        return await self._repo.list_copies(book_id)


# ── validation helpers ───────────────────────────────────────────────────────
def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _require_text(value: str | None, field: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise ValidationError(f"{field} is required")
    return cleaned


def _validate_year(year: int | None) -> None:
    if year is None:
        return
    if year < _MIN_YEAR or year > utcnow().year + 1:
        raise ValidationError(f"published_year must be between {_MIN_YEAR} and next year")


def _normalize_isbn(isbn: str | None) -> str | None:
    cleaned = _clean(isbn)
    if cleaned is None:
        return None
    digits = cleaned.replace("-", "").replace(" ", "")
    if len(digits) not in (10, 13) or not digits[:-1].isdigit():
        raise ValidationError("isbn must be a valid ISBN-10 or ISBN-13")
    return digits
