"""StaffRepository implementation backed by SQLAlchemy/PostgreSQL."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from library.core.entities import Staff
from library.models.staff import StaffUser
from library.utils.clock import utcnow


def _to_entity(row: StaffUser) -> Staff:
    return Staff(
        id=row.id,
        email=row.email,
        role=row.role,
        is_active=row.is_active,
        password_hash=row.password_hash,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyStaffRepository:
    """Reads/writes staff users. Returns framework-free `Staff` entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Staff | None:
        row = await self._session.scalar(
            select(StaffUser).where(StaffUser.email == email.lower().strip())
        )
        return _to_entity(row) if row else None

    async def get_by_id(self, staff_id: uuid.UUID) -> Staff | None:
        row = await self._session.get(StaffUser, staff_id)
        return _to_entity(row) if row else None

    async def touch_last_login(self, staff_id: uuid.UUID) -> None:
        await self._session.execute(
            update(StaffUser)
            .where(StaffUser.id == staff_id)
            .values(last_login_at=utcnow())
        )
