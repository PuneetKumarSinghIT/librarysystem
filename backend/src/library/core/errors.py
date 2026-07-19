"""Domain error hierarchy.

Controllers (REST / gRPC) map these to HTTP / gRPC status codes in ONE place, so business
code never imports transport concepts. (Single Responsibility + Dependency Inversion.)
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all expected business errors."""

    code: str = "domain_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = "not_found"


class AlreadyExistsError(DomainError):
    """Unique-constraint / duplicate resource (e.g. email, ISBN, barcode)."""

    code = "already_exists"


class ValidationError(DomainError):
    code = "validation_error"


class ConflictError(DomainError):
    """State precondition failed — e.g. borrowing an already-checked-out copy."""

    code = "conflict"


class UnauthenticatedError(DomainError):
    code = "unauthenticated"


class PermissionDeniedError(DomainError):
    code = "permission_denied"
