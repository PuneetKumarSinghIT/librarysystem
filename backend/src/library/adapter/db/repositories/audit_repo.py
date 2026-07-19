"""AuditRepository implementation — appends immutable audit-trail rows."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from library.models.audit import AuditLog


class SqlAlchemyAuditRepository:
    """Writes accountability records (who did what) to the audit_log table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        actor_staff_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        metadata: dict | None = None,
    ) -> None:
        self._session.add(
            AuditLog(
                actor_staff_id=actor_staff_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata_json=metadata,
            )
        )
        await self._session.flush()
