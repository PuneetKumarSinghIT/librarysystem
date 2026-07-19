"""Domain enumerations shared across layers."""

from __future__ import annotations

from enum import StrEnum


class StaffRole(StrEnum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"


class MemberStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class CopyCondition(StrEnum):
    NEW = "new"
    GOOD = "good"
    WORN = "worn"
    DAMAGED = "damaged"


class CopyStatus(StrEnum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    LOST = "lost"
    MAINTENANCE = "maintenance"


class LoanStatus(StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class FineStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    WAIVED = "waived"
