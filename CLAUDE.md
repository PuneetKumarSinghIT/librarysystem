# CLAUDE.md — Neighborhood Library Service

> **Purpose of this file.** This is the single source of truth for building the Neighborhood
> Library Service. It captures the architecture, database design, security posture, DevOps
> setup, conventions, and the feature-by-feature roadmap. Read it at the start of every
> session. When we build a feature, follow the **Working Protocol** below and update the
> **Decision Log** and **Roadmap** as we go — so we never re-explain the task twice.

---

## 0. Current Status — RESUME HERE

> Updated after every phase/subtask so work can resume without the full chat history.

**Last updated:** 2026-07-19

**Done:** F0 (scaffold) ✅ · F1 (database) ✅
**In progress:** — (F1 just completed)
**Next up:** F2 (proto contract) → F3 (auth). **Milestone target:** "login works end-to-end" (F1+F2+F3).

**Environment / how to run locally:**
- Postgres runs in Docker: `docker compose up -d postgres` (container `library_postgres`, db `library`, user `library_app`).
- Backend venv: `backend/.venv` (Python 3.12). Activate: `backend\.venv\Scripts\activate`.
- Apply migrations: `cd backend && .\.venv\Scripts\python -m alembic upgrade head`.
- Seed sample data: `cd backend && .\.venv\Scripts\python -m scripts.seed`.
- Run REST API: `cd backend && .\.venv\Scripts\python -m uvicorn library.main:app --reload --port 8000` → http://localhost:8000/docs
- Frontend: `cd frontend && npm run dev` → http://localhost:3000 (still default starter page until F10).
- Lint: `cd backend && .\.venv\Scripts\ruff check src scripts alembic`.

**Repo:** public GitHub `PuneetKumarSinghIT/librarysystem` (origin/main). Commit each feature.

**State of the DB:** migration `607eae6aadb0` (initial schema) applied — 8 tables, `updated_at`
triggers, partial unique index `uq_active_loan_per_copy`, trigram indexes. Seeded with 5 books
/ 13 copies / 3 members. Staff/admin accounts seeded later in F3 (need the password hasher).

**Env gotcha:** file writes in `backend/` occasionally fail silently (sync/AV on `D:`). After
creating/editing files, verify they persisted (Read or `Get-ChildItem`) before moving on.

**Progress log:**
- **F0** — SOLID/hexagonal scaffold (main→controller→service→core→adapter), FastAPI+gRPC
  bootstrap, config, structured logging, health/ready, Docker Compose, Next.js scaffold. Booted & committed.
- **F1** — ORM models (staff, members, books, book_copies, loans, fines, audit_log,
  refresh_tokens), Alembic async env + initial migration (extensions, constraints, indexes,
  partial unique index, updated_at triggers), seed script. Migration applied to Postgres; seed run; lint clean.

---

## 1. Project Snapshot

A backend + web app for a small neighborhood library to manage **books, members, and lending
operations** (borrow / return / query). Built to an enterprise bar: secure, fast, scalable,
and highly maintainable.

**Source spec:** `Neighborhood Library App – Take-Home Test.pdf` (in repo root).

**Core requirements (must-have):**
1. Create/Update records for **books** and **members**.
2. Record when a member **borrows** a book.
3. Record when a borrowed book is **returned**.
4. **Query/list** borrowed books (e.g. all books a member currently has out).

**Deliverables (from the spec):** DB schema · Protobuf service (.proto) · Python API server ·
README (setup/run/test) · minimal Next.js/React frontend.

**Evaluation axes:** schema design · service-interface quality · code quality ·
documentation. **Bonus:** error handling (e.g. borrowing an already-checked-out book), input
validation, sample client.

---

## 2. Locked Architectural Decisions

These are settled. Do not re-litigate without adding an ADR to the Decision Log.

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| D1 | Service interface | **gRPC (Protobuf) core + REST/JSON gateway** | Honors the assignment's gRPC preference *and* gives the Next.js frontend a browser-friendly REST surface. |
| D2 | Book inventory model | **Per physical copy** (`books` → `book_copies` → `loans`) | Mirrors a real library; enables true per-copy "already checked out" enforcement; best normalization. |
| D3 | Auth | **Staff auth: JWT (access+refresh) + RBAC** (admin/librarian) | Matches the "hard to hack" goal without over-scoping to full OIDC/MFA. |
| D4 | Language/runtime | **Python 3.12** | Required by spec. |
| D5 | Datastore | **PostgreSQL 16** | Required by spec. |
| D6 | Frontend | **Next.js 14 (App Router) + TypeScript + React Query** | Spec prefers Next.js. |
| D7 | Delivery | **Docker Compose** for full local stack | "Highly manageable" / reproducible one-command setup. |

---

## 3. Tech Stack

**Backend**
- Python 3.12, `grpcio` + `grpcio-tools` (gRPC server + codegen)
- **REST gateway:** FastAPI + Pydantic v2 (thin layer that calls the same service/business
  layer as gRPC; auto OpenAPI/Swagger docs for the frontend and graders)
- SQLAlchemy 2.0 (async) + Alembic (migrations)
- `asyncpg` driver
- `argon2-cffi` (password hashing), `pyjwt` (tokens), `passlib` optional
- `pydantic-settings` (typed config from env)
- `structlog` (structured JSON logging)

**Database**
- PostgreSQL 16, UUID PKs (`gen_random_uuid()` via `pgcrypto`)

**Frontend**
- Next.js 14 (App Router), TypeScript, TanStack Query, Tailwind CSS, React Hook Form + Zod

**Infra / DevOps**
- Docker + Docker Compose (postgres, backend, gateway, frontend, envoy-optional)
- Envoy (optional) for native gRPC-Web if we later want the browser to hit gRPC directly;
  default path is REST gateway
- GitHub Actions CI (lint, type-check, tests, build)
- `ruff` (lint+format), `mypy` (types), `pytest` (tests) for Python; `eslint`+`prettier` for FE

---

## 4. System Architecture

```mermaid
flowchart LR
    subgraph Client
        FE[Next.js Frontend<br/>TypeScript + React Query]
    end
    subgraph Edge
        GW[REST Gateway<br/>FastAPI + Pydantic<br/>authn/z, rate limit, validation]
    end
    subgraph Core
        SVC[Domain / Service Layer<br/>business rules, transactions]
        GRPC[gRPC Server<br/>grpcio + Protobuf]
    end
    DB[(PostgreSQL 16)]

    FE -->|HTTPS/JSON| GW
    GW -->|in-proc call| SVC
    GRPC -->|in-proc call| SVC
    SVC -->|async SQLAlchemy| DB
```

**Layering — Ports & Adapters (Hexagonal) + SOLID.** Mandated call flow:

```
main.py  (composition root: wires concrete adapters into services, starts servers)
   │
   ▼
controller/   REST routers + gRPC servicers — translate transport ⇄ service ONLY
   │
   ▼
service/      use-cases: orchestration, transactions, business rules
   │
   ▼
core/         PURE domain — entities, enums, errors, and PORTS (abstract interfaces)
   ▲
   │  (Dependency Inversion: service depends on core ports, NOT on adapters)
adapter/      concrete implementations of core ports (DB repos, argon2, JWT, ...)

support:  models/ (ORM)   config/ (settings, logging)   utils/ (helpers)   schemas/ (DTOs)
```

- **Dependency rule:** dependencies point *inward*. `core` imports nothing from
  `service`/`adapter`/`controller`. `service` depends only on `core` abstractions (ports).
  `adapter` implements those ports. `controller` calls `service`. `main.py` is the only place
  that knows concrete adapters (composition root / DI).
- Both transports (gRPC + REST) are thin `controller` adapters over the **same `service`
  layer** — no business logic in controllers. Keeps the two interfaces consistent + DRY.
- This is exactly what makes the project loosely coupled, swappable (e.g. change DB or hashing
  by writing a new adapter), and unit-testable (services tested against fake ports).

### 4.1 SOLID Principles (mandatory)

All code MUST follow SOLID. Concretely, in this codebase:

- **S — Single Responsibility.** Each module has one reason to change. Controllers only
  translate transport ⇄ service. Services only orchestrate use-cases. Repositories only
  persist. No "god" classes.
- **O — Open/Closed.** Extend via new adapters/services, not by editing stable core. New
  transport (e.g. GraphQL) or new store = new adapter implementing an existing port.
- **L — Liskov Substitution.** Any adapter implementing a core port is fully swappable
  (e.g. a fake in-memory repo in tests substitutes the Postgres repo without breaking callers).
- **I — Interface Segregation.** Ports are small and focused (`BookRepository`,
  `PasswordHasher`, `TokenProvider`) — no fat interfaces forcing unused methods.
- **D — Dependency Inversion.** High-level `service` depends on `core` abstractions (ports),
  never on concrete `adapter` classes. `main.py` injects concretes (constructor injection).

**Non-negotiables:** no business logic in controllers; no framework/ORM imports in `core`;
services receive their dependencies via constructor (DI), never instantiate adapters directly;
one class/responsibility per file where practical.

---

## 5. Repository Structure

```
neighborhood-library/
├── CLAUDE.md                     # this file
├── README.md                     # setup / run / test (a deliverable)
├── docker-compose.yml
├── .env.example
├── proto/
│   └── library/v1/
│       ├── common.proto
│       ├── books.proto
│       ├── members.proto
│       ├── loans.proto
│       └── auth.proto
├── backend/
│   ├── pyproject.toml
│   ├── alembic/                  # migrations
│   ├── src/library/
│   │   ├── main.py               # composition root + REST entry (grpc entry: main_grpc.py)
│   │   ├── config/               # settings.py (pydantic-settings), logging.py
│   │   ├── controller/           # transport adapters (translate only)
│   │   │   ├── rest/             # FastAPI app, routers, deps, middleware, errors
│   │   │   └── grpc/             # gRPC servicers + generated stubs
│   │   ├── service/              # use-cases: BookService, MemberService, LoanService, AuthService
│   │   ├── core/                 # PURE domain
│   │   │   ├── entities.py       # domain entities / value objects
│   │   │   ├── enums.py
│   │   │   ├── errors.py
│   │   │   └── ports/            # abstract interfaces (repositories, hasher, token provider)
│   │   ├── adapter/              # concrete implementations of core ports
│   │   │   ├── db/               # engine, session, repositories (implement core.ports)
│   │   │   └── security/         # argon2 hasher, jwt provider
│   │   ├── models/               # SQLAlchemy ORM models (persistence)
│   │   ├── schemas/              # Pydantic DTOs (request/response)
│   │   └── utils/                # cross-cutting helpers
│   ├── tests/                    # unit (services vs fake ports) + integration
│   └── scripts/                  # sample client, seed data
├── frontend/                     # Next.js app
│   ├── app/                      # routes: /books /members /loans /login
│   ├── components/
│   ├── lib/api/                  # typed API client
│   └── ...
└── infra/
    ├── envoy/ (optional)
    └── ci/ (GitHub Actions)
```

---

## 6. Database Design

### 6.1 ER Diagram

```mermaid
erDiagram
    STAFF_USERS ||--o{ LOANS : "processed_by"
    STAFF_USERS ||--o{ AUDIT_LOG : "actor"
    STAFF_USERS ||--o{ REFRESH_TOKENS : "owns"
    MEMBERS ||--o{ LOANS : "borrows"
    BOOKS ||--o{ BOOK_COPIES : "has copies"
    BOOK_COPIES ||--o{ LOANS : "lent as"
    LOANS ||--o{ FINES : "may incur"

    STAFF_USERS {
        uuid id PK
        text email UK
        text password_hash
        text role "admin | librarian"
        bool is_active
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }
    MEMBERS {
        uuid id PK
        text first_name
        text last_name
        text email UK
        text phone
        text address
        text status "active | suspended"
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at "soft delete"
    }
    BOOKS {
        uuid id PK
        text title
        text author
        text isbn UK
        text publisher
        int published_year
        text category
        text description
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }
    BOOK_COPIES {
        uuid id PK
        uuid book_id FK
        text barcode UK
        text condition "new | good | worn | damaged"
        text status "available | borrowed | lost | maintenance"
        date acquired_on
        timestamptz created_at
        timestamptz updated_at
    }
    LOANS {
        uuid id PK
        uuid copy_id FK
        uuid member_id FK
        uuid staff_id FK
        timestamptz borrowed_at
        timestamptz due_at
        timestamptz returned_at "NULL = still out"
        text status "active | returned | overdue"
        int renewed_count
        timestamptz created_at
        timestamptz updated_at
    }
    FINES {
        uuid id PK
        uuid loan_id FK
        uuid member_id FK
        numeric amount
        text reason
        text status "pending | paid | waived"
        timestamptz assessed_at
        timestamptz paid_at
    }
    AUDIT_LOG {
        uuid id PK
        uuid actor_staff_id FK
        text action
        text entity_type
        uuid entity_id
        jsonb metadata
        inet ip_address
        timestamptz created_at
    }
    REFRESH_TOKENS {
        uuid id PK
        uuid staff_id FK
        text token_hash
        timestamptz expires_at
        timestamptz revoked_at
        timestamptz created_at
    }
```

### 6.2 Key Integrity Rules (enforce at the DB, not just the app)

- **"A copy can only be on loan once at a time"** → partial unique index:
  ```sql
  CREATE UNIQUE INDEX uq_active_loan_per_copy
    ON loans (copy_id) WHERE returned_at IS NULL;
  ```
  This makes double-borrow **impossible** even under concurrency — the DB rejects it.
- Borrowing flow runs in a **transaction**: insert `loans` row + flip `book_copies.status`
  to `borrowed`. Use `SELECT ... FOR UPDATE` on the copy row to serialize.
- Returning: set `loans.returned_at = now()`, `status = returned`, copy back to `available`;
  optionally assess a fine if `now() > due_at`.
- Foreign keys with sensible `ON DELETE` (RESTRICT for referenced masters; soft-delete masters
  instead of hard delete).
- Indexes: `loans(member_id) WHERE returned_at IS NULL`, `book_copies(book_id)`,
  `books(isbn)`, `members(email)`, full-text/`pg_trgm` on `books.title/author` for search.
- All timestamps `timestamptz` (UTC). Money as `numeric(10,2)`, never float.
- `updated_at` maintained by trigger; soft-delete via `deleted_at` on master tables.

---

## 7. Service Interface (gRPC + REST)

**Contract-first:** define `.proto` → generate Python stubs → implement servicers → REST
gateway mirrors the same operations. REST paths below are what the frontend consumes.

| Domain | gRPC RPC | REST | Notes |
|--------|----------|------|-------|
| Auth | `Login`, `Refresh`, `Logout` | `POST /auth/login` `/refresh` `/logout` | Returns JWT access+refresh |
| Books | `CreateBook`, `UpdateBook`, `GetBook`, `ListBooks` | `POST/PATCH/GET /books`, `GET /books/{id}` | List supports search + pagination |
| Copies | `AddCopy`, `UpdateCopy`, `ListCopies` | `.../books/{id}/copies` | Per-copy inventory |
| Members | `CreateMember`, `UpdateMember`, `GetMember`, `ListMembers` | `/members...` | |
| Loans | `BorrowBook`, `ReturnBook`, `ListLoans`, `ListMemberLoans` | `POST /loans` (borrow), `POST /loans/{id}/return`, `GET /loans?member_id=&active=true` | Core lending ops |

**Conventions:**
- Pagination: `page_size` + `page_token` (gRPC) / `?limit=&cursor=` (REST).
- Errors: gRPC status codes ↔ HTTP codes mapped centrally
  (`ALREADY_EXISTS`→409, `FAILED_PRECONDITION`→422 for "already checked out",
  `NOT_FOUND`→404, `INVALID_ARGUMENT`→400, `UNAUTHENTICATED`→401, `PERMISSION_DENIED`→403).
- Consistent envelope for REST errors: `{ "error": { "code", "message", "details" } }`.
- Timestamps as RFC3339 strings in REST, `google.protobuf.Timestamp` in gRPC.

---

## 8. Security Blueprint ("very hard to hack")

**Authentication & sessions**
- Passwords hashed with **argon2id** (never store plaintext; never bcrypt-with-defaults only).
- **JWT access token** (~15 min) + **refresh token** (rotating, stored hashed, revocable).
- Refresh-token rotation + reuse detection (revoke family on reuse).
- `Logout` revokes the refresh token.

**Authorization**
- **RBAC**: `admin` (manage staff + everything) vs `librarian` (books/members/loans).
- Enforced in the service layer (single choke point), not scattered in transport.

**Input handling / injection defense**
- All queries via SQLAlchemy parameter binding — **no string-built SQL**.
- Strict validation with Pydantic (REST) and proto + service-layer validators (gRPC):
  types, lengths, enums, email/ISBN format, positive integers.
- Reject unknown fields; normalize/trim; canonicalize emails.

**Transport & headers**
- TLS everywhere in prod (terminate at edge). HSTS.
- Security headers on REST + frontend: `Content-Security-Policy`, `X-Content-Type-Options`,
  `X-Frame-Options: DENY`, `Referrer-Policy`, `Permission-Policy`.
- CORS locked to the known frontend origin(s).

**Abuse / DoS**
- **Rate limiting** (per IP + per account) on auth and mutating endpoints (e.g. `slowapi`/
  gateway-level). Login lockout/backoff after N failures.
- Request size limits; pagination caps (max page size) to prevent scraping/OOM.

**Secrets & config**
- No secrets in code/repo. `.env` (gitignored) + `.env.example`. In prod: env/secret store.
- Separate DB users with least privilege; app user cannot DDL.

**Auditability**
- `audit_log` records who did what (staff, action, entity, IP, timestamp).
- Structured logs; never log secrets/tokens/passwords/PII in plaintext.

**Data protection**
- Soft-delete PII (members) with retention policy; ability to hard-purge on request.
- Principle of least data in tokens/logs.

**Dependency & supply chain**
- Pin dependencies; run `pip-audit` / `npm audit` in CI; Dependabot.

---

## 9. DevOps & Infrastructure

**Local (one command):** `docker compose up` brings up postgres + backend (gRPC) +
gateway (REST) + frontend. Healthchecks + `depends_on`. Migrations run on start.

**Config:** 12-factor via env vars, typed by `pydantic-settings`. `.env.example` documents all.

**Migrations:** Alembic; every schema change is a migration (never manual DDL). Seed script
for demo data (`scripts/seed.py`).

**CI (GitHub Actions):**
1. Lint + format check (`ruff`, `eslint`)
2. Type check (`mypy`, `tsc`)
3. Tests (`pytest` with a throwaway postgres service; FE unit tests)
4. Build Docker images
5. Security scans (`pip-audit`, `npm audit`)

**Observability:** structured JSON logs (`structlog`), request IDs propagated,
health/readiness endpoints, optional OpenTelemetry hooks (stretch).

**Deployment target (documented, not necessarily built):** container images deployable to
any orchestrator; stateless app tier behind a load balancer; managed Postgres.

---

## 10. Performance & Scalability

- **Async everywhere** (FastAPI async + SQLAlchemy async + asyncpg) — high concurrency.
- **Connection pooling** (pool size tuned; `pgbouncer` in front of Postgres for scale-out).
- **Stateless app tier** → horizontal scale; sessions live in DB/JWT, not memory.
- **Indexed queries** (see §6.2); avoid N+1 via explicit joins/`selectinload`.
- **Pagination** on all list endpoints; caps enforced.
- **Caching** (stretch): read-through cache for hot reads (book catalog) via Redis; ETags on
  REST GETs.
- Keep transactions short; use the partial unique index instead of app-level locking where
  possible.

---

## 11. Feature-by-Feature Roadmap

Build in this order. **Each feature follows the Working Protocol (§12) and is "done" only
when it meets the Definition of Done (§13).** Check items off here as we complete them.

- [ ] **F0 — Scaffold & infra:** repo structure, docker-compose (postgres+backend+frontend),
  pyproject, base FastAPI+gRPC bootstrap, config, structured logging, healthcheck, CI skeleton.
- [ ] **F1 — DB schema & migrations:** all tables from §6, Alembic migration, constraints,
  indexes, `updated_at` triggers, seed script.
- [ ] **F2 — Proto contract:** `.proto` files for auth/books/members/loans + codegen wired
  into build.
- [ ] **F3 — Auth (JWT + RBAC):** staff login/refresh/logout, argon2 hashing, middleware,
  role guards, rate limiting on login.
- [ ] **F4 — Books + Copies CRUD:** create/update/get/list books; add/update/list copies;
  search + pagination; validation.
- [ ] **F5 — Members CRUD:** create/update/get/list; validation; soft delete.
- [ ] **F6 — Lending (borrow):** `BorrowBook` — transactional, enforces "copy available",
  sets due date, flips copy status; rejects already-checked-out (409/422).
- [ ] **F7 — Lending (return):** `ReturnBook` — closes loan, frees copy, optional overdue
  fine.
- [ ] **F8 — Queries:** list active loans per member, overdue report, catalog availability.
- [ ] **F9 — REST gateway polish:** OpenAPI docs, error envelope, CORS, security headers.
- [ ] **F10 — Frontend:** login, books list/detail, members, borrow/return flows, "member's
  current loans" view. TanStack Query + form validation.
- [ ] **F11 — Hardening:** audit log, rate limits across mutations, input fuzz/validation
  pass, security headers, `pip-audit`/`npm audit`, **full exception-handling sweep (§18)**.
- [ ] **F12 — Test suite:** unit tests for every service against fake ports covering **all
  edge cases**, integration tests for transactional flows (double-borrow, concurrency),
  ≥90% coverage on `service/` + `core/`. See §18.
- [ ] **F13 — Load / stress test:** 500 concurrent users against the running site; capture
  throughput, latency percentiles (p50/p95/p99), error rate; write results to
  `docs/load-test.md`. See §18.
- [ ] **F14 — Comprehensive README (§19):** architecture + rationale, ER diagram, sample SQL,
  FE/BE paradigms + rationale, step-by-step time/space complexity, security & scalability,
  sample client, setup/run/test.

**Optional / stretch:** fines management UI, Redis cache, Envoy gRPC-Web path, OpenTelemetry,
overdue email notifications, MFA.

---

## 12. Working Protocol (how we build each feature)

1. **State the slice.** One feature from §11 at a time; smallest shippable vertical slice.
2. **Schema/contract first.** If it touches data → migration; if it touches the API → proto +
   REST route, both mirroring the service layer.
3. **Service layer = business rules.** Put invariants here (e.g. "copy must be available").
4. **Both transports thin.** gRPC servicer and FastAPI router just adapt in/out.
5. **Tests alongside.** Unit for service logic; integration for the transactional flows
   (borrow/return double-book, concurrency).
6. **Validate & handle errors** per §7/§8 mapping.
7. **Update this file:** tick the roadmap box, add an ADR if a decision changed.
8. **Report:** what changed, how to run/test it, what's next.

Keep changes small and reviewable. Match existing code style. No business logic in transport
or frontend. No secrets committed.

---

## 13. Definition of Done (per feature)

- Code compiles; `ruff`, `mypy`, tests pass locally (and in CI).
- Migration written + applies cleanly; rollback considered.
- Both gRPC + REST paths work where applicable and return mapped errors.
- Input validated; **every failure path has explicit, logical exception handling** (§18) —
  no bare `except`, no silently swallowed errors, every raise maps to a status code.
- **Unit tests written AND passing for the happy path + all edge cases** (§18); new business
  rules covered against fake ports.
- No plaintext secrets/PII in logs; authz enforced.
- README/section updated if setup or usage changed.
- Roadmap checkbox ticked; Decision Log updated if needed.

---

## 14. Coding Conventions & Quality Gates

- **Python:** type hints everywhere; `ruff` format+lint; `mypy` strict-ish; docstrings on
  public service methods; small functions; explicit exceptions (custom domain errors mapped
  to gRPC/HTTP codes centrally).
- **SQL/ORM:** migrations only (no ad-hoc DDL); parameterized queries only.
- **TS/React:** typed API client generated/hand-written from the contract; server components
  where sensible; forms validated with Zod; no `any`.
- **Naming:** snake_case (Python/SQL), camelCase (TS), `library.v1` proto package.
- **Commits (when a git repo exists):** conventional commits (`feat:`, `fix:`, `chore:`).
  > NOTE: this workspace is **not currently a git repo** — offer to `git init` before any
  > commit-based workflow.

---

## 15. Environment & Config (draft `.env.example`)

```
# Postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=library
POSTGRES_USER=library_app
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql+asyncpg://library_app:change_me@postgres:5432/library

# Auth
JWT_SECRET=change_me_long_random
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=1209600
ARGON2_TIME_COST=3

# Server
GRPC_PORT=50051
REST_PORT=8000
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_LOGIN_PER_MINUTE=5

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 18. Testing, Exception Handling & Load Testing (mandatory)

### 18.1 Exception handling policy
- **Every** external call and business branch has a defined failure path. No bare `except:`,
  no `except Exception: pass`, no silent defaults hiding errors.
- Business failures raise a **typed `DomainError`** (`core/errors.py`); controllers map them
  to HTTP/gRPC codes centrally (§7). Unexpected errors → logged with request id → generic 500
  (never leak stack traces/PII to clients).
- Validation happens at the edge (Pydantic/proto) **and** invariants re-checked in the service
  (defense in depth). Log at the boundary with structured context; include a `request_id`.
- Document the "logical steps" of each handler in a short docstring: preconditions → action →
  failure modes → result.

### 18.2 Unit & integration tests (cover ALL edge cases)
- Framework: `pytest` + `pytest-asyncio`. Services tested **against fake in-memory ports**
  (fast, deterministic, no DB) — this is why ports exist (DIP pays off here).
- Integration tests hit a **real Postgres** (Docker or a test schema) for transactional flows.
- **Edge cases are mandatory**, e.g.: borrow an already-borrowed copy; return an already-
  returned loan; borrow for a suspended member; duplicate ISBN/email/barcode; not-found ids;
  invalid inputs; unauthorized role; expired/invalid/revoked token; pagination bounds;
  concurrent double-borrow (the partial unique index must win).
- **Coverage target ≥ 90%** on `service/` and `core/`; every `DomainError` raise has a test.
- Tests run in CI on every push. `pytest -q` must be green before any commit.

### 18.3 Load / stress test — 500 concurrent users
- Tool: **Locust** (Python, scriptable) — `backend/loadtest/locustfile.py`. Alt: `k6`.
- Scenario: realistic mix — login, list/search books, view a member's loans, borrow, return.
- Run: **500 concurrent users** ramping up, sustained window, against the running stack
  (Postgres + backend + gateway) on the laptop.
- Capture & report: requests/sec (throughput), latency **p50/p95/p99**, error rate, and
  resource notes (CPU/mem). Save to `docs/load-test.md` with a short interpretation +
  bottleneck analysis and tuning notes (pool size, workers).
- Goal is evidence + honest numbers, not a pass/fail vanity metric. Report real results.

---

## 19. README Specification (the documentation deliverable)

The final `README.md` MUST explain (this is an explicit requirement, not optional):
1. **Architecture** — each layer (`main→controller→service→core→adapter`) and **why** it was
   adopted (SOLID, hexagonal, loose coupling, testability, swappability).
2. **Database schema** — the **ER diagram** (Mermaid), table-by-table rationale, normalization
   choices, key constraints (esp. the partial unique index), and **sample SQL queries** for
   common questions ("books a member has out", "overdue loans", "availability by title").
3. **Backend design & paradigm** — Ports & Adapters + DI, async I/O, contract-first gRPC+REST,
   with the reasoning behind each choice.
4. **Frontend design & paradigm** — Next.js App Router, server/client components, React Query
   data layer, typed API client, form validation — with reasons.
5. **Complexity analysis** — step-by-step **time & space complexity** of the key operations
   (borrow, return, list/search, member-loans lookup) and how indexes make them efficient.
6. **Security** — every concept used (argon2id, JWT rotation, RBAC, parameterized SQL,
   validation, rate limiting, security headers, CORS, audit log, least privilege) and how each
   hardens the app.
7. **Scalability** — async, stateless tier, pooling/pgbouncer, indexing, pagination, caching
   path; plus the **load-test statistics** from §18.3.
8. **Setup / run / test** — DB (Docker), proto codegen, running servers, env vars, sample
   client, how to run unit + load tests.

---

## 16. Decision Log (ADRs)

| ID | Date | Decision | Status |
|----|------|----------|--------|
| ADR-001 | 2026-07-19 | Interface = gRPC core + REST gateway (D1) | Accepted |
| ADR-002 | 2026-07-19 | Book inventory modeled per physical copy (D2) | Accepted |
| ADR-003 | 2026-07-19 | Auth = JWT access+refresh + RBAC, argon2id (D3) | Accepted |
| ADR-004 | 2026-07-19 | Docker Compose as canonical local environment (D7) | Accepted |
| ADR-005 | 2026-07-19 | Double-borrow prevented by partial unique index on `loans` | Accepted |
| ADR-006 | 2026-07-19 | Local dev: Postgres in Docker; backend + frontend run natively (venv / npm) for fast hot-reload. `docker compose up` also runs the full stack. | Accepted |
| ADR-007 | 2026-07-19 | Build & run the whole project locally first; **git init + commit to a new repo only after** the local run is verified working. | Accepted |
| ADR-008 | 2026-07-19 | Architecture = Hexagonal (Ports & Adapters) + SOLID. Mandated flow `main.py → controller → service → core → adapter`, with `models/config/utils/schemas` support. Dependencies point inward; DI at the composition root. | Accepted |
| ADR-009 | 2026-07-19 | Mandatory: explicit exception handling on every failure path; unit tests covering all edge cases (≥90% on service/core); pytest in CI. (§18) | Accepted |
| ADR-010 | 2026-07-19 | Load test with **Locust at 500 concurrent users**; publish throughput + p50/p95/p99 latency + error rate to `docs/load-test.md`. (§18.3) | Accepted |
| ADR-011 | 2026-07-19 | README is a first-class deliverable covering architecture rationale, ER diagram, sample SQL, FE/BE paradigms, step-by-step time/space complexity, security & scalability. (§19) | Accepted |

Add a row whenever a locked decision changes or a new architectural choice is made.

---

## 17. Open Questions / Assumptions

- **Assumed** loan period default (e.g. 14 days) — confirm library policy; configurable.
- **Assumed** fines are optional/stretch; core flow works without them.
- **Assumed** single-tenant (one library branch). Multi-branch is out of scope for now.
- **Envoy/gRPC-Web** for the browser is optional; default frontend path is the REST gateway.
- Deployment is documented but not provisioned (no target cloud chosen yet).

---

_Last updated: 2026-07-19 · Keep this file current — it is how we avoid re-explaining the task._
