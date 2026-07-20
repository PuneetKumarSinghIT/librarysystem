"""Tests for the REST error handlers — consistent envelope for every error type."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from library.controller.rest.errors import register_exception_handlers
from library.core.errors import ConflictError, NotFoundError


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    class Body(BaseModel):
        name: str

    @app.get("/boom")
    async def boom():
        # An unexpected, unhandled error (e.g. a bug) — must not crash the contract.
        raise ValueError("secret internal detail: db password leaked")

    @app.get("/missing")
    async def missing():
        raise NotFoundError("Book not found")

    @app.get("/conflict")
    async def conflict():
        raise ConflictError("This copy is already checked out")

    @app.post("/validate")
    async def validate(body: Body):
        return {"ok": body.name}

    # raise_server_exceptions=False so the 500 handler's response is returned to us.
    return TestClient(app, raise_server_exceptions=False)


def _error(resp) -> dict:
    body = resp.json()
    assert "error" in body, body
    assert {"code", "message", "details"} <= set(body["error"]), body
    return body["error"]


def test_unhandled_exception_returns_500_envelope(client: TestClient):
    resp = client.get("/boom")
    assert resp.status_code == 500
    err = _error(resp)
    assert err["code"] == "internal_error"


def test_unhandled_exception_does_not_leak_internals(client: TestClient):
    resp = client.get("/boom")
    # The generic message must not expose the underlying exception text.
    assert "secret internal detail" not in resp.text
    assert "db password" not in resp.text


def test_domain_not_found_maps_to_404_envelope(client: TestClient):
    resp = client.get("/missing")
    assert resp.status_code == 404
    err = _error(resp)
    assert err["code"] == "not_found"
    assert err["message"] == "Book not found"


def test_domain_conflict_maps_to_409_envelope(client: TestClient):
    resp = client.get("/conflict")
    assert resp.status_code == 409
    assert _error(resp)["code"] == "conflict"


def test_request_validation_returns_envelope(client: TestClient):
    resp = client.post("/validate", json={})  # missing required "name"
    assert resp.status_code == 422
    err = _error(resp)
    assert err["code"] == "validation_error"
    assert "errors" in err["details"]


def test_unknown_route_returns_envelope(client: TestClient):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert _error(resp)["code"] == "not_found"


def test_method_not_allowed_returns_envelope(client: TestClient):
    resp = client.post("/missing")  # /missing only allows GET
    assert resp.status_code == 405
    assert _error(resp)["code"] == "method_not_allowed"
