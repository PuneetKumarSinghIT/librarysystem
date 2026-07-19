"""Domain entities and value objects — framework-free dataclasses.

Entities model business objects. Repositories (adapters) map between these and ORM models;
services operate purely on entities via ports. Populated feature-by-feature.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from library.core.enums import CopyCondition, CopyStatus, StaffRole


@dataclass(slots=True)
class BookCopy:
    """A physical copy of a book."""

    id: uuid.UUID
    book_id: uuid.UUID
    barcode: str
    condition: CopyCondition
    status: CopyStatus
    created_at: datetime | None = None


@dataclass(slots=True)
class Book:
    """A catalog title, with convenience copy counts for listing."""

    id: uuid.UUID
    title: str
    author: str
    isbn: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    category: str | None = None
    description: str | None = None
    total_copies: int = 0
    available_copies: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class Staff:
    """A library staff user (admin or librarian)."""

    id: uuid.UUID
    email: str
    role: StaffRole
    is_active: bool
    password_hash: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class RefreshTokenRecord:
    """A stored refresh token (only its hash is persisted)."""

    id: uuid.UUID
    staff_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(slots=True)
class AccessClaims:
    """Decoded claims carried by a JWT access token."""

    staff_id: uuid.UUID
    role: StaffRole


@dataclass(slots=True)
class AuthTokens:
    """Result of a successful login/refresh: the token pair plus the staff identity."""

    access_token: str
    refresh_token: str
    expires_in: int
    staff: Staff
