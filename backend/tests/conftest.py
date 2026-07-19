"""Shared pytest fixtures for unit tests."""

from __future__ import annotations

import uuid

import pytest

from library.adapter.security.token_codec import JwtAccessTokenCodec
from library.core.entities import Staff
from library.core.enums import StaffRole
from library.service.auth_service import AuthService
from library.service.book_service import BookService
from library.service.loan_service import LoanService
from library.service.member_service import MemberService
from tests.fakes import (
    FakeBookRepository,
    FakeLoanRepository,
    FakeMemberRepository,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeStaffRepository,
)


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def token_codec() -> JwtAccessTokenCodec:
    # Real codec (pure + fast) with a throwaway 32+ byte secret and short TTL.
    return JwtAccessTokenCodec(secret="test-secret-0123456789-abcdefghij", ttl_seconds=900)


@pytest.fixture
def staff_repo() -> FakeStaffRepository:
    return FakeStaffRepository()


@pytest.fixture
def refresh_repo() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def make_staff(hasher: FakePasswordHasher):
    def _make(
        email: str = "admin@example.com",
        password: str = "Admin@12345",
        role: StaffRole = StaffRole.ADMIN,
        is_active: bool = True,
    ) -> Staff:
        return Staff(
            id=uuid.uuid4(),
            email=email,
            role=role,
            is_active=is_active,
            password_hash=hasher.hash(password),
        )

    return _make


@pytest.fixture
def book_repo() -> FakeBookRepository:
    return FakeBookRepository()


@pytest.fixture
def book_service(book_repo: FakeBookRepository) -> BookService:
    return BookService(repo=book_repo)


@pytest.fixture
def member_repo() -> FakeMemberRepository:
    return FakeMemberRepository()


@pytest.fixture
def member_service(member_repo: FakeMemberRepository) -> MemberService:
    return MemberService(repo=member_repo)


@pytest.fixture
def loan_repo() -> FakeLoanRepository:
    return FakeLoanRepository()


@pytest.fixture
def loan_service(
    loan_repo: FakeLoanRepository, member_repo: FakeMemberRepository
) -> LoanService:
    return LoanService(
        loan_repo=loan_repo,
        member_repo=member_repo,
        loan_period_days=14,
        fine_per_day=0.25,
    )


@pytest.fixture
def auth_service(
    staff_repo: FakeStaffRepository,
    refresh_repo: FakeRefreshTokenRepository,
    hasher: FakePasswordHasher,
    token_codec: JwtAccessTokenCodec,
) -> AuthService:
    return AuthService(
        staff_repo=staff_repo,
        refresh_repo=refresh_repo,
        hasher=hasher,
        token_codec=token_codec,
        refresh_ttl_seconds=1_209_600,
    )
