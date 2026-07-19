# Load Test — 500 Concurrent Users

Stress test of the REST API under **500 concurrent virtual users** using
[Locust](https://locust.io) (`FastHttpUser`). The workload is read-heavy (the typical library
staff pattern): listing/searching books, listing members, and listing active loans, plus a
no-DB health check. One shared staff login is performed at test start.

Reproduce:

```bash
# 1. Start the API with multiple workers (no reload):
DB_MAX_OVERFLOW=10 uvicorn library.main:app --port 8000 --workers 4
# 2. Run the test:
locust -f loadtest/locustfile.py --headless -u 500 -r 50 -t 30s \
       --host http://localhost:8000 --csv loadtest/report
```

## Environment

| Item | Value |
|------|-------|
| Machine | Single laptop (Windows 11), Postgres 16 in Docker |
| App server | Uvicorn, **4 workers**, async SQLAlchemy + asyncpg |
| DB pool | 10 base + 10 overflow per worker → **80 connections** total (< Postgres max 100) |
| Users | **500** concurrent, ramp 50/s, 30s steady window |

## Results (4 workers)

| Endpoint | Requests | Failures | p50 | p95 | p99 | Max |
|----------|---------:|---------:|----:|----:|----:|----:|
| GET /books | 1671 | 0 | 1.8 s | 6.4 s | 10 s | 20.3 s |
| GET /books?search | 958 | 0 | 1.8 s | 6.2 s | 8.6 s | 15.7 s |
| GET /members | 625 | 0 | 1.9 s | 5.8 s | 8.6 s | 16.8 s |
| GET /loans | 638 | 0 | 1.8 s | 6.5 s | 11 s | 14.2 s |
| GET /health (no DB) | 333 | 0 | **0.2 s** | 2.4 s | 2.7 s | 2.8 s |
| **Aggregated** | **4225** | **0 (0.00%)** | **1.6 s** | **6.0 s** | **10 s** | 20.3 s |

- **Throughput:** ~142 requests/second sustained.
- **Error rate:** **0.00%** — every request under 500 concurrent users succeeded.

## Interpretation

- **The app layer is fast.** `GET /health` (no database) holds a **p50 of 200 ms** even under
  full 500-user load — JWT verification, routing, and serialization are cheap.
- **The bottleneck is the database connection pool.** 500 users share 80 pooled connections, so
  DB-backed requests queue for a connection, which is why their p50 sits near ~1.8 s. This is
  expected and is the correct place to scale.
- **Multiple workers matter.** An earlier single-worker run saturated one event loop + a
  30-connection pool and produced ~4% `ConnectionRefused` errors and a p50 of ~4.2 s. Moving to
  4 workers eliminated all errors and roughly halved p50 — evidence the stateless app tier
  scales horizontally.

## How to go faster (scaling path)

1. **Connection pooling at scale:** put **pgBouncer** in front of Postgres and raise pool sizes;
   this lets far more app workers share a bounded set of DB connections.
2. **Scale the stateless app tier:** more Uvicorn workers / more replicas behind a load balancer
   (the app holds no session state — JWT + DB only).
3. **Give Postgres more resources / read replicas:** the read-heavy workload distributes well
   across replicas; writes stay on primary.
4. **Cache hot reads:** a Redis read-through cache + HTTP `ETag`s on the catalog would remove the
   most frequent queries (`GET /books`) from the DB entirely.
5. **Right-size the pool per worker** to `cores × 2`-ish and keep `workers × pool ≤ Postgres
   max_connections`.

_Numbers are from one laptop run and are meant as an honest baseline + bottleneck analysis, not
a peak-hardware benchmark._
