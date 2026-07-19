"""Sample gRPC client — logs in, then lists books using the access token as metadata.

Run the gRPC server first:  python -m library.main_grpc
Then:                       python -m scripts.grpc_client
"""

from __future__ import annotations

import asyncio
import os

import grpc

from library.v1 import auth_pb2, auth_pb2_grpc, books_pb2, books_pb2_grpc, common_pb2

TARGET = os.getenv("GRPC_TARGET", "localhost:50051")
EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@12345")


async def main() -> None:
    async with grpc.aio.insecure_channel(TARGET) as channel:
        auth = auth_pb2_grpc.AuthServiceStub(channel)
        tokens = await auth.Login(auth_pb2.LoginRequest(email=EMAIL, password=PASSWORD))
        print(f"Logged in as {tokens.staff.email} (role={tokens.staff.role})")

        metadata = (("authorization", f"Bearer {tokens.access_token}"),)
        books = books_pb2_grpc.BookServiceStub(channel)
        resp = await books.ListBooks(
            books_pb2.ListBooksRequest(page=common_pb2.PageParams(limit=5)), metadata=metadata
        )
        print(f"{resp.page.total} book(s) in catalog. First page:")
        for book in resp.books:
            print(f"  - {book.title} by {book.author} "
                  f"({book.available_copies}/{book.total_copies} available)")


if __name__ == "__main__":
    asyncio.run(main())
