"""gRPC AuthService servicer — thin adapter over AuthService (mirrors the REST router)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker

from library.adapter.db.repositories.refresh_token_repo import (
    SqlAlchemyRefreshTokenRepository,
)
from library.adapter.db.repositories.staff_repo import SqlAlchemyStaffRepository
from library.controller.grpc.errors import grpc_status_for
from library.core.entities import AuthTokens
from library.core.errors import DomainError
from library.core.ports.security import AccessTokenCodec, PasswordHasher
from library.service.auth_service import AuthService
from library.v1 import auth_pb2, auth_pb2_grpc


def _to_token_response(tokens: AuthTokens) -> auth_pb2.TokenResponse:
    return auth_pb2.TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="Bearer",
        expires_in=tokens.expires_in,
        staff=auth_pb2.Staff(
            id=str(tokens.staff.id),
            email=tokens.staff.email,
            role=tokens.staff.role.value,
            is_active=tokens.staff.is_active,
        ),
    )


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    def __init__(
        self,
        sessionmaker: async_sessionmaker,
        hasher: PasswordHasher,
        token_codec: AccessTokenCodec,
        refresh_ttl_seconds: int,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._hasher = hasher
        self._codec = token_codec
        self._refresh_ttl = refresh_ttl_seconds

    def _service(self, session) -> AuthService:
        return AuthService(
            staff_repo=SqlAlchemyStaffRepository(session),
            refresh_repo=SqlAlchemyRefreshTokenRepository(session),
            hasher=self._hasher,
            token_codec=self._codec,
            refresh_ttl_seconds=self._refresh_ttl,
        )

    async def Login(self, request, context) -> auth_pb2.TokenResponse:
        async with self._sessionmaker() as session:
            try:
                tokens = await self._service(session).login(request.email, request.password)
                await session.commit()
                return _to_token_response(tokens)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def Refresh(self, request, context) -> auth_pb2.TokenResponse:
        async with self._sessionmaker() as session:
            try:
                tokens = await self._service(session).refresh(request.refresh_token)
                await session.commit()
                return _to_token_response(tokens)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def Logout(self, request, context) -> auth_pb2.LogoutResponse:
        async with self._sessionmaker() as session:
            try:
                await self._service(session).logout(request.refresh_token)
                await session.commit()
                return auth_pb2.LogoutResponse(success=True)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)
