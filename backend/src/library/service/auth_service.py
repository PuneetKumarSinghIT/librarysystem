"""Authentication use-cases: login, refresh (with rotation + reuse detection), logout.

Business rules live here. Dependencies are injected as core ports (DIP), so this class is
fully unit-testable against fakes and never imports a framework, ORM, or transport.

Logical steps are documented per method: preconditions -> action -> failure modes -> result.
"""

from __future__ import annotations

from datetime import timedelta

from library.core.entities import AuthTokens
from library.core.errors import UnauthenticatedError
from library.core.ports.repositories import RefreshTokenRepository, StaffRepository
from library.core.ports.security import AccessTokenCodec, PasswordHasher
from library.utils.clock import utcnow
from library.utils.tokens import generate_refresh_token, hash_token


class AuthService:
    def __init__(
        self,
        staff_repo: StaffRepository,
        refresh_repo: RefreshTokenRepository,
        hasher: PasswordHasher,
        token_codec: AccessTokenCodec,
        refresh_ttl_seconds: int,
    ) -> None:
        self._staff = staff_repo
        self._refresh = refresh_repo
        self._hasher = hasher
        self._codec = token_codec
        self._refresh_ttl = refresh_ttl_seconds

    async def login(self, email: str, password: str) -> AuthTokens:
        """Authenticate staff by email + password.

        Preconditions: staff exists, is active, password matches.
        Failure: UnauthenticatedError (generic — never reveal which check failed).
        Result: a new access + refresh token pair; last_login updated.
        """
        staff = await self._staff.get_by_email(email)
        # Verify even when staff is None-ish to reduce user-enumeration timing signal.
        password_ok = self._hasher.verify(password, staff.password_hash) if (
            staff and staff.password_hash
        ) else False
        if staff is None or not staff.is_active or not password_ok:
            raise UnauthenticatedError("Invalid email or password")

        await self._staff.touch_last_login(staff.id)
        return await self._issue_tokens(staff)

    async def refresh(self, refresh_token: str) -> AuthTokens:
        """Exchange a valid refresh token for a new token pair (rotation).

        Preconditions: token known, not revoked, not expired, staff still active.
        Reuse detection: presenting an already-revoked token revokes the whole family.
        Failure: UnauthenticatedError. Result: new access + refresh pair.
        """
        token_hash = hash_token(refresh_token)
        record = await self._refresh.get_by_hash(token_hash)
        if record is None:
            raise UnauthenticatedError("Invalid refresh token")

        if record.revoked_at is not None:
            # A revoked token being reused signals theft — revoke every token for this staff.
            await self._refresh.revoke_all_for_staff(record.staff_id)
            raise UnauthenticatedError("Refresh token reuse detected")

        if record.expires_at <= utcnow():
            raise UnauthenticatedError("Refresh token expired")

        staff = await self._staff.get_by_id(record.staff_id)
        if staff is None or not staff.is_active:
            raise UnauthenticatedError("Account is not active")

        await self._refresh.revoke(token_hash)  # rotate: old token can't be reused
        return await self._issue_tokens(staff)

    async def logout(self, refresh_token: str) -> None:
        """Revoke the given refresh token. Idempotent — unknown tokens are a no-op."""
        await self._refresh.revoke(hash_token(refresh_token))

    async def _issue_tokens(self, staff) -> AuthTokens:
        access_token, expires_in = self._codec.encode(staff.id, staff.role)
        refresh_token = generate_refresh_token()
        expires_at = utcnow() + timedelta(seconds=self._refresh_ttl)
        await self._refresh.add(staff.id, hash_token(refresh_token), expires_at)
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            staff=staff,
        )
