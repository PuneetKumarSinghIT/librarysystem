"""Rate limiting (brute-force protection) via slowapi, keyed by client IP."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from library.config import get_settings

limiter = Limiter(key_func=get_remote_address)


def login_rate_limit() -> str:
    """Per-IP limit for the login endpoint (configurable via env)."""
    return f"{get_settings().rate_limit_login_per_minute}/minute"
