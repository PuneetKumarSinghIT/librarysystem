"""Unit tests for BookService — validation, uniqueness, not-found, pagination, copies."""

from __future__ import annotations

import uuid

import pytest

from library.core.commands import BookCreate
from library.core.enums import CopyCondition
from library.core.errors import AlreadyExistsError, NotFoundError, ValidationError


def _valid(**overrides) -> BookCreate:
    base = {"title": "Clean Code", "author": "Robert C. Martin"}
    base.update(overrides)
    return BookCreate(**base)


# ── create ───────────────────────────────────────────────────────────────────
async def test_create_book_success(book_service):
    book = await book_service.create_book(_valid(isbn="978-0132350884"))
    assert book.title == "Clean Code"
    assert book.isbn == "9780132350884"  # normalized: hyphens stripped
    assert book.total_copies == 0


async def test_create_trims_whitespace(book_service):
    book = await book_service.create_book(_valid(title="  Refactoring  "))
    assert book.title == "Refactoring"


@pytest.mark.parametrize("field", ["title", "author"])
async def test_create_requires_text_fields(book_service, field):
    with pytest.raises(ValidationError):
        await book_service.create_book(_valid(**{field: "   "}))


async def test_create_rejects_bad_year(book_service):
    with pytest.raises(ValidationError):
        await book_service.create_book(_valid(published_year=999))


async def test_create_rejects_bad_isbn(book_service):
    with pytest.raises(ValidationError):
        await book_service.create_book(_valid(isbn="123"))


async def test_create_duplicate_isbn_raises(book_service):
    await book_service.create_book(_valid(isbn="9780132350884"))
    with pytest.raises(AlreadyExistsError):
        await book_service.create_book(_valid(title="Dup", isbn="9780132350884"))


# ── get / update ──────────────────────────────────────────────────────────────
async def test_get_missing_raises(book_service):
    with pytest.raises(NotFoundError):
        await book_service.get_book(uuid.uuid4())


async def test_update_success(book_service):
    book = await book_service.create_book(_valid())
    updated = await book_service.update_book(book.id, {"category": "Software"})
    assert updated.category == "Software"


async def test_update_unknown_field_raises(book_service):
    book = await book_service.create_book(_valid())
    with pytest.raises(ValidationError):
        await book_service.update_book(book.id, {"bogus": "x"})


async def test_update_missing_book_raises(book_service):
    with pytest.raises(NotFoundError):
        await book_service.update_book(uuid.uuid4(), {"title": "X"})


async def test_update_blank_title_raises(book_service):
    book = await book_service.create_book(_valid())
    with pytest.raises(ValidationError):
        await book_service.update_book(book.id, {"title": "  "})


# ── list ─────────────────────────────────────────────────────────────────────
async def test_list_search_and_pagination(book_service):
    await book_service.create_book(_valid(title="Python 101", author="A"))
    await book_service.create_book(_valid(title="Rust Book", author="B"))
    await book_service.create_book(_valid(title="Python 202", author="C"))

    items, total = await book_service.list_books("python", limit=1, offset=0)
    assert total == 2
    assert len(items) == 1  # limited


async def test_list_clamps_excessive_limit(book_service):
    items, total = await book_service.list_books(None, limit=9999, offset=-5)
    assert total == 0
    assert items == []


# ── copies ───────────────────────────────────────────────────────────────────
async def test_add_copy_success(book_service):
    book = await book_service.create_book(_valid())
    copy = await book_service.add_copy(book.id, "BC-001", CopyCondition.NEW)
    assert copy.barcode == "BC-001"
    assert copy.condition == CopyCondition.NEW


async def test_add_copy_to_missing_book_raises(book_service):
    with pytest.raises(NotFoundError):
        await book_service.add_copy(uuid.uuid4(), "BC-001", None)


async def test_add_copy_blank_barcode_raises(book_service):
    book = await book_service.create_book(_valid())
    with pytest.raises(ValidationError):
        await book_service.add_copy(book.id, "   ", None)


async def test_add_copy_duplicate_barcode_raises(book_service):
    book = await book_service.create_book(_valid())
    await book_service.add_copy(book.id, "BC-DUP", None)
    with pytest.raises(AlreadyExistsError):
        await book_service.add_copy(book.id, "BC-DUP", None)


async def test_list_copies_missing_book_raises(book_service):
    with pytest.raises(NotFoundError):
        await book_service.list_copies(uuid.uuid4())
