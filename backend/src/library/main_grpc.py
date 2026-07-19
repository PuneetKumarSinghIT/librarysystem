"""gRPC server entrypoint (composition root for the gRPC transport).

Servicers are registered here as they are built (F2/F3+). Run: python -m library.main_grpc
"""

from __future__ import annotations

import asyncio

import grpc

from library.adapter.db.engine import get_sessionmaker
from library.adapter.security.password_hasher import Argon2PasswordHasher
from library.adapter.security.token_codec import JwtAccessTokenCodec
from library.config import get_settings
from library.config.logging import configure_logging, get_logger
from library.controller.grpc.auth_servicer import AuthServicer
from library.controller.grpc.book_servicer import BookServicer
from library.controller.grpc.loan_servicer import LoanServicer
from library.controller.grpc.member_servicer import MemberServicer
from library.v1 import (
    auth_pb2_grpc,
    books_pb2_grpc,
    loans_pb2_grpc,
    members_pb2_grpc,
)

log = get_logger("grpc")


async def serve() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.is_production)

    # Composition root for the gRPC transport: build shared adapters once.
    sessionmaker = get_sessionmaker()
    hasher = Argon2PasswordHasher(time_cost=settings.argon2_time_cost)
    token_codec = JwtAccessTokenCodec(
        secret=settings.jwt_secret, ttl_seconds=settings.jwt_access_ttl_seconds
    )

    server = grpc.aio.server()
    auth_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServicer(sessionmaker, hasher, token_codec, settings.jwt_refresh_ttl_seconds),
        server,
    )
    books_pb2_grpc.add_BookServiceServicer_to_server(
        BookServicer(sessionmaker, token_codec), server
    )
    members_pb2_grpc.add_MemberServiceServicer_to_server(
        MemberServicer(sessionmaker, token_codec), server
    )
    loans_pb2_grpc.add_LoanServiceServicer_to_server(
        LoanServicer(sessionmaker, token_codec), server
    )

    listen_addr = f"0.0.0.0:{settings.grpc_port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    log.info("grpc.started", address=listen_addr)
    await server.wait_for_termination()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
