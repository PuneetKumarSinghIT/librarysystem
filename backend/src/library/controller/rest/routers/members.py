"""Member REST endpoints — thin controller over MemberService. Requires authentication."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from library.controller.rest.deps import get_current_claims, get_member_service
from library.core.commands import MemberCreate
from library.schemas.books import PageOut
from library.schemas.members import (
    MemberCreateIn,
    MemberListOut,
    MemberOut,
    MemberUpdateIn,
)
from library.service.member_service import MemberService

router = APIRouter(
    prefix="/members",
    tags=["members"],
    dependencies=[Depends(get_current_claims)],
)


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def create_member(
    body: MemberCreateIn, service: MemberService = Depends(get_member_service)
) -> MemberOut:
    member = await service.create_member(MemberCreate(**body.model_dump()))
    return MemberOut.from_entity(member)


@router.get("", response_model=MemberListOut)
async def list_members(
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: MemberService = Depends(get_member_service),
) -> MemberListOut:
    members, total = await service.list_members(search, limit, offset)
    return MemberListOut(
        items=[MemberOut.from_entity(m) for m in members],
        page=PageOut(limit=limit, offset=offset, total=total),
    )


@router.get("/{member_id}", response_model=MemberOut)
async def get_member(
    member_id: uuid.UUID, service: MemberService = Depends(get_member_service)
) -> MemberOut:
    return MemberOut.from_entity(await service.get_member(member_id))


@router.patch("/{member_id}", response_model=MemberOut)
async def update_member(
    member_id: uuid.UUID,
    body: MemberUpdateIn,
    service: MemberService = Depends(get_member_service),
) -> MemberOut:
    changes = body.model_dump(exclude_unset=True)
    return MemberOut.from_entity(await service.update_member(member_id, changes))


@router.delete("/{member_id}", status_code=status.HTTP_200_OK)
async def delete_member(
    member_id: uuid.UUID, service: MemberService = Depends(get_member_service)
) -> dict[str, bool]:
    await service.delete_member(member_id)
    return {"success": True}
