"""Auth REST endpoints — thin controller over AuthService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from library.controller.rest.deps import get_auth_service
from library.schemas.auth import LoginIn, LogoutIn, RefreshIn, TokenOut
from library.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut, summary="Staff login")
async def login(body: LoginIn, service: AuthService = Depends(get_auth_service)) -> TokenOut:
    tokens = await service.login(body.email, body.password)
    return TokenOut.from_tokens(tokens)


@router.post("/refresh", response_model=TokenOut, summary="Rotate tokens")
async def refresh(
    body: RefreshIn, service: AuthService = Depends(get_auth_service)
) -> TokenOut:
    tokens = await service.refresh(body.refresh_token)
    return TokenOut.from_tokens(tokens)


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Revoke a refresh token")
async def logout(
    body: LogoutIn, service: AuthService = Depends(get_auth_service)
) -> dict[str, bool]:
    await service.logout(body.refresh_token)
    return {"success": True}
