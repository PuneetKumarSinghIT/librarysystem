"""Shared base for authenticated gRPC servicers (session + auth + error mapping)."""

from __future__ import annotations

import grpc
from sqlalchemy.ext.asyncio import async_sessionmaker

from library.core.entities import AccessClaims
from library.core.errors import UnauthenticatedError
from library.core.ports.security import AccessTokenCodec


class AuthenticatedServicer:
    """Base providing a sessionmaker and Bearer-token authentication for RPC methods."""

    def __init__(
        self, sessionmaker: async_sessionmaker, token_codec: AccessTokenCodec
    ) -> None:
        self._sessionmaker = sessionmaker
        self._codec = token_codec

    async def _authenticate(self, context: grpc.aio.ServicerContext) -> AccessClaims:
        metadata = dict(context.invocation_metadata() or ())
        header = metadata.get("authorization", "")
        if not header.startswith("Bearer "):
            await context.abort(
                grpc.StatusCode.UNAUTHENTICATED, "Missing or malformed Authorization metadata"
            )
        try:
            return self._codec.decode(header.removeprefix("Bearer ").strip())
        except UnauthenticatedError:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token")
