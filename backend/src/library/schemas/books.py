"""Pydantic request/response DTOs for the book/copy REST endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from library.core.entities import Book, BookCopy


class BookCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str = Field(min_length=1, max_length=300)
    isbn: str | None = Field(default=None, max_length=20)
    publisher: str | None = Field(default=None, max_length=300)
    published_year: int | None = None
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None


class BookUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    author: str | None = Field(default=None, max_length=300)
    isbn: str | None = Field(default=None, max_length=20)
    publisher: str | None = Field(default=None, max_length=300)
    published_year: int | None = None
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None


class CopyCreateIn(BaseModel):
    barcode: str = Field(min_length=1, max_length=64)
    condition: str | None = None


class BookOut(BaseModel):
    id: str
    title: str
    author: str
    isbn: str | None
    publisher: str | None
    published_year: int | None
    category: str | None
    description: str | None
    total_copies: int
    available_copies: int

    @classmethod
    def from_entity(cls, book: Book) -> BookOut:
        return cls(
            id=str(book.id),
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            publisher=book.publisher,
            published_year=book.published_year,
            category=book.category,
            description=book.description,
            total_copies=book.total_copies,
            available_copies=book.available_copies,
        )


class CopyOut(BaseModel):
    id: str
    book_id: str
    barcode: str
    condition: str
    status: str

    @classmethod
    def from_entity(cls, copy: BookCopy) -> CopyOut:
        return cls(
            id=str(copy.id),
            book_id=str(copy.book_id),
            barcode=copy.barcode,
            condition=copy.condition.value,
            status=copy.status.value,
        )


class PageOut(BaseModel):
    limit: int
    offset: int
    total: int


class BookListOut(BaseModel):
    items: list[BookOut]
    page: PageOut
