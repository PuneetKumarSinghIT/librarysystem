"""Repository ports — persistence abstractions the service layer depends on.

Each repository is small and aggregate-focused (Interface Segregation). Adapters in
`library.adapter.db.repositories` implement these against PostgreSQL; tests use fakes.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Protocol

from library.core.commands import BookCreate
from library.core.entities import Book, BookCopy, RefreshTokenRecord, Staff
from library.core.enums import CopyCondition


class StaffRepository(Protocol):
    async def get_by_email(self, email: str) -> Staff | None: ...

    async def get_by_id(self, staff_id: uuid.UUID) -> Staff | None: ...

    async def touch_last_login(self, staff_id: uuid.UUID) -> None: ...


class BookRepository(Protocol):
    async def create(self, data: BookCreate) -> Book: ...

    async def update(self, book_id: uuid.UUID, changes: Mapping[str, Any]) -> Book | None: ...

    async def get(self, book_id: uuid.UUID) -> Book | None: ...

    async def list(
        self, search: str | None, limit: int, offset: int
    ) -> tuple[list[Book], int]: ...

    async def book_exists(self, book_id: uuid.UUID) -> bool: ...

    async def add_copy(
        self, book_id: uuid.UUID, barcode: str, condition: CopyCondition
    ) -> BookCopy: ...

    async def list_copies(self, book_id: uuid.UUID) -> list[BookCopy]: ...


class RefreshTokenRepository(Protocol):
    async def add(
        self, staff_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> None: ...

    async def get_by_hash(self, token_hash: str) -> RefreshTokenRecord | None: ...

    async def revoke(self, token_hash: str) -> None: ...

    async def revoke_all_for_staff(self, staff_id: uuid.UUID) -> None: ...
