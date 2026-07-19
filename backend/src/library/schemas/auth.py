"""Pydantic request/response DTOs for the auth REST endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from library.core.entities import AuthTokens


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class StaffOut(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    staff: StaffOut

    @classmethod
    def from_tokens(cls, tokens: AuthTokens) -> TokenOut:
        return cls(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            staff=StaffOut(
                id=str(tokens.staff.id),
                email=tokens.staff.email,
                role=tokens.staff.role.value,
                is_active=tokens.staff.is_active,
            ),
        )
