"""Argon2id password hasher — implements the PasswordHasher port."""

from __future__ import annotations

from argon2 import PasswordHasher as _Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class Argon2PasswordHasher:
    """Hash/verify passwords using argon2id (memory-hard, resistant to GPU cracking)."""

    def __init__(self, time_cost: int = 3) -> None:
        self._hasher = _Argon2Hasher(time_cost=time_cost)

    def hash(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
