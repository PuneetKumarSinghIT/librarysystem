"""Map domain errors to HTTP responses with a consistent error envelope.

Single place that knows the DomainError -> HTTP status mapping (SRP).
Envelope: {"error": {"code": str, "message": str, "details": dict}}
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from library.core.errors import (
    AlreadyExistsError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    UnauthenticatedError,
    ValidationError,
)

# Domain error type -> HTTP status code.
_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    AlreadyExistsError: 409,
    ValidationError: 400,
    ConflictError: 409,
    UnauthenticatedError: 401,
    PermissionDeniedError: 403,
}


def _status_for(exc: DomainError) -> int:
    for exc_type, status in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status
    return 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        status = _status_for(exc)
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
