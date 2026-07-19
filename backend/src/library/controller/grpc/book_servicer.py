"""gRPC BookService servicer — thin adapter over BookService."""

from __future__ import annotations

import uuid

from library.adapter.db.repositories.book_repo import SqlAlchemyBookRepository
from library.controller.grpc.base import AuthenticatedServicer
from library.controller.grpc.errors import grpc_status_for
from library.core.commands import BookCreate
from library.core.entities import Book, BookCopy
from library.core.enums import CopyCondition
from library.core.errors import DomainError, ValidationError
from library.service.book_service import BookService
from library.v1 import books_pb2, books_pb2_grpc, common_pb2


def _book_proto(b: Book) -> books_pb2.Book:
    return books_pb2.Book(
        id=str(b.id),
        title=b.title,
        author=b.author,
        isbn=b.isbn or "",
        publisher=b.publisher or "",
        published_year=b.published_year or 0,
        category=b.category or "",
        description=b.description or "",
        total_copies=b.total_copies,
        available_copies=b.available_copies,
    )


def _copy_proto(c: BookCopy) -> books_pb2.BookCopy:
    return books_pb2.BookCopy(
        id=str(c.id),
        book_id=str(c.book_id),
        barcode=c.barcode,
        condition=c.condition.value,
        status=c.status.value,
    )


def _parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"{field} must be a valid UUID") from exc


class BookServicer(AuthenticatedServicer, books_pb2_grpc.BookServiceServicer):
    async def CreateBook(self, request, context) -> books_pb2.Book:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                book = await BookService(SqlAlchemyBookRepository(session)).create_book(
                    BookCreate(
                        title=request.title,
                        author=request.author,
                        isbn=request.isbn or None,
                        publisher=request.publisher or None,
                        published_year=request.published_year or None,
                        category=request.category or None,
                        description=request.description or None,
                    )
                )
                await session.commit()
                return _book_proto(book)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def UpdateBook(self, request, context) -> books_pb2.Book:
        await self._authenticate(context)
        changes: dict = {}
        for field in ("title", "author", "isbn", "publisher", "category", "description"):
            value = getattr(request, field)
            if value:
                changes[field] = value
        if request.published_year:
            changes["published_year"] = request.published_year
        async with self._sessionmaker() as session:
            try:
                book = await BookService(SqlAlchemyBookRepository(session)).update_book(
                    _parse_uuid(request.id, "id"), changes
                )
                await session.commit()
                return _book_proto(book)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def GetBook(self, request, context) -> books_pb2.Book:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                book = await BookService(SqlAlchemyBookRepository(session)).get_book(
                    _parse_uuid(request.id, "id")
                )
                return _book_proto(book)
            except DomainError as exc:
                await context.abort(grpc_status_for(exc), exc.message)

    async def ListBooks(self, request, context) -> books_pb2.ListBooksResponse:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            books, total = await BookService(SqlAlchemyBookRepository(session)).list_books(
                request.search or None, request.page.limit or None, request.page.offset
            )
            return books_pb2.ListBooksResponse(
                books=[_book_proto(b) for b in books],
                page=common_pb2.PageInfo(
                    limit=request.page.limit or 20, offset=request.page.offset, total=total
                ),
            )

    async def AddCopy(self, request, context) -> books_pb2.BookCopy:
        await self._authenticate(context)
        condition = None
        if request.condition:
            try:
                condition = CopyCondition(request.condition)
            except ValueError:
                await context.abort(
                    grpc_status_for(ValidationError("invalid condition")), "invalid condition"
                )
        async with self._sessionmaker() as session:
            try:
                copy = await BookService(SqlAlchemyBookRepository(session)).add_copy(
                    _parse_uuid(request.book_id, "book_id"), request.barcode, condition
                )
                await session.commit()
                return _copy_proto(copy)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def ListCopies(self, request, context) -> books_pb2.ListCopiesResponse:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                copies = await BookService(SqlAlchemyBookRepository(session)).list_copies(
                    _parse_uuid(request.book_id, "book_id")
                )
                return books_pb2.ListCopiesResponse(copies=[_copy_proto(c) for c in copies])
            except DomainError as exc:
                await context.abort(grpc_status_for(exc), exc.message)
