"""Composition root and REST entrypoint.

This is the ONLY place that wires concrete adapters into services (Dependency Injection).
Feature wiring is added here as services/adapters are built (F3+).

Run (dev):  uvicorn library.main:app --reload --port 8000
Or:         python -m library.main
"""

from __future__ import annotations

import uvicorn

from library.config import get_settings
from library.controller.rest.app import create_app

# ASGI application object (used by uvicorn: `library.main:app`).
app = create_app()

__all__ = ["app", "main"]


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "library.main:app",
        host="0.0.0.0",
        port=settings.rest_port,
        reload=not settings.is_production,
    )


if __name__ == "__main__":
    main()
