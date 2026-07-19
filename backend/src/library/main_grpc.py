"""gRPC server entrypoint (composition root for the gRPC transport).

Servicers are registered here as they are built (F2/F3+). Run: python -m library.main_grpc
"""

from __future__ import annotations

import asyncio

import grpc

from library.config import get_settings
from library.config.logging import configure_logging, get_logger

log = get_logger("grpc")


async def serve() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.is_production)

    server = grpc.aio.server()
    # Servicers registered here as features land (F2/F3+):
    # library_pb2_grpc.add_BookServiceServicer_to_server(BookServicer(...), server)

    listen_addr = f"0.0.0.0:{settings.grpc_port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    log.info("grpc.started", address=listen_addr)
    await server.wait_for_termination()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
