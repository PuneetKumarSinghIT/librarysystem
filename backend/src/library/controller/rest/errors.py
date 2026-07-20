"""Map all errors to a consistent JSON envelope — one place owns the mapping (SRP).

Envelope: {"error": {"code": str, "message": str, "details": dict}}

Handlers (Starlette picks the most specific by the exception's MRO):
  - DomainError            -> mapped business status (404/409/400/401/403)
  - RequestValidationError -> 422 validation_error
  - HTTPException          -> its status code, wrapped in the envelope (404/405/...)
  - Exception (catch-all)  -> 500 internal_error; the real error is logged server-side
                              with the request id, and never leaked to the client.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from library.core.errors import (
    AlreadyExistsError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    UnauthenticatedError,
    ValidationError,
)

log = structlog.get_logger("errors")

# Domain error type -> HTTP status code.
_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    AlreadyExistsError: 409,
    ValidationError: 400,
    ConflictError: 409,
    UnauthenticatedError: 401,
    PermissionDeniedError: 403,
}

# HTTP status code -> stable machine-readable error code (for HTTPException responses).
_HTTP_CODE: dict[int, str] = {
    400: "bad_request",
    401: "unauthenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
}


def _status_for(exc: DomainError) -> int:
    for exc_type, status in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status
    return 500


def _request_id(request: Request) -> str | None:
    rid = getattr(request.state, "request_id", None)
    if rid:
        return rid
    return structlog.contextvars.get_contextvars().get("request_id")


def _envelope(
    request: Request,
    *,
    status: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    payload_details = dict(details or {})
    rid = _request_id(request)
    if rid:
        payload_details.setdefault("request_id", rid)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": payload_details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain(request: Request, exc: DomainError) -> JSONResponse:
        return _envelope(
            request,
            status=_status_for(exc),
            code=exc.code,
            message=exc.message,
            details=dict(exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _envelope(
            request,
            status=422,
            code="validation_error",
            message="Request validation failed",
            details={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return _envelope(
            request,
            status=exc.status_code,
            code=_HTTP_CODE.get(exc.status_code, "http_error"),
            message=message,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log the real error (with traceback) server-side, tagged with the request id.
        # NEVER return the exception text/stack to the client.
        log.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
            exc_info=exc,
        )
        return _envelope(
            request,
            status=500,
            code="internal_error",
            message="An unexpected error occurred. Please try again or contact support.",
        )
