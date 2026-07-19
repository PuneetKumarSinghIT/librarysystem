"""Lending REST endpoints — thin controller over LoanService. Requires authentication."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from library.controller.rest.deps import get_current_claims, get_loan_service
from library.core.entities import AccessClaims
from library.core.errors import ValidationError
from library.schemas.books import PageOut
from library.schemas.loans import BorrowIn, LoanListOut, LoanOut
from library.service.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])


def _uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"{field} must be a valid UUID") from exc


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    body: BorrowIn,
    claims: AccessClaims = Depends(get_current_claims),
    service: LoanService = Depends(get_loan_service),
) -> LoanOut:
    loan = await service.borrow(
        member_id=_uuid(body.member_id, "member_id"),
        copy_id=_uuid(body.copy_id, "copy_id") if body.copy_id else None,
        book_id=_uuid(body.book_id, "book_id") if body.book_id else None,
        staff_id=claims.staff_id,
    )
    return LoanOut.from_entity(loan)


@router.post("/{loan_id}/return", response_model=LoanOut)
async def return_book(
    loan_id: uuid.UUID,
    _: AccessClaims = Depends(get_current_claims),
    service: LoanService = Depends(get_loan_service),
) -> LoanOut:
    return LoanOut.from_entity(await service.return_book(loan_id))


@router.get("", response_model=LoanListOut)
async def list_loans(
    member_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    overdue_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: AccessClaims = Depends(get_current_claims),
    service: LoanService = Depends(get_loan_service),
) -> LoanListOut:
    loans, total = await service.list_loans(member_id, active_only, overdue_only, limit, offset)
    return LoanListOut(
        items=[LoanOut.from_entity(loan) for loan in loans],
        page=PageOut(limit=limit, offset=offset, total=total),
    )
