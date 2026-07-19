"""Lending use-cases: borrow, return, and loan queries.

Business rules live here. The DB partial unique index on loans(copy_id) WHERE
returned_at IS NULL is the ultimate guard against double-borrow; this service also checks
copy availability under a row lock and maps a unique violation to a clear ConflictError.
"""

from __future__ import annotations

import math
import uuid
from datetime import timedelta
from decimal import Decimal

from library.core.entities import Loan
from library.core.enums import CopyStatus, MemberStatus
from library.core.errors import ConflictError, NotFoundError, ValidationError
from library.core.ports.repositories import LoanRepository, MemberRepository
from library.utils.clock import utcnow
from library.utils.pagination import clamp_page


class LoanService:
    def __init__(
        self,
        loan_repo: LoanRepository,
        member_repo: MemberRepository,
        loan_period_days: int,
        fine_per_day: float,
    ) -> None:
        self._loans = loan_repo
        self._members = member_repo
        self._loan_period_days = loan_period_days
        self._fine_per_day = Decimal(str(fine_per_day))

    async def borrow(
        self,
        member_id: uuid.UUID,
        copy_id: uuid.UUID | None,
        book_id: uuid.UUID | None,
        staff_id: uuid.UUID | None,
    ) -> Loan:
        """Record a borrow.

        Steps: validate member (exists + active) -> resolve & lock a copy -> ensure it is
        available -> insert loan + flip copy to borrowed (one transaction).
        Failure modes: NotFound (member/copy/book), Conflict (suspended, unavailable,
        already checked out), Validation (no copy_id/book_id).
        """
        member = await self._members.get(member_id)
        if member is None:
            raise NotFoundError("Member not found")
        if member.status != MemberStatus.ACTIVE:
            raise ConflictError("Member is suspended and cannot borrow")

        copy = await self._resolve_copy(copy_id, book_id)
        if copy.status != CopyStatus.AVAILABLE:
            raise ConflictError("This copy is already checked out or unavailable")

        borrowed_at = utcnow()
        due_at = borrowed_at + timedelta(days=self._loan_period_days)
        try:
            loan_id = await self._loans.create_loan(
                copy.id, member_id, staff_id, borrowed_at, due_at
            )
        except ConflictError:
            # Lost the race to the partial unique index — someone else borrowed it first.
            raise ConflictError("This copy is already checked out") from None

        view = await self._loans.get_loan_view(loan_id)
        assert view is not None  # just created
        return view

    async def return_book(self, loan_id: uuid.UUID) -> Loan:
        """Close an open loan, free the copy, and assess an overdue fine if applicable."""
        ref = await self._loans.get_loan_ref(loan_id)
        if ref is None:
            raise NotFoundError("Loan not found")
        if ref.returned_at is not None:
            raise ConflictError("This loan has already been returned")

        returned_at = utcnow()
        await self._loans.close_loan(loan_id, returned_at)

        if returned_at > ref.due_at and self._fine_per_day > 0:
            days_overdue = max(1, math.ceil((returned_at - ref.due_at).total_seconds() / 86400))
            amount = self._fine_per_day * days_overdue
            await self._loans.create_fine(
                loan_id, ref.member_id, amount, "Overdue return", returned_at
            )

        view = await self._loans.get_loan_view(loan_id)
        assert view is not None
        return view

    async def list_loans(
        self,
        member_id: uuid.UUID | None,
        active_only: bool,
        overdue_only: bool,
        limit: int | None,
        offset: int | None,
    ) -> tuple[list[Loan], int]:
        clamped_limit, clamped_offset = clamp_page(limit, offset)
        return await self._loans.list_loans(
            member_id, active_only, overdue_only, utcnow(), clamped_limit, clamped_offset
        )

    async def _resolve_copy(self, copy_id: uuid.UUID | None, book_id: uuid.UUID | None):
        if copy_id is not None:
            copy = await self._loans.lock_copy(copy_id)
            if copy is None:
                raise NotFoundError("Copy not found")
            return copy
        if book_id is not None:
            copy = await self._loans.lock_available_copy_for_book(book_id)
            if copy is None:
                raise ConflictError("No copies of this book are available")
            return copy
        raise ValidationError("Either copy_id or book_id must be provided")
