"""FastAPI application factory for the REST controller."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from library import __version__
from library.adapter.db.engine import get_engine
from library.adapter.security.password_hasher import Argon2PasswordHasher
from library.adapter.security.token_codec import JwtAccessTokenCodec
from library.config import get_settings
from library.config.logging import configure_logging
from library.controller.rest.errors import register_exception_handlers
from library.controller.rest.middleware import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from library.controller.rest.routers import auth, books, loans, members


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.is_production)

    app = FastAPI(
        title="Neighborhood Library Service",
        version=__version__,
        description="REST gateway over the library domain (shares the service layer with gRPC).",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # CORS locked to the configured frontend origin(s).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    # Composition root: build shared security adapters once and expose via app.state.
    app.state.hasher = Argon2PasswordHasher(time_cost=settings.argon2_time_cost)
    app.state.token_codec = JwtAccessTokenCodec(
        secret=settings.jwt_secret, ttl_seconds=settings.jwt_access_ttl_seconds
    )

    @app.get("/health", tags=["system"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/ready", tags=["system"], summary="Readiness probe (checks DB)")
    async def ready() -> dict[str, str]:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}

    # Feature routers.
    app.include_router(auth.router)
    app.include_router(books.router)
    app.include_router(members.router)
    app.include_router(loans.router)

    return app
