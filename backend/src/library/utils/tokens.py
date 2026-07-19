"""Opaque refresh-token generation and hashing.

The refresh token itself is a high-entropy random string given to the client. Only its
SHA-256 hash is stored, so a database leak does not expose usable tokens.
"""

from __future__ import annotations

import hashlib
import secrets


def generate_refresh_token() -> str:
    """Return a new cryptographically-random, URL-safe refresh token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Deterministic SHA-256 hex digest used to look up / store a refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
