"""Unit tests for AuthService — happy paths and every failure edge case (fakes only)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from library.core.enums import StaffRole
from library.core.errors import UnauthenticatedError
from library.utils.clock import utcnow
from library.utils.tokens import hash_token


# ── login ────────────────────────────────────────────────────────────────────
async def test_login_success_issues_tokens_and_touches_login(
    auth_service, staff_repo, refresh_repo, make_staff
):
    staff = make_staff()
    staff_repo.add(staff)

    tokens = await auth_service.login("admin@example.com", "Admin@12345")

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.staff.id == staff.id
    assert tokens.expires_in == 900
    assert staff.id in staff_repo.touched
    assert refresh_repo.active_count() == 1


async def test_login_is_case_insensitive_on_email(auth_service, staff_repo, make_staff):
    staff_repo.add(make_staff(email="admin@example.com"))
    tokens = await auth_service.login("ADMIN@Example.com", "Admin@12345")
    assert tokens.staff.id == staff_repo._by_email["admin@example.com"].id


async def test_login_wrong_password_raises(auth_service, staff_repo, make_staff):
    staff_repo.add(make_staff())
    with pytest.raises(UnauthenticatedError):
        await auth_service.login("admin@example.com", "not-the-password")


async def test_login_unknown_email_raises(auth_service):
    with pytest.raises(UnauthenticatedError):
        await auth_service.login("ghost@example.com", "whatever")


async def test_login_inactive_staff_raises(auth_service, staff_repo, make_staff):
    staff_repo.add(make_staff(is_active=False))
    with pytest.raises(UnauthenticatedError):
        await auth_service.login("admin@example.com", "Admin@12345")


# ── refresh ──────────────────────────────────────────────────────────────────
async def test_refresh_success_rotates_token(auth_service, staff_repo, refresh_repo, make_staff):
    staff_repo.add(make_staff())
    first = await auth_service.login("admin@example.com", "Admin@12345")

    second = await auth_service.refresh(first.refresh_token)

    assert second.refresh_token != first.refresh_token
    assert second.access_token
    # Old rotated + new issued: exactly one active token remains.
    assert refresh_repo.active_count() == 1


async def test_refresh_unknown_token_raises(auth_service):
    with pytest.raises(UnauthenticatedError):
        await auth_service.refresh("does-not-exist")


async def test_refresh_expired_token_raises(auth_service, staff_repo, refresh_repo, make_staff):
    staff = make_staff()
    staff_repo.add(staff)
    token = "expired-token"
    await refresh_repo.add(staff.id, hash_token(token), utcnow() - timedelta(seconds=1))

    with pytest.raises(UnauthenticatedError):
        await auth_service.refresh(token)


async def test_refresh_reuse_detected_revokes_family(
    auth_service, staff_repo, refresh_repo, make_staff
):
    staff_repo.add(make_staff())
    first = await auth_service.login("admin@example.com", "Admin@12345")
    await auth_service.refresh(first.refresh_token)  # rotate: first is now revoked

    # Reusing the already-rotated token must be detected and revoke ALL tokens.
    with pytest.raises(UnauthenticatedError):
        await auth_service.refresh(first.refresh_token)

    assert refresh_repo.active_count() == 0


async def test_refresh_inactive_staff_raises(auth_service, staff_repo, make_staff):
    staff = make_staff()
    staff_repo.add(staff)
    tokens = await auth_service.login("admin@example.com", "Admin@12345")
    staff.is_active = False  # deactivated after issuing a token

    with pytest.raises(UnauthenticatedError):
        await auth_service.refresh(tokens.refresh_token)


# ── logout ───────────────────────────────────────────────────────────────────
async def test_logout_revokes_token(auth_service, staff_repo, refresh_repo, make_staff):
    staff_repo.add(make_staff())
    tokens = await auth_service.login("admin@example.com", "Admin@12345")

    await auth_service.logout(tokens.refresh_token)

    assert refresh_repo.active_count() == 0


async def test_logout_unknown_token_is_noop(auth_service):
    # Idempotent: logging out an unknown token must not raise.
    await auth_service.logout("never-issued")


# ── access-token codec round trip ────────────────────────────────────────────
async def test_access_token_encodes_and_decodes_claims(token_codec, make_staff):
    staff = make_staff(role=StaffRole.LIBRARIAN)
    token, expires_in = token_codec.encode(staff.id, staff.role)

    claims = token_codec.decode(token)

    assert claims.staff_id == staff.id
    assert claims.role == StaffRole.LIBRARIAN
    assert expires_in == 900


async def test_decode_invalid_token_raises(token_codec):
    with pytest.raises(UnauthenticatedError):
        token_codec.decode("garbage.token.value")
