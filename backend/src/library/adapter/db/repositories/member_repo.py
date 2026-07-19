"""MemberRepository implementation backed by SQLAlchemy/PostgreSQL."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from library.core.commands import MemberCreate
from library.core.entities import Member
from library.core.errors import AlreadyExistsError
from library.models.member import Member as MemberModel
from library.utils.clock import utcnow


def _to_entity(row: MemberModel) -> Member:
    return Member(
        id=row.id,
        first_name=row.first_name,
        last_name=row.last_name,
        email=row.email,
        status=row.status,
        phone=row.phone,
        address=row.address,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: MemberCreate) -> Member:
        row = MemberModel(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
        self._session.add(row)
        await self._flush_unique()
        return _to_entity(row)

    async def update(self, member_id: uuid.UUID, changes: Mapping[str, Any]) -> Member | None:
        row = await self._get_active(member_id)
        if row is None:
            return None
        for key, value in changes.items():
            setattr(row, key, value)
        await self._flush_unique()
        return _to_entity(row)

    async def get(self, member_id: uuid.UUID) -> Member | None:
        row = await self._get_active(member_id)
        return _to_entity(row) if row else None

    async def list(
        self, search: str | None, limit: int, offset: int
    ) -> tuple[list[Member], int]:
        filters = [MemberModel.deleted_at.is_(None)]
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    MemberModel.first_name.ilike(pattern),
                    MemberModel.last_name.ilike(pattern),
                    MemberModel.email.ilike(pattern),
                )
            )

        total = await self._session.scalar(
            select(func.count()).select_from(MemberModel).where(*filters)
        )
        rows = await self._session.scalars(
            select(MemberModel)
            .where(*filters)
            .order_by(MemberModel.last_name, MemberModel.first_name)
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(r) for r in rows], int(total or 0)

    async def soft_delete(self, member_id: uuid.UUID) -> bool:
        row = await self._get_active(member_id)
        if row is None:
            return False
        row.deleted_at = utcnow()
        await self._session.flush()
        return True

    # ── helpers ──
    async def _get_active(self, member_id: uuid.UUID) -> MemberModel | None:
        row = await self._session.get(MemberModel, member_id)
        if row is None or row.deleted_at is not None:
            return None
        return row

    async def _flush_unique(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AlreadyExistsError("A member with this email already exists") from exc
