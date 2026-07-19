"""Security ports — abstractions the service layer depends on (Dependency Inversion).

Small, focused interfaces (Interface Segregation): one for hashing, one for access tokens.
Adapters in `library.adapter.security` implement these.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from library.core.entities import AccessClaims
from library.core.enums import StaffRole


class PasswordHasher(Protocol):
    """Hash and verify passwords. Implementations must use a strong KDF (argon2id)."""

    def hash(self, plain: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...


class AccessTokenCodec(Protocol):
    """Encode/decode short-lived JWT access tokens."""

    def encode(self, staff_id: uuid.UUID, role: StaffRole) -> tuple[str, int]:
        """Return (signed_jwt, expires_in_seconds)."""
        ...

    def decode(self, token: str) -> AccessClaims:
        """Return claims, or raise UnauthenticatedError if invalid/expired."""
        ...
