"""Pydantic request/response DTOs for the lending REST endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, model_validator

from library.core.entities import Loan
from library.schemas.books import PageOut


class BorrowIn(BaseModel):
    member_id: str
    copy_id: str | None = None
    book_id: str | None = None

    @model_validator(mode="after")
    def _one_target(self) -> BorrowIn:
        if not self.copy_id and not self.book_id:
            raise ValueError("Either copy_id or book_id must be provided")
        return self


class LoanOut(BaseModel):
    id: str
    copy_id: str
    book_id: str
    book_title: str
    barcode: str
    member_id: str
    member_name: str
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None
    status: str
    renewed_count: int

    @classmethod
    def from_entity(cls, loan: Loan) -> LoanOut:
        return cls(
            id=str(loan.id),
            copy_id=str(loan.copy_id),
            book_id=str(loan.book_id),
            book_title=loan.book_title,
            barcode=loan.barcode,
            member_id=str(loan.member_id),
            member_name=loan.member_name,
            borrowed_at=loan.borrowed_at,
            due_at=loan.due_at,
            returned_at=loan.returned_at,
            status=loan.status.value,
            renewed_count=loan.renewed_count,
        )


class LoanListOut(BaseModel):
    items: list[LoanOut]
    page: PageOut
