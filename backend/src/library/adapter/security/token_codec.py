"""JWT access-token codec — implements the AccessTokenCodec port (PyJWT + HS256)."""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt

from library.core.entities import AccessClaims
from library.core.enums import StaffRole
from library.core.errors import UnauthenticatedError
from library.utils.clock import utcnow

_ALGORITHM = "HS256"


class JwtAccessTokenCodec:
    """Sign and verify short-lived JWT access tokens carrying staff id + role."""

    def __init__(self, secret: str, ttl_seconds: int) -> None:
        self._secret = secret
        self._ttl_seconds = ttl_seconds

    def encode(self, staff_id: uuid.UUID, role: StaffRole) -> tuple[str, int]:
        now = utcnow()
        payload = {
            "sub": str(staff_id),
            "role": role.value,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._ttl_seconds)).timestamp()),
        }
        token = jwt.encode(payload, self._secret, algorithm=_ALGORITHM)
        return token, self._ttl_seconds

    def decode(self, token: str) -> AccessClaims:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
            return AccessClaims(
                staff_id=uuid.UUID(payload["sub"]),
                role=StaffRole(payload["role"]),
            )
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise UnauthenticatedError("Invalid or expired token") from exc
