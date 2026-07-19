"""Unit tests for LoanService — borrow, return, double-borrow, overdue fines, queries."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from library.core.entities import Member
from library.core.enums import CopyStatus, LoanStatus, MemberStatus
from library.core.errors import ConflictError, NotFoundError, ValidationError
from library.utils.clock import utcnow


def _add_member(member_repo, loan_repo, status=MemberStatus.ACTIVE) -> Member:
    member = Member(
        id=uuid.uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        status=status,
    )
    member_repo.members[member.id] = member
    loan_repo.register_member(member.id, "Ada Lovelace")
    return member


# ── borrow ───────────────────────────────────────────────────────────────────
async def test_borrow_specific_copy_success(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy(barcode="BC-1", title="DDD")

    loan = await loan_service.borrow(member.id, copy_id, None, staff_id=None)

    assert loan.status == LoanStatus.ACTIVE
    assert loan.barcode == "BC-1"
    assert loan_repo.copies[copy_id]["status"] == CopyStatus.BORROWED
    assert loan.due_at > loan.borrowed_at


async def test_borrow_by_book_picks_available_copy(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    book_id = uuid.uuid4()
    loan_repo.add_copy(book_id=book_id, status=CopyStatus.BORROWED, barcode="B1")
    free = loan_repo.add_copy(book_id=book_id, status=CopyStatus.AVAILABLE, barcode="B2")

    loan = await loan_service.borrow(member.id, None, book_id, staff_id=None)
    assert loan.copy_id == free


async def test_borrow_unknown_member_raises(loan_service, loan_repo):
    copy_id = loan_repo.add_copy()
    with pytest.raises(NotFoundError):
        await loan_service.borrow(uuid.uuid4(), copy_id, None, None)


async def test_borrow_suspended_member_raises(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo, status=MemberStatus.SUSPENDED)
    copy_id = loan_repo.add_copy()
    with pytest.raises(ConflictError):
        await loan_service.borrow(member.id, copy_id, None, None)


async def test_borrow_unknown_copy_raises(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    with pytest.raises(NotFoundError):
        await loan_service.borrow(member.id, uuid.uuid4(), None, None)


async def test_borrow_unavailable_copy_raises(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy(status=CopyStatus.BORROWED)
    with pytest.raises(ConflictError):
        await loan_service.borrow(member.id, copy_id, None, None)


async def test_borrow_no_available_copy_for_book_raises(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    book_id = uuid.uuid4()
    loan_repo.add_copy(book_id=book_id, status=CopyStatus.BORROWED)
    with pytest.raises(ConflictError):
        await loan_service.borrow(member.id, None, book_id, None)


async def test_borrow_requires_copy_or_book(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    with pytest.raises(ValidationError):
        await loan_service.borrow(member.id, None, None, None)


async def test_double_borrow_same_copy_rejected(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy()
    await loan_service.borrow(member.id, copy_id, None, None)
    # Simulate the copy still looking available (race) — the unique guard must reject.
    loan_repo.copies[copy_id]["status"] = CopyStatus.AVAILABLE
    with pytest.raises(ConflictError):
        await loan_service.borrow(member.id, copy_id, None, None)


# ── return ───────────────────────────────────────────────────────────────────
async def test_return_success_frees_copy(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy()
    loan = await loan_service.borrow(member.id, copy_id, None, None)

    returned = await loan_service.return_book(loan.id)

    assert returned.status == LoanStatus.RETURNED
    assert returned.returned_at is not None
    assert loan_repo.copies[copy_id]["status"] == CopyStatus.AVAILABLE


async def test_return_unknown_loan_raises(loan_service):
    with pytest.raises(NotFoundError):
        await loan_service.return_book(uuid.uuid4())


async def test_return_already_returned_raises(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy()
    loan = await loan_service.borrow(member.id, copy_id, None, None)
    await loan_service.return_book(loan.id)
    with pytest.raises(ConflictError):
        await loan_service.return_book(loan.id)


async def test_return_overdue_creates_fine(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy()
    loan = await loan_service.borrow(member.id, copy_id, None, None)
    # Force the loan to be 3 days overdue.
    loan_repo.loans[loan.id]["due_at"] = utcnow() - timedelta(days=3)

    await loan_service.return_book(loan.id)

    assert len(loan_repo.fines) == 1
    assert loan_repo.fines[0]["member_id"] == member.id
    assert loan_repo.fines[0]["amount"] > 0


async def test_return_on_time_no_fine(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    copy_id = loan_repo.add_copy()
    loan = await loan_service.borrow(member.id, copy_id, None, None)
    await loan_service.return_book(loan.id)
    assert loan_repo.fines == []


# ── queries ──────────────────────────────────────────────────────────────────
async def test_list_active_loans_for_member(loan_service, loan_repo, member_repo):
    member = _add_member(member_repo, loan_repo)
    c1 = loan_repo.add_copy(barcode="A")
    c2 = loan_repo.add_copy(barcode="B")
    loan1 = await loan_service.borrow(member.id, c1, None, None)
    await loan_service.borrow(member.id, c2, None, None)
    await loan_service.return_book(loan1.id)

    active, total = await loan_service.list_loans(member.id, True, False, 20, 0)
    assert total == 1
    assert active[0].status == LoanStatus.ACTIVE
