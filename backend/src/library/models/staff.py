"""Staff user ORM model (library employees who operate the system)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from library.adapter.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from library.core.enums import StaffRole


class StaffUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A library staff account (admin or librarian) that can operate the system."""

    __tablename__ = "staff_users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[StaffRole] = mapped_column(
        str_enum(StaffRole), nullable=False, default=StaffRole.LIBRARIAN
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
