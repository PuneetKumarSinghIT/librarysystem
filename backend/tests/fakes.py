"""In-memory fake adapters implementing the core ports.

These let us unit-test services with zero I/O — the whole point of depending on ports
(Dependency Inversion). They are Liskov-substitutable for the real Postgres/argon2 adapters.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from library.core.entities import RefreshTokenRecord, Staff
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
