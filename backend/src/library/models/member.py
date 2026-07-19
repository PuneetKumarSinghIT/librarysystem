"""Library member ORM model (people who borrow books)."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from library.adapter.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    str_enum,
)
from library.core.enums import MemberStatus


class Member(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A library member who can borrow copies. Soft-deleted to preserve loan history."""

    __tablename__ = "members"

    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[MemberStatus] = mapped_column(
        str_enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE
    )
