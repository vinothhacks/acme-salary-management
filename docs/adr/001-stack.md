# ADR 001 — Stack

**Status:** Accepted  
**Date:** 2026-08-29

## Context

The assessment brief says “language and framework as per JD (preferred).” The candidate confirmed Python is acceptable. We need a stack that can serve 10k rows, generate OpenAPI, and ship a dense HR UI quickly without looking like a tutorial.

## Decision

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI | OpenAPI for free; async-ready; typed |
| ORM | SQLAlchemy 2 + Alembic | Explicit models; portable migrations |
| Prod DB | PostgreSQL | `percentile_cont`, partial unique indexes, DECIMAL |
| Test DB | SQLite | Suite under 10s, zero network |
| UI | React + Vite + TypeScript | Fast refresh; typed forms |
| UI kit | shadcn/ui + TanStack Table/Query + Recharts | Accessible primitives; server tables; charts |
| Auth | HTTP-only session cookie | Single user; no JWT ceremony |
| Local | Docker Compose (Postgres + API + UI) | One command; documented `.env` fallback |

Deploy (Phase 7, not this loop): Railway/Render for API+DB, Vercel for UI.

## Consequences

- Tests use SQLite; a few Postgres-only features (`percentile_cont`, partial unique indexes) need dialect-aware tests or Postgres in CI for those cases.
- TypeScript + Pydantic keep money and dates honest at both edges.
