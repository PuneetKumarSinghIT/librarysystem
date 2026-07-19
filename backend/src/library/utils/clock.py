"""Time helpers. Centralized so time can be reasoned about (and faked in tests)."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware current UTC time."""
    return datetime.now(UTC)
