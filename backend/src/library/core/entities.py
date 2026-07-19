"""Domain entities — framework-free dataclasses.

Entities model the business objects and their invariants. Repositories (adapters) map
between these and ORM models; services operate purely on entities via ports. Populated
feature-by-feature (F1+) as each aggregate is introduced.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from library.core.enums import StaffRole


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
