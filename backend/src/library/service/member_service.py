"""Member use-cases: create, update, get, list (search + pagination), soft delete.

Business rules and validation here; depends only on the MemberRepository port (DIP).
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from typing import Any

from library.core.commands import MemberCreate
from library.core.entities import Member
from library.core.enums import MemberStatus
from library.core.errors import NotFoundError, ValidationError
from library.core.ports.repositories import MemberRepository
from library.utils.pagination import clamp_page

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_UPDATABLE_FIELDS = {"first_name", "last_name", "email", "phone", "address", "status"}


class MemberService:
    def __init__(self, repo: MemberRepository) -> None:
        self._repo = repo

    async def create_member(self, data: MemberCreate) -> Member:
        return await self._repo.create(
            MemberCreate(
                first_name=_require_text(data.first_name, "first_name"),
                last_name=_require_text(data.last_name, "last_name"),
                email=_normalize_email(data.email),
                phone=_clean(data.phone),
                address=_clean(data.address),
            )
        )

    async def update_member(self, member_id: uuid.UUID, changes: Mapping[str, Any]) -> Member:
        unknown = set(changes) - _UPDATABLE_FIELDS
        if unknown:
            raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")

        cleaned: dict[str, Any] = dict(changes)
        if "first_name" in cleaned:
            cleaned["first_name"] = _require_text(cleaned["first_name"], "first_name")
        if "last_name" in cleaned:
            cleaned["last_name"] = _require_text(cleaned["last_name"], "last_name")
        if "email" in cleaned:
            cleaned["email"] = _normalize_email(cleaned["email"])
        if "status" in cleaned:
            cleaned["status"] = _validate_status(cleaned["status"])

        member = await self._repo.update(member_id, cleaned)
        if member is None:
            raise NotFoundError("Member not found")
        return member

    async def get_member(self, member_id: uuid.UUID) -> Member:
        member = await self._repo.get(member_id)
        if member is None:
            raise NotFoundError("Member not found")
        return member

    async def list_members(
        self, search: str | None, limit: int | None, offset: int | None
    ) -> tuple[list[Member], int]:
        clamped_limit, clamped_offset = clamp_page(limit, offset)
        term = search.strip() if search else None
        return await self._repo.list(term or None, clamped_limit, clamped_offset)

    async def delete_member(self, member_id: uuid.UUID) -> None:
        if not await self._repo.soft_delete(member_id):
            raise NotFoundError("Member not found")


# ── validation helpers ───────────────────────────────────────────────────────
def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _require_text(value: str | None, field: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise ValidationError(f"{field} is required")
    return cleaned


def _normalize_email(email: str | None) -> str:
    cleaned = _require_text(email, "email").lower()
    if not _EMAIL_RE.match(cleaned):
        raise ValidationError("email must be a valid email address")
    return cleaned


def _validate_status(status: Any) -> MemberStatus:
    try:
        return MemberStatus(status)
    except ValueError as exc:
        allowed = ", ".join(s.value for s in MemberStatus)
        raise ValidationError(f"status must be one of: {allowed}") from exc
