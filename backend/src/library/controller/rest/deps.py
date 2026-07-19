"""FastAPI dependency providers — build services from request-scoped sessions + app state.

Concrete adapters (hasher, token codec) are constructed once at the composition root
(create_app) and stored on app.state; here we only wire them into per-request services.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from library.adapter.db.engine import get_session
from library.adapter.db.repositories.book_repo import SqlAlchemyBookRepository
from library.adapter.db.repositories.member_repo import SqlAlchemyMemberRepository
from library.adapter.db.repositories.refresh_token_repo import (
    SqlAlchemyRefreshTokenRepository,
)
from library.adapter.db.repositories.staff_repo import SqlAlchemyStaffRepository
from library.config import get_settings
from library.core.entities import AccessClaims
from library.core.enums import StaffRole
from library.core.errors import PermissionDeniedError, UnauthenticatedError
from library.service.auth_service import AuthService
from library.service.book_service import BookService
from library.service.member_service import MemberService


async def get_auth_service(
    request: Request, session: AsyncSession = Depends(get_session)
) -> AuthService:
    return AuthService(
        staff_repo=SqlAlchemyStaffRepository(session),
        refresh_repo=SqlAlchemyRefreshTokenRepository(session),
        hasher=request.app.state.hasher,
        token_codec=request.app.state.token_codec,
        refresh_ttl_seconds=get_settings().jwt_refresh_ttl_seconds,
    )


async def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    return BookService(repo=SqlAlchemyBookRepository(session))


async def get_member_service(session: AsyncSession = Depends(get_session)) -> MemberService:
    return MemberService(repo=SqlAlchemyMemberRepository(session))


def get_current_claims(
    request: Request, authorization: str | None = Header(default=None)
) -> AccessClaims:
    """Authenticate the request from the `Authorization: Bearer <jwt>` header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthenticatedError("Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    return request.app.state.token_codec.decode(token)


def require_role(*roles: StaffRole) -> Callable[..., AccessClaims]:
    """Dependency factory enforcing RBAC. No roles => any authenticated staff."""

    def _dependency(claims: AccessClaims = Depends(get_current_claims)) -> AccessClaims:
        if roles and claims.role not in roles:
            raise PermissionDeniedError("You do not have permission to perform this action")
        return claims

    return _dependency
