"""RefreshTokenRepository implementation backed by SQLAlchemy/PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from library.core.entities import RefreshTokenRecord
from library.models.refresh_token import RefreshToken
from library.utils.clock import utcnow


class SqlAlchemyRefreshTokenRepository:
    """Persists refresh-token hashes and supports rotation/revocation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self, staff_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> None:
        self._session.add(
            RefreshToken(
                staff_id=staff_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )

    async def get_by_hash(self, token_hash: str) -> RefreshTokenRecord | None:
        row = await self._session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if row is None:
            return None
        return RefreshTokenRecord(
            id=row.id,
            staff_id=row.staff_id,
            token_hash=row.token_hash,
            expires_at=row.expires_at,
            revoked_at=row.revoked_at,
        )

    async def revoke(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )

    async def revoke_all_for_staff(self, staff_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.staff_id == staff_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
