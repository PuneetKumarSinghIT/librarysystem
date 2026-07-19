# Neighborhood Library System

An enterprise-grade service to manage a small library's **books, members, and lending
operations** — built with a **gRPC core + REST gateway** in Python over **PostgreSQL**, with a
**Next.js** frontend. Designed to be secure, fast, scalable, and highly maintainable.

> **Status:** under active, feature-by-feature development. This README is expanded into full
> documentation (architecture rationale, ER diagram, sample SQL, complexity analysis, security
> & scalability, load-test statistics) as the build progresses. The living design document is
> [CLAUDE.md](./CLAUDE.md).

## Tech stack

| Layer | Technology |
|-------|-----------|
| Server | Python 3.12, gRPC (grpcio) + FastAPI REST gateway |
| Data | PostgreSQL 16, SQLAlchemy 2 (async) + Alembic |
| Auth | JWT (access + refresh) + RBAC, argon2id hashing |
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind, React Query |
| Infra | Docker Compose, GitHub Actions CI |

## Architecture

Hexagonal (Ports & Adapters) + **SOLID**, with a strict inward-pointing dependency flow:

```
main.py → controller → service → core (ports) ← adapter
support: models · schemas · config · utils
```

- **controller/** — REST routers + gRPC servicers (translate transport ⇄ service only)
- **service/** — use-cases, transactions, business rules
- **core/** — pure domain: entities, enums, errors, and ports (abstract interfaces)
- **adapter/** — concrete implementations of core ports (DB repos, security)

See [CLAUDE.md](./CLAUDE.md) for the full architecture, database design, security blueprint,
and roadmap.

## Project layout

```
backend/     Python service (gRPC core + REST gateway)
frontend/    Next.js web app
proto/       Protobuf service contracts
docker-compose.yml
```

## Quick start (local dev)

```bash
# 1. Start PostgreSQL
cp .env.example .env
docker compose up -d postgres

# 2. Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn library.main:app --reload --port 8000       # REST at http://localhost:8000/docs

# 3. Frontend
cd ../frontend
npm install
npm run dev                                         # http://localhost:3000
```

Health check: `GET http://localhost:8000/health`

## License & disclaimer

Licensed under the [MIT License](./LICENSE). This project is published **for educational
purposes only** — please read the [DISCLAIMER](./DISCLAIMER.md). Use at your own risk; the
author accepts no liability.
