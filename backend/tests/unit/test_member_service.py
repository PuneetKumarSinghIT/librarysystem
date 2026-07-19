"""Unit tests for MemberService — validation, uniqueness, not-found, soft delete, search."""

from __future__ import annotations

import uuid

import pytest

from library.core.commands import MemberCreate
from library.core.enums import MemberStatus
from library.core.errors import AlreadyExistsError, NotFoundError, ValidationError


def _valid(**overrides) -> MemberCreate:
    base = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
    base.update(overrides)
    return MemberCreate(**base)


# ── create ───────────────────────────────────────────────────────────────────
async def test_create_success_normalizes_email(member_service):
    member = await member_service.create_member(_valid(email="Ada@Example.COM"))
    assert member.email == "ada@example.com"
    assert member.status == MemberStatus.ACTIVE


@pytest.mark.parametrize("field", ["first_name", "last_name"])
async def test_create_requires_names(member_service, field):
    with pytest.raises(ValidationError):
        await member_service.create_member(_valid(**{field: "  "}))


async def test_create_rejects_bad_email(member_service):
    with pytest.raises(ValidationError):
        await member_service.create_member(_valid(email="not-an-email"))


async def test_create_duplicate_email_raises(member_service):
    await member_service.create_member(_valid())
    with pytest.raises(AlreadyExistsError):
        await member_service.create_member(_valid(first_name="Other"))


# ── get / update ──────────────────────────────────────────────────────────────
async def test_get_missing_raises(member_service):
    with pytest.raises(NotFoundError):
        await member_service.get_member(uuid.uuid4())


async def test_update_success(member_service):
    member = await member_service.create_member(_valid())
    updated = await member_service.update_member(member.id, {"phone": "+1-555-9999"})
    assert updated.phone == "+1-555-9999"


async def test_update_status_success(member_service):
    member = await member_service.create_member(_valid())
    updated = await member_service.update_member(member.id, {"status": "suspended"})
    assert updated.status == MemberStatus.SUSPENDED


async def test_update_invalid_status_raises(member_service):
    member = await member_service.create_member(_valid())
    with pytest.raises(ValidationError):
        await member_service.update_member(member.id, {"status": "banned"})


async def test_update_unknown_field_raises(member_service):
    member = await member_service.create_member(_valid())
    with pytest.raises(ValidationError):
        await member_service.update_member(member.id, {"role": "admin"})


async def test_update_missing_raises(member_service):
    with pytest.raises(NotFoundError):
        await member_service.update_member(uuid.uuid4(), {"first_name": "X"})


async def test_update_duplicate_email_raises(member_service):
    await member_service.create_member(_valid(email="a@example.com"))
    m2 = await member_service.create_member(_valid(email="b@example.com"))
    with pytest.raises(AlreadyExistsError):
        await member_service.update_member(m2.id, {"email": "a@example.com"})


# ── list / delete ─────────────────────────────────────────────────────────────
async def test_list_search(member_service):
    await member_service.create_member(_valid(email="ada@example.com", first_name="Ada"))
    await member_service.create_member(
        _valid(email="alan@example.com", first_name="Alan", last_name="Turing")
    )
    items, total = await member_service.list_members("turing", limit=20, offset=0)
    assert total == 1
    assert items[0].last_name == "Turing"


async def test_delete_success(member_service):
    member = await member_service.create_member(_valid())
    await member_service.delete_member(member.id)
    with pytest.raises(NotFoundError):
        await member_service.get_member(member.id)


async def test_delete_missing_raises(member_service):
    with pytest.raises(NotFoundError):
        await member_service.delete_member(uuid.uuid4())
