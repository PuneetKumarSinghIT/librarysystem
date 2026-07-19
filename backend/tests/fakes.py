"""In-memory fake adapters implementing the core ports.

These let us unit-test services with zero I/O — the whole point of depending on ports
(Dependency Inversion). They are Liskov-substitutable for the real Postgres/argon2 adapters.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from library.core.commands import BookCreate, MemberCreate
from library.core.entities import (
    Book,
    BookCopy,
    CopyRef,
    Loan,
    LoanRef,
    Member,
    RefreshTokenRecord,
    Staff,
)
from library.core.enums import CopyCondition, CopyStatus, LoanStatus, MemberStatus
from library.core.errors import AlreadyExistsError, ConflictError
from library.utils.clock import utcnow


class FakeStaffRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, Staff] = {}
        self._by_email: dict[str, Staff] = {}
        self.touched: list[uuid.UUID] = []

    def add(self, staff: Staff) -> None:
        self._by_id[staff.id] = staff
        self._by_email[staff.email.lower().strip()] = staff

    async def get_by_email(self, email: str) -> Staff | None:
        return self._by_email.get(email.lower().strip())

    async def get_by_id(self, staff_id: uuid.UUID) -> Staff | None:
        return self._by_id.get(staff_id)

    async def touch_last_login(self, staff_id: uuid.UUID) -> None:
        self.touched.append(staff_id)


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._records: dict[str, RefreshTokenRecord] = {}

    async def add(
        self, staff_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> None:
        self._records[token_hash] = RefreshTokenRecord(
            id=uuid.uuid4(),
            staff_id=staff_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def get_by_hash(self, token_hash: str) -> RefreshTokenRecord | None:
        return self._records.get(token_hash)

    async def revoke(self, token_hash: str) -> None:
        record = self._records.get(token_hash)
        if record and record.revoked_at is None:
            record.revoked_at = utcnow()

    async def revoke_all_for_staff(self, staff_id: uuid.UUID) -> None:
        for record in self._records.values():
            if record.staff_id == staff_id and record.revoked_at is None:
                record.revoked_at = utcnow()

    # Test helpers
    def active_count(self) -> int:
        return sum(1 for r in self._records.values() if r.revoked_at is None)


class FakePasswordHasher:
    """Deterministic, fast stand-in for argon2 (unit tests only)."""

    def hash(self, plain: str) -> str:
        return f"hashed::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed::{plain}"


class FakeBookRepository:
    """In-memory BookRepository. Enforces ISBN/barcode uniqueness like the real DB."""

    def __init__(self) -> None:
        self.books: dict[uuid.UUID, Book] = {}
        self.copies: dict[uuid.UUID, list[BookCopy]] = {}

    def _isbn_taken(self, isbn: str, exclude: uuid.UUID | None = None) -> bool:
        return any(b.isbn == isbn and b.id != exclude for b in self.books.values())

    async def create(self, data: BookCreate) -> Book:
        if data.isbn and self._isbn_taken(data.isbn):
            raise AlreadyExistsError("A book with this ISBN already exists")
        book = Book(
            id=uuid.uuid4(),
            title=data.title,
            author=data.author,
            isbn=data.isbn,
            publisher=data.publisher,
            published_year=data.published_year,
            category=data.category,
            description=data.description,
        )
        self.books[book.id] = book
        return book

    async def update(self, book_id, changes):
        book = self.books.get(book_id)
        if book is None:
            return None
        if changes.get("isbn") and self._isbn_taken(changes["isbn"], exclude=book_id):
            raise AlreadyExistsError("A book with this ISBN already exists")
        for key, value in changes.items():
            setattr(book, key, value)
        return book

    async def get(self, book_id):
        return self.books.get(book_id)

    async def list(self, search, limit, offset):
        items = list(self.books.values())
        if search:
            term = search.lower()
            items = [
                b for b in items if term in b.title.lower() or term in b.author.lower()
            ]
        items.sort(key=lambda b: b.title)
        return items[offset : offset + limit], len(items)

    async def book_exists(self, book_id) -> bool:
        return book_id in self.books

    async def add_copy(self, book_id, barcode, condition) -> BookCopy:
        if any(c.barcode == barcode for cl in self.copies.values() for c in cl):
            raise AlreadyExistsError("A copy with this barcode already exists")
        copy = BookCopy(
            id=uuid.uuid4(),
            book_id=book_id,
            barcode=barcode,
            condition=condition or CopyCondition.GOOD,
            status=CopyStatus.AVAILABLE,
        )
        self.copies.setdefault(book_id, []).append(copy)
        return copy

    async def list_copies(self, book_id) -> list[BookCopy]:
        return list(self.copies.get(book_id, []))


class FakeMemberRepository:
    """In-memory MemberRepository. Enforces email uniqueness; supports soft delete."""

    def __init__(self) -> None:
        self.members: dict[uuid.UUID, Member] = {}

    def _email_taken(self, email: str, exclude: uuid.UUID | None = None) -> bool:
        return any(m.email == email and m.id != exclude for m in self.members.values())

    async def create(self, data: MemberCreate) -> Member:
        if self._email_taken(data.email):
            raise AlreadyExistsError("A member with this email already exists")
        member = Member(
            id=uuid.uuid4(),
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            status=MemberStatus.ACTIVE,
            phone=data.phone,
            address=data.address,
        )
        self.members[member.id] = member
        return member

    async def update(self, member_id, changes):
        member = self.members.get(member_id)
        if member is None:
            return None
        if changes.get("email") and self._email_taken(changes["email"], exclude=member_id):
            raise AlreadyExistsError("A member with this email already exists")
        for key, value in changes.items():
            setattr(member, key, value)
        return member

    async def get(self, member_id):
        return self.members.get(member_id)

    async def list(self, search, limit, offset):
        items = list(self.members.values())
        if search:
            term = search.lower()
            items = [
                m
                for m in items
                if term in m.first_name.lower()
                or term in m.last_name.lower()
                or term in m.email.lower()
            ]
        items.sort(key=lambda m: (m.last_name, m.first_name))
        return items[offset : offset + limit], len(items)

    async def soft_delete(self, member_id) -> bool:
        return self.members.pop(member_id, None) is not None


class FakeLoanRepository:
    """In-memory LoanRepository. Enforces one active loan per copy (like the DB index)."""

    def __init__(self) -> None:
        self.copies: dict[uuid.UUID, dict] = {}
        self.loans: dict[uuid.UUID, dict] = {}
        self.fines: list[dict] = []
        self.members: dict[uuid.UUID, str] = {}

    def add_copy(
        self,
        *,
        book_id: uuid.UUID | None = None,
        status: CopyStatus = CopyStatus.AVAILABLE,
        barcode: str = "BC-001",
        title: str = "Some Book",
    ) -> uuid.UUID:
        copy_id = uuid.uuid4()
        self.copies[copy_id] = {
            "book_id": book_id or uuid.uuid4(),
            "status": status,
            "barcode": barcode,
            "title": title,
        }
        return copy_id

    def register_member(self, member_id: uuid.UUID, name: str = "Ada Lovelace") -> None:
        self.members[member_id] = name

    async def lock_copy(self, copy_id):
        c = self.copies.get(copy_id)
        return CopyRef(id=copy_id, book_id=c["book_id"], status=c["status"]) if c else None

    async def lock_available_copy_for_book(self, book_id):
        for cid, c in self.copies.items():
            if c["book_id"] == book_id and c["status"] == CopyStatus.AVAILABLE:
                return CopyRef(id=cid, book_id=book_id, status=c["status"])
        return None

    async def create_loan(self, copy_id, member_id, staff_id, borrowed_at, due_at):
        if any(
            loan["copy_id"] == copy_id and loan["returned_at"] is None
            for loan in self.loans.values()
        ):
            raise ConflictError("This copy is already checked out")
        loan_id = uuid.uuid4()
        self.loans[loan_id] = {
            "copy_id": copy_id,
            "member_id": member_id,
            "staff_id": staff_id,
            "borrowed_at": borrowed_at,
            "due_at": due_at,
            "returned_at": None,
            "status": LoanStatus.ACTIVE,
            "renewed_count": 0,
        }
        self.copies[copy_id]["status"] = CopyStatus.BORROWED
        return loan_id

    async def get_loan_ref(self, loan_id):
        loan = self.loans.get(loan_id)
        if loan is None:
            return None
        return LoanRef(
            id=loan_id,
            copy_id=loan["copy_id"],
            member_id=loan["member_id"],
            due_at=loan["due_at"],
            returned_at=loan["returned_at"],
        )

    async def close_loan(self, loan_id, returned_at):
        loan = self.loans[loan_id]
        loan["returned_at"] = returned_at
        loan["status"] = LoanStatus.RETURNED
        self.copies[loan["copy_id"]]["status"] = CopyStatus.AVAILABLE

    async def create_fine(self, loan_id, member_id, amount, reason, assessed_at):
        self.fines.append(
            {
                "loan_id": loan_id,
                "member_id": member_id,
                "amount": Decimal(amount),
                "reason": reason,
            }
        )

    async def get_loan_view(self, loan_id):
        loan = self.loans.get(loan_id)
        if loan is None:
            return None
        copy = self.copies[loan["copy_id"]]
        status = (
            LoanStatus.RETURNED
            if loan["returned_at"]
            else (LoanStatus.OVERDUE if loan["due_at"] < utcnow() else LoanStatus.ACTIVE)
        )
        return Loan(
            id=loan_id,
            copy_id=loan["copy_id"],
            book_id=copy["book_id"],
            book_title=copy["title"],
            barcode=copy["barcode"],
            member_id=loan["member_id"],
            member_name=self.members.get(loan["member_id"], "Unknown"),
            borrowed_at=loan["borrowed_at"],
            due_at=loan["due_at"],
            returned_at=loan["returned_at"],
            status=status,
            staff_id=loan["staff_id"],
            renewed_count=loan["renewed_count"],
        )

    async def list_loans(self, member_id, active_only, overdue_only, now, limit, offset):
        matches = []
        for loan_id, loan in self.loans.items():
            if member_id and loan["member_id"] != member_id:
                continue
            if (active_only or overdue_only) and loan["returned_at"] is not None:
                continue
            if overdue_only and not loan["due_at"] < now:
                continue
            matches.append(loan_id)
        total = len(matches)
        views = [await self.get_loan_view(lid) for lid in matches[offset : offset + limit]]
        return views, total
