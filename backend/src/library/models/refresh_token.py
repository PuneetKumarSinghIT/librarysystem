"""Refresh-token ORM model — stores only a HASH of each token, never the token itself.

Enables refresh-token rotation, revocation, and reuse detection (F3 auth).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from library.adapter.db.base import Base, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """A single issued refresh token (hashed). Revoked by setting revoked_at."""

    __tablename__ = "refresh_tokens"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
