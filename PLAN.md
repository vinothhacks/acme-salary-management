# PLAN.md — ACME Salary Management (Assessment Build)

**Cadence (locked 2026-08-29):** Phases 0–6 run continuously. Each phase still lives
on `phase-N-<name>`, reports a checkpoint in chat, and merges to `main` when its
tests are green. Work does **not** wait for a y/n between phases. **Phase 7
(deploy, demo video, public live URL) is a hard stop** — ask before touching it.

**Fault containment:** if a later phase exposes a defect from an earlier phase, fix
it on `fix/phase-N-<bug>` reopened from that phase. Later phases do not silently
patch earlier-phase faults.

---

## 0. What is actually being assessed → what to produce

| Their words | The artifact that proves it |
|---|---|
| "Clarity in thought" | `docs/REQUIREMENTS.md` — one page, explicit out-of-scope + reasons |
| "Architectural decisions" | `docs/adr/` — short ADRs: money type, salary history, FX, DB choice |
| "Production-quality code and tests" | Layered backend, pytest suite, deterministic seed, CI |
| "Use AI intentionally" | `artifacts/ai-prompts.md` — real prompts + what was accepted/rewritten |
| "Incremental commits" | ~15–25 real commits, one coherent step each, made as work happens |
| "Product thinking" | CSV import (HR lives in Excel today), audit trail, currency handling, analytics |

---

## Ground rules (all phases)

1. **Checkpoint report.** Each phase ends with: what was built, decisions + why,
   deviations, test results, risks carried forward — then the next phase starts.
2. **Fault containment.** Each phase lives on branch `phase-N-<name>`, merged to
   `main` when green. A regression means a fault escaped its phase — reopen there.
3. **Commit discipline.** Small commits with real messages (`feat(api): salary revision
   endpoint`), committed as work happens.
4. **AI-usage log.** Every significant prompt goes into `artifacts/ai-prompts.md`.
5. **Definition of done for this loop:** Phases 0–6 merged, E2E green, perf recorded.
   Live URL + demo video wait for Phase 7 approval.

---

## Phase 0 — Decisions & Requirements Document

**Status:** done. Stack confirmed by candidate: FastAPI + SQLAlchemy 2 + Alembic +
PostgreSQL (SQLite in tests); React + Vite + TypeScript + shadcn/ui + TanStack
Table/Query + Recharts. Deploy default remains Railway/Render + Vercel (Phase 7).

- [x] Stack confirmed (Python track)
- [x] `docs/REQUIREMENTS.md`
- [x] ADRs: `001-stack`, `002-money`, `003-salary-history`, `004-fx`

---

## Phase 1 — Scaffold, Tooling, CI

**Goal:** Empty-but-running skeleton with quality gates before any feature code.

- [x] Monorepo: `/backend`, `/frontend`, `/docs`, `/artifacts`, `/scripts`
- [x] Backend: app factory, `/health`, pytest+coverage, ruff, mypy
- [x] Frontend: Vite+TS scaffold, ESLint/Prettier, Vitest, renders "OK"
- [x] GitHub Actions: lint+test both packages on push
- [x] `docker-compose.yml`: Postgres + API + UI for local dev; pre-commit hooks

**Exit:** CI green on trivial tests; `docker compose up` serves health + blank UI.

---

## Phase 2 — Data Model, Migrations, Seed (10,000)

**Schema:**
- `employees` (id, employee_code UNIQUE, full_name, email UNIQUE, country_code,
  department_id FK, job_title, band, employment_type, hire_date, status, timestamps)
- `departments` (id, name)
- `salary_records` (id, employee_id FK, base_amount DECIMAL(14,2), bonus_amount,
  allowances_amount, currency CHAR(3), effective_from DATE, effective_to DATE NULL,
  revision_reason, created_at) — **partial unique index: one open record per employee**
- `fx_rates` (currency, rate_to_usd, as_of_date)
- Indexes: employees(country_code), (department_id), salary_records(employee_id, effective_to),
  name/code search index.

**Seed `scripts/seed.py`:** deterministic, `--reset`, <60s; 10,000 employees, 8
countries, 10 departments, log-normal pay, ~30% with 2–4 historical revisions.

**Tests:** one-open-salary constraint, seed determinism, migration up/down.

---

## Phase 3 — Core Backend API + Unit Tests

- `GET /employees` — pagination, search, filters, sort; indexed, no N+1
- `GET /employees/{id}` — profile + full salary history
- `POST /employees`, `PATCH /employees/{id}`
- `POST /employees/{id}/salary-revisions` — one transaction; reject overlaps; require reason
- `POST /employees/import` — CSV with row-level errors
- Soft-delete only; single-user session auth

Suite <10s, zero network, frozen time. List p95 on 10k in `artifacts/perf.md`.

---

## Phase 4 — Analytics

SQL, not Python loops: `GET /analytics/summary|distribution|percentiles|cost-trend`.
`percentile_cont` (Postgres) / equivalent in tests. <300ms each on seed.

---

## Phase 5 — UI

Employees list, employee detail + revise modal, dashboard, add-employee, CSV
import/export. Loading/empty/error on every data surface. Paper/ink design.
Playwright MCP + Chrome DevTools after this phase.

---

## Phase 6 — Integration Hardening & Performance Sanity

Playwright smoke in CI; list/dashboard p95; N+1 audit; DB-down 503; hostile input.
Budgets: list p95 <200ms, analytics <300ms, LCP <2.5s, INP <200ms, CLS <0.1,
Lighthouse a11y ≥90.

---

## Phase 7 — Deploy, Demo Video, Submission (HARD STOP)

Do not start without an explicit go. Railway/Render + Vercel, prod seed, CORS,
demo video, live-URL README.

---

## Phase-definition rule

Scope changes are edited into this file and committed before the affected phase
starts. The diff history of PLAN.md is an artifact of how the thinking evolved.
