"""Book/copy REST endpoints — thin controller over BookService. Requires authentication."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from library.controller.rest.deps import get_book_service, get_current_claims
from library.core.commands import BookCreate
from library.core.enums import CopyCondition
from library.core.errors import ValidationError
from library.schemas.books import (
    BookCreateIn,
    BookListOut,
    BookOut,
    BookUpdateIn,
    CopyCreateIn,
    CopyOut,
    PageOut,
)
from library.service.book_service import BookService

router = APIRouter(
    prefix="/books",
    tags=["books"],
    dependencies=[Depends(get_current_claims)],  # all book ops require a valid staff token
)


def _parse_condition(value: str | None) -> CopyCondition | None:
    if value is None:
        return None
    try:
        return CopyCondition(value)
    except ValueError as exc:
        allowed = ", ".join(c.value for c in CopyCondition)
        raise ValidationError(f"condition must be one of: {allowed}") from exc


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(
    body: BookCreateIn, service: BookService = Depends(get_book_service)
) -> BookOut:
    book = await service.create_book(BookCreate(**body.model_dump()))
    return BookOut.from_entity(book)


@router.get("", response_model=BookListOut)
async def list_books(
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: BookService = Depends(get_book_service),
) -> BookListOut:
    books, total = await service.list_books(search, limit, offset)
    return BookListOut(
        items=[BookOut.from_entity(b) for b in books],
        page=PageOut(limit=limit, offset=offset, total=total),
    )


@router.get("/{book_id}", response_model=BookOut)
async def get_book(
    book_id: uuid.UUID, service: BookService = Depends(get_book_service)
) -> BookOut:
    return BookOut.from_entity(await service.get_book(book_id))


@router.patch("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: uuid.UUID,
    body: BookUpdateIn,
    service: BookService = Depends(get_book_service),
) -> BookOut:
    changes = body.model_dump(exclude_unset=True)
    return BookOut.from_entity(await service.update_book(book_id, changes))


@router.post("/{book_id}/copies", response_model=CopyOut, status_code=status.HTTP_201_CREATED)
async def add_copy(
    book_id: uuid.UUID,
    body: CopyCreateIn,
    service: BookService = Depends(get_book_service),
) -> CopyOut:
    copy = await service.add_copy(book_id, body.barcode, _parse_condition(body.condition))
    return CopyOut.from_entity(copy)


@router.get("/{book_id}/copies", response_model=list[CopyOut])
async def list_copies(
    book_id: uuid.UUID, service: BookService = Depends(get_book_service)
) -> list[CopyOut]:
    copies = await service.list_copies(book_id)
    return [CopyOut.from_entity(c) for c in copies]
