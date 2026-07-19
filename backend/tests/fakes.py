"""In-memory fake adapters implementing the core ports.

These let us unit-test services with zero I/O — the whole point of depending on ports
(Dependency Inversion). They are Liskov-substitutable for the real Postgres/argon2 adapters.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from library.core.commands import BookCreate
from library.core.entities import Book, BookCopy, RefreshTokenRecord, Staff
from library.core.enums import CopyCondition, CopyStatus
from library.core.errors import AlreadyExistsError
from library.utils.clock import utcnow


class FakeStaffRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, Staff] = {}
        self._by_email: dict[str, Staff] = {}
        self.touched: list[uuid.UUID] = []

    def add(self, staff: Staff) -> None:
        self._by_id[staff.id] = staff
        self._by_email[staff.email.lower().strip()] = staff

    async def get_by_email(self, email: str) -> Staff | None:
        return self._by_email.get(email.lower().strip())

    async def get_by_id(self, staff_id: uuid.UUID) -> Staff | None:
        return self._by_id.get(staff_id)

    async def touch_last_login(self, staff_id: uuid.UUID) -> None:
        self.touched.append(staff_id)


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._records: dict[str, RefreshTokenRecord] = {}

    async def add(
        self, staff_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> None:
        self._records[token_hash] = RefreshTokenRecord(
            id=uuid.uuid4(),
            staff_id=staff_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def get_by_hash(self, token_hash: str) -> RefreshTokenRecord | None:
        return self._records.get(token_hash)

    async def revoke(self, token_hash: str) -> None:
        record = self._records.get(token_hash)
        if record and record.revoked_at is None:
            record.revoked_at = utcnow()

    async def revoke_all_for_staff(self, staff_id: uuid.UUID) -> None:
        for record in self._records.values():
            if record.staff_id == staff_id and record.revoked_at is None:
                record.revoked_at = utcnow()

    # Test helpers
    def active_count(self) -> int:
        return sum(1 for r in self._records.values() if r.revoked_at is None)


class FakePasswordHasher:
    """Deterministic, fast stand-in for argon2 (unit tests only)."""

    def hash(self, plain: str) -> str:
        return f"hashed::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed::{plain}"


class FakeBookRepository:
    """In-memory BookRepository. Enforces ISBN/barcode uniqueness like the real DB."""

    def __init__(self) -> None:
        self.books: dict[uuid.UUID, Book] = {}
        self.copies: dict[uuid.UUID, list[BookCopy]] = {}

    def _isbn_taken(self, isbn: str, exclude: uuid.UUID | None = None) -> bool:
        return any(b.isbn == isbn and b.id != exclude for b in self.books.values())

    async def create(self, data: BookCreate) -> Book:
        if data.isbn and self._isbn_taken(data.isbn):
            raise AlreadyExistsError("A book with this ISBN already exists")
        book = Book(
            id=uuid.uuid4(),
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            publisher=data.publisher,
            published_year=data.published_year,
            category=data.category,
            description=data.description,
        )
        self.books[book.id] = book
        return book

    async def update(self, book_id, changes):
        book = self.books.get(book_id)
        if book is None:
            return None
        if changes.get("isbn") and self._isbn_taken(changes["isbn"], exclude=book_id):
            raise AlreadyExistsError("A book with this ISBN already exists")
        for key, value in changes.items():
            setattr(book, key, value)
        return book

    async def get(self, book_id):
        return self.books.get(book_id)

    async def list(self, search, limit, offset):
        items = list(self.books.values())
        if search:
            term = search.lower()
            items = [
                b for b in items if term in b.title.lower() or term in b.author.lower()
            ]
        items.sort(key=lambda b: b.title)
        return items[offset : offset + limit], len(items)

    async def book_exists(self, book_id) -> bool:
        return book_id in self.books

    async def add_copy(self, book_id, barcode, condition) -> BookCopy:
        if any(c.barcode == barcode for cl in self.copies.values() for c in cl):
            raise AlreadyExistsError("A copy with this barcode already exists")
        copy = BookCopy(
            id=uuid.uuid4(),
            book_id=book_id,
            barcode=barcode,
            condition=condition or CopyCondition.GOOD,
            status=CopyStatus.AVAILABLE,
        )
        self.copies.setdefault(book_id, []).append(copy)
        return copy

    async def list_copies(self, book_id) -> list[BookCopy]:
        return list(self.copies.get(book_id, []))
