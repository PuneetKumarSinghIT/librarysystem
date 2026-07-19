"""Pagination helpers shared by list use-cases."""

from __future__ import annotations

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def clamp_page(limit: int | None, offset: int | None) -> tuple[int, int]:
    """Clamp limit to [1, MAX_LIMIT] (default DEFAULT_LIMIT) and offset to >= 0.

    Prevents unbounded/negative queries that could exhaust memory or scrape data.
    """
    effective_limit = limit if limit and limit > 0 else DEFAULT_LIMIT
    effective_limit = min(effective_limit, MAX_LIMIT)
    effective_offset = max(0, offset or 0)
    return effective_limit, effective_offset
