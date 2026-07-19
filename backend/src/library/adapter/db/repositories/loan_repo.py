"""LoanRepository implementation — transactional borrow/return with row locking."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from library.core.entities import CopyRef, Loan, LoanRef
from library.core.enums import CopyStatus, LoanStatus
from library.core.errors import ConflictError
from library.models.book import Book as BookModel
from library.models.book_copy import BookCopy as BookCopyModel
from library.models.fine import Fine as FineModel
from library.models.loan import Loan as LoanModel
from library.models.member import Member as MemberModel


def _view_status(returned_at: datetime | None, due_at: datetime, now: datetime) -> LoanStatus:
    if returned_at is not None:
        return LoanStatus.RETURNED
    if due_at < now:
        return LoanStatus.OVERDUE
    return LoanStatus.ACTIVE


class SqlAlchemyLoanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_copy(self, copy_id: uuid.UUID) -> CopyRef | None:
        row = await self._session.scalar(
            select(BookCopyModel).where(BookCopyModel.id == copy_id).with_for_update()
        )
        if row is None:
            return None
        return CopyRef(id=row.id, book_id=row.book_id, status=row.status)

    async def lock_available_copy_for_book(self, book_id: uuid.UUID) -> CopyRef | None:
        row = await self._session.scalar(
            select(BookCopyModel)
            .where(
                BookCopyModel.book_id == book_id,
                BookCopyModel.status == CopyStatus.AVAILABLE,
            )
            .order_by(BookCopyModel.barcode)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if row is None:
            return None
        return CopyRef(id=row.id, book_id=row.book_id, status=row.status)

    async def create_loan(
        self,
        copy_id: uuid.UUID,
        member_id: uuid.UUID,
        staff_id: uuid.UUID | None,
        borrowed_at: datetime,
        due_at: datetime,
    ) -> uuid.UUID:
        loan = LoanModel(
            copy_id=copy_id,
            member_id=member_id,
            staff_id=staff_id,
            borrowed_at=borrowed_at,
            due_at=due_at,
            status=LoanStatus.ACTIVE,
        )
        self._session.add(loan)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError("This copy is already checked out") from exc

        await self._session.execute(
            update(BookCopyModel)
            .where(BookCopyModel.id == copy_id)
            .values(status=CopyStatus.BORROWED)
        )
        return loan.id

    async def get_loan_ref(self, loan_id: uuid.UUID) -> LoanRef | None:
        row = await self._session.get(LoanModel, loan_id)
        if row is None:
            return None
        return LoanRef(
            id=row.id,
            copy_id=row.copy_id,
            member_id=row.member_id,
            due_at=row.due_at,
            returned_at=row.returned_at,
        )

    async def close_loan(self, loan_id: uuid.UUID, returned_at: datetime) -> None:
        row = await self._session.get(LoanModel, loan_id)
        if row is None:
            return
        row.returned_at = returned_at
        row.status = LoanStatus.RETURNED
        await self._session.execute(
            update(BookCopyModel)
            .where(BookCopyModel.id == row.copy_id)
            .values(status=CopyStatus.AVAILABLE)
        )
        await self._session.flush()

    async def create_fine(
        self,
        loan_id: uuid.UUID,
        member_id: uuid.UUID,
        amount: Decimal,
        reason: str,
        assessed_at: datetime,
    ) -> None:
        self._session.add(
            FineModel(
                loan_id=loan_id,
                member_id=member_id,
                amount=amount,
                reason=reason,
                assessed_at=assessed_at,
            )
        )
        await self._session.flush()

    async def get_loan_view(self, loan_id: uuid.UUID, now: datetime | None = None) -> Loan | None:
        from library.utils.clock import utcnow

        now = now or utcnow()
        stmt = self._view_select().where(LoanModel.id == loan_id)
        row = (await self._session.execute(stmt)).first()
        return self._to_view(row, now) if row else None

    async def list_loans(
        self,
        member_id: uuid.UUID | None,
        active_only: bool,
        overdue_only: bool,
        now: datetime,
        limit: int,
        offset: int,
    ) -> tuple[list[Loan], int]:
        filters = []
        if member_id is not None:
            filters.append(LoanModel.member_id == member_id)
        if active_only or overdue_only:
            filters.append(LoanModel.returned_at.is_(None))
        if overdue_only:
            filters.append(LoanModel.due_at < now)

        total = await self._session.scalar(
            select(func.count()).select_from(LoanModel).where(*filters)
        )
        stmt = (
            self._view_select()
            .where(*filters)
            .order_by(LoanModel.borrowed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).all()
        return [self._to_view(r, now) for r in rows], int(total or 0)

    # ── helpers ──
    def _view_select(self):
        return (
            select(
                LoanModel,
                BookModel.id.label("book_id"),
                BookModel.title.label("book_title"),
                BookCopyModel.barcode.label("barcode"),
                MemberModel.first_name.label("first_name"),
                MemberModel.last_name.label("last_name"),
            )
            .join(BookCopyModel, LoanModel.copy_id == BookCopyModel.id)
            .join(BookModel, BookCopyModel.book_id == BookModel.id)
            .join(MemberModel, LoanModel.member_id == MemberModel.id)
        )

    def _to_view(self, row, now: datetime) -> Loan:
        loan: LoanModel = row[0]
        return Loan(
            id=loan.id,
            copy_id=loan.copy_id,
            book_id=row.book_id,
            book_title=row.book_title,
            barcode=row.barcode,
            member_id=loan.member_id,
            member_name=f"{row.first_name} {row.last_name}",
            borrowed_at=loan.borrowed_at,
            due_at=loan.due_at,
            returned_at=loan.returned_at,
            status=_view_status(loan.returned_at, loan.due_at, now),
            staff_id=loan.staff_id,
            renewed_count=loan.renewed_count,
        )
