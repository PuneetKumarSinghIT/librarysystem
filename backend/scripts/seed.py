"""Seed the database with sample catalog + members for local development/testing.

Idempotent: does nothing if books already exist. Staff/admin accounts are seeded in F3
(they require the password hasher). Run:  python -m scripts.seed
"""

from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import func, select

from library.adapter.db.engine import get_sessionmaker
from library.core.enums import CopyCondition, CopyStatus, MemberStatus
from library.models import Book, BookCopy, Member

# (title, author, isbn, category, num_copies)
_BOOKS = [
    ("The Pragmatic Programmer", "Andrew Hunt", "9780201616224", "Software", 3),
    ("Clean Code", "Robert C. Martin", "9780132350884", "Software", 2),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "9781449373320", "Software", 2),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", "History", 2),
    ("The Midnight Library", "Matt Haig", "9780525559474", "Fiction", 4),
]

# (first, last, email, phone)
_MEMBERS = [
    ("Ada", "Lovelace", "ada@example.com", "+1-555-0101"),
    ("Alan", "Turing", "alan@example.com", "+1-555-0102"),
    ("Grace", "Hopper", "grace@example.com", "+1-555-0103"),
]


async def seed() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        existing = await session.scalar(select(func.count()).select_from(Book))
        if existing:
            print(f"Seed skipped: {existing} books already present.")
            return

        for i, (title, author, isbn, category, n_copies) in enumerate(_BOOKS, start=1):
            book = Book(title=title, author=author, isbn=isbn, category=category)
            for c in range(1, n_copies + 1):
                book.copies.append(
                    BookCopy(
                        barcode=f"BC-{i:03d}-{c:02d}",
                        condition=CopyCondition.GOOD,
                        status=CopyStatus.AVAILABLE,
                        acquired_on=date(2024, 1, 1),
                    )
                )
            session.add(book)

        for first, last, email, phone in _MEMBERS:
            session.add(
                Member(
                    first_name=first,
                    last_name=last,
                    email=email,
                    phone=phone,
                    status=MemberStatus.ACTIVE,
                )
            )

        await session.commit()

    n_copies = sum(b[4] for b in _BOOKS)
    print(f"Seeded {len(_BOOKS)} books ({n_copies} copies) and {len(_MEMBERS)} members.")


if __name__ == "__main__":
    asyncio.run(seed())
