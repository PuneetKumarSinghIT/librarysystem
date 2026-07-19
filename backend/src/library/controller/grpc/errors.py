"""Map domain errors to gRPC status codes (single place — mirrors the REST mapping)."""

from __future__ import annotations

import grpc

from library.core.errors import (
    AlreadyExistsError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    UnauthenticatedError,
    ValidationError,
)

_STATUS_MAP: dict[type[DomainError], grpc.StatusCode] = {
    NotFoundError: grpc.StatusCode.NOT_FOUND,
    AlreadyExistsError: grpc.StatusCode.ALREADY_EXISTS,
    ValidationError: grpc.StatusCode.INVALID_ARGUMENT,
    ConflictError: grpc.StatusCode.FAILED_PRECONDITION,
    UnauthenticatedError: grpc.StatusCode.UNAUTHENTICATED,
    PermissionDeniedError: grpc.StatusCode.PERMISSION_DENIED,
}


def grpc_status_for(exc: DomainError) -> grpc.StatusCode:
    for exc_type, code in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return code
    return grpc.StatusCode.INTERNAL
