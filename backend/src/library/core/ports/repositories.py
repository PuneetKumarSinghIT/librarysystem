"""Repository ports — persistence abstractions the service layer depends on.

Each repository is small and aggregate-focused (Interface Segregation). Adapters in
`library.adapter.db.repositories` implement these against PostgreSQL; tests use fakes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from library.core.entities import RefreshTokenRecord, Staff


class StaffRepository(Protocol):
    async def get_by_email(self, email: str) -> Staff | None: ...

    async def get_by_id(self, staff_id: uuid.UUID) -> Staff | None: ...

    async def touch_last_login(self, staff_id: uuid.UUID) -> None: ...


class RefreshTokenRepository(Protocol):
    async def add(
        self, staff_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> None: ...

    async def get_by_hash(self, token_hash: str) -> RefreshTokenRecord | None: ...

    async def revoke(self, token_hash: str) -> None: ...

    async def revoke_all_for_staff(self, staff_id: uuid.UUID) -> None: ...
