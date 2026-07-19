"""gRPC LoanService servicer — thin adapter over LoanService."""

from __future__ import annotations

import uuid

from google.protobuf.timestamp_pb2 import Timestamp

from library.adapter.db.repositories.loan_repo import SqlAlchemyLoanRepository
from library.adapter.db.repositories.member_repo import SqlAlchemyMemberRepository
from library.config import get_settings
from library.controller.grpc.base import AuthenticatedServicer
from library.controller.grpc.errors import grpc_status_for
from library.core.entities import Loan
from library.core.errors import DomainError, ValidationError
from library.service.loan_service import LoanService
from library.v1 import common_pb2, loans_pb2, loans_pb2_grpc


def _ts(value) -> Timestamp | None:
    if value is None:
        return None
    ts = Timestamp()
    ts.FromDatetime(value)
    return ts


def _loan_proto(loan: Loan) -> loans_pb2.Loan:
    msg = loans_pb2.Loan(
        id=str(loan.id),
        copy_id=str(loan.copy_id),
        book_id=str(loan.book_id),
        book_title=loan.book_title,
        barcode=loan.barcode,
        member_id=str(loan.member_id),
        member_name=loan.member_name,
        staff_id=str(loan.staff_id) if loan.staff_id else "",
        status=loan.status.value,
        renewed_count=loan.renewed_count,
        borrowed_at=_ts(loan.borrowed_at),
        due_at=_ts(loan.due_at),
    )
    if loan.returned_at is not None:
        msg.returned_at.CopyFrom(_ts(loan.returned_at))
    return msg


def _parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"{field} must be a valid UUID") from exc


class LoanServicer(AuthenticatedServicer, loans_pb2_grpc.LoanServiceServicer):
    def _svc(self, session) -> LoanService:
        settings = get_settings()
        return LoanService(
            loan_repo=SqlAlchemyLoanRepository(session),
            member_repo=SqlAlchemyMemberRepository(session),
            loan_period_days=settings.loan_period_days,
            fine_per_day=settings.fine_per_day,
        )

    async def BorrowBook(self, request, context) -> loans_pb2.Loan:
        claims = await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                loan = await self._svc(session).borrow(
                    member_id=_parse_uuid(request.member_id, "member_id"),
                    copy_id=_parse_uuid(request.copy_id, "copy_id") if request.copy_id else None,
                    book_id=_parse_uuid(request.book_id, "book_id") if request.book_id else None,
                    staff_id=claims.staff_id,
                )
                await session.commit()
                return _loan_proto(loan)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def ReturnBook(self, request, context) -> loans_pb2.Loan:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                loan = await self._svc(session).return_book(
                    _parse_uuid(request.loan_id, "loan_id")
                )
                await session.commit()
                return _loan_proto(loan)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def ListLoans(self, request, context) -> loans_pb2.ListLoansResponse:
        await self._authenticate(context)
        member_id = _parse_uuid(request.member_id, "member_id") if request.member_id else None
        async with self._sessionmaker() as session:
            loans, total = await self._svc(session).list_loans(
                member_id,
                request.active_only,
                request.overdue_only,
                request.page.limit or None,
                request.page.offset,
            )
            return loans_pb2.ListLoansResponse(
                loans=[_loan_proto(loan) for loan in loans],
                page=common_pb2.PageInfo(
                    limit=request.page.limit or 20, offset=request.page.offset, total=total
                ),
            )
