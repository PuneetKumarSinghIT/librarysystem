"""Input command objects for service use-cases (framework-free)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BookCreate:
    title: str
    author: str
    isbn: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    category: str | None = None
    description: str | None = None


@dataclass(slots=True)
class MemberCreate:
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    address: str | None = None
