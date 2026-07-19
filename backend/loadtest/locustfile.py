"""Locust load test — a read-heavy library staff workload.

One shared staff login is performed at test start (real staff stay logged in); every virtual
user then exercises the authenticated read endpoints plus health. Run against a running API:

  # 1. Start the API (no reload, a couple of workers):
  #    uvicorn library.main:app --port 8000 --workers 2
  # 2. Run 500 users for 30s, headless:
  #    locust -f loadtest/locustfile.py --headless -u 500 -r 100 -t 30s \
  #           --host http://localhost:8000 --csv loadtest/report
"""

from __future__ import annotations

import os

import requests
from locust import FastHttpUser, between, events, task

EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@12345")
_TOKEN: dict[str, str] = {}


@events.test_start.add_listener
def _login(environment, **_: object) -> None:
    host = environment.host or "http://localhost:8000"
    resp = requests.post(
        f"{host}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=10
    )
    resp.raise_for_status()
    _TOKEN["value"] = resp.json()["access_token"]


class LibraryStaff(FastHttpUser):
    wait_time = between(0.1, 0.5)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {_TOKEN.get('value', '')}"}

    @task(5)
    def list_books(self) -> None:
        self.client.get("/books?limit=20", headers=self._headers(), name="GET /books")

    @task(3)
    def search_books(self) -> None:
        self.client.get(
            "/books?search=code&limit=20", headers=self._headers(), name="GET /books?search"
        )

    @task(2)
    def list_members(self) -> None:
        self.client.get("/members?limit=20", headers=self._headers(), name="GET /members")

    @task(2)
    def list_active_loans(self) -> None:
        self.client.get(
            "/loans?active_only=true&limit=20", headers=self._headers(), name="GET /loans"
        )

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
