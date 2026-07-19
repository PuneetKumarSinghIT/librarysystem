"""Pydantic request/response DTOs for the member REST endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from library.core.entities import Member
from library.schemas.books import PageOut  # shared pagination shape


class MemberCreateIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)


class MemberUpdateIn(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    status: str | None = None


class MemberOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    address: str | None
    status: str

    @classmethod
    def from_entity(cls, member: Member) -> MemberOut:
        return cls(
            id=str(member.id),
            first_name=member.first_name,
            last_name=member.last_name,
            email=member.email,
            phone=member.phone,
            address=member.address,
            status=member.status.value,
        )


class MemberListOut(BaseModel):
    items: list[MemberOut]
    page: PageOut
