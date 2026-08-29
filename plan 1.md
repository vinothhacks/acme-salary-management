# PLAN.md — ACME Salary Management (Assessment Build)

**Operating contract:** This build proceeds in gated phases. Every phase is fully defined
in this document before any phase starts. **No phase begins until the previous phase's
checkpoint is reported and approved.** A fault is contained to the phase that caused it:
if a later phase exposes a defect from an earlier phase, work stops, the defect is logged,
and the earlier phase is reopened on its own branch. Later phases never patch over
earlier-phase faults.

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

1. **Checkpoint protocol.** Each phase ends with a report: what was built, decisions + why,
   deviations from plan, test results (passed/failed/runtime), risks carried forward, then
   the explicit question **"Proceed to Phase N+1? (y/n)"** — and STOPS.
2. **Fault containment.** Each phase lives on branch `phase-N-<name>`, merged to `main` only
   after checkpoint approval. All prior phases' tests must be green before merge; a
   regression means a fault escaped its phase — stop, reopen at origin, fix there.
3. **Commit discipline.** Small commits with real messages (`feat(api): salary revision
   endpoint`), committed as work happens. History is evidence of process; it must be genuine.
4. **AI-usage log.** Every significant prompt to an AI tool goes into `artifacts/ai-prompts.md`
   with one line on what was accepted, rejected, or rewritten.
5. **Global definition of done:** live deployed URL, seeded data, demo video, README with
   <10-step setup, all artifacts committed.

---

## Phase 0 — Decisions & Requirements Document

**Goal:** Lock every expensive-to-reverse decision. Produce the required one-page requirements doc.

- [ ] **Confirm stack against the JD.** ⚠️ OPEN — brief says "Language & Framework as per JD
      (preferred)". Defaults below assume the JD tolerates Python. If the JD is Java/Spring
      (the brief's "AngularJS with Java" line hints one track is), Phase 0 re-plans and
      nothing downstream starts.
  - Backend default: **FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL** (SQLite in tests)
  - Frontend default: **React + Vite + TypeScript + shadcn/ui + TanStack Table/Query + Recharts**
  - Deploy default: **Railway/Render** (API+DB) + **Vercel** (UI). Decide now, not in Phase 7.
- [ ] `docs/REQUIREMENTS.md` (one page):
  - **Goal:** replace Excel salary management for 10,000 employees across countries; one HR
    manager can view, edit, audit, and *ask questions of* pay data.
  - **In scope:** employee directory (search/filter/paginate), salary records with full
    effective-dated history, multi-currency + org-wide normalization, analytics dashboard,
    CSV import + export, deterministic 10k seed, single-user auth gate.
  - **Deliberately out, with reasons:**
    - Payroll execution (tax, payslips, transfers) — different domain and risk class
    - RBAC/multi-user — persona is one HR manager; login gate only
    - Approval workflows — no second persona exists to approve
    - Live FX — static seeded rates table; live FX adds an external dependency with zero
      assessment value
    - Employee self-service — out of persona
- [ ] ADRs: `001-stack`, `002-money`, `003-salary-history`, `004-fx`.

**Design positions to defend in interview:**
- Money as `DECIMAL(14,2)` (or integer minor units) — never float.
- Salaries are **effective-dated rows** (`effective_from`, `effective_to NULL` = current):
  "how the org pays people" includes how that changed over time.
- Aggregates normalize via seeded `fx_rates` to USD; per-country views stay local-currency.

**Exit:** requirements + ADRs committed; stack confirmed by the candidate, not assumed by a tool.
**CHECKPOINT 0 → report → STOP.**

---

## Phase 1 — Scaffold, Tooling, CI

**Goal:** Empty-but-running skeleton with quality gates before any feature code.

- [ ] Monorepo: `/backend`, `/frontend`, `/docs`, `/artifacts`, `/scripts`
- [ ] Backend: app factory, `/health`, pytest+coverage, ruff, mypy
- [ ] Frontend: Vite+TS scaffold, ESLint/Prettier, Vitest, renders "OK"
- [ ] GitHub Actions: lint+test both packages on push
- [ ] `docker-compose.yml`: Postgres + API + UI for local dev; pre-commit hooks

**Fault domain:** pure tooling — no feature code exists to contaminate.
**Exit:** CI green on trivial tests; `docker compose up` serves health + blank UI.
**CHECKPOINT 1 → report → STOP.**

---

## Phase 2 — Data Model, Migrations, Seed (10,000)

**Goal:** Schema + deterministic seed. Most expensive phase to get wrong → own gate.

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

**Seed `scripts/seed.py`:**
- [ ] Deterministic (fixed seed) — identical output on rerun; `--reset` flag; runs <60s
- [ ] 10,000 employees, 6–8 countries, 8–12 departments, log-normal salary distributions per
      country/band, ~30% of employees with 2–4 historical revisions

**Tests:** one-open-salary constraint, seed determinism (two runs → identical checksums),
migration up/down.
**Exit:** migrate + seed → verified counts; tests green.
**CHECKPOINT 2 → report → STOP.**

---

## Phase 3 — Core Backend API + Unit Tests

**Goal:** Everything the UI needs except analytics, as tested endpoints.

- [ ] `GET /employees` — pagination, search (name/code/email), filters (country/dept/band/status),
      sort; fast on 10k (indexed, no N+1)
- [ ] `GET /employees/{id}` — profile + full salary history
- [ ] `POST /employees`, `PATCH /employees/{id}` — Pydantic validation, field-level errors
- [ ] `POST /employees/{id}/salary-revisions` — closes open record + opens new **in one
      transaction**; rejects overlaps; requires reason
- [ ] `POST /employees/import` — CSV import with row-level error report (product thinking:
      HR migrates FROM Excel; imports will be messy)
- [ ] Soft-delete only (status=inactive); salary data never hard-deleted
- [ ] Single-user auth gate (session/token) — matches persona, nothing more

**Tests (core of their test requirement):** revision logic (happy/overlap/rollback),
pagination+filter correctness on fixtures, validation edges (negative salary, unknown
currency, malformed CSV rows). Suite **<10s, zero network, frozen time**.
**Exit:** OpenAPI docs generated; suite green; list-endpoint p95 on 10k recorded in `artifacts/perf.md`.
**CHECKPOINT 3 → report → STOP.**

---

## Phase 4 — Analytics ("answer questions about how the org pays")

**Goal:** The product differentiator, computed in SQL — not Python loops over 10k rows.

- [ ] `GET /analytics/summary` — headcount, total annual cost (USD-normalized), mean/median,
      by-country + by-department
- [ ] `GET /analytics/distribution` — histogram buckets, filterable
- [ ] `GET /analytics/percentiles` — p10/p25/p50/p75/p90 by band and country (`percentile_cont`)
- [ ] `GET /analytics/cost-trend` — org cost over time from effective-dated records

**Tests:** percentile math vs hand-computed fixtures; FX normalization; empty-filter edges.
**Exit:** correct on fixtures, <300ms each on seed, numbers traceable to a SQL query.
**CHECKPOINT 4 → report → STOP.**

---

## Phase 5 — UI

**Goal:** Three surfaces, boring in the good way. Every data surface has loading/empty/error
states — that is the line between production-quality and demo-quality.

- [ ] **Employees list** — server-paginated table, search, filter chips, row → detail
- [ ] **Employee detail** — profile, current comp card, salary history timeline,
      "Revise salary" modal mirroring API validation
- [ ] **Dashboard** — summary cards, distribution chart, percentiles-by-band, country breakdown
- [ ] Add-employee form; CSV import flow with per-row error display; CSV export
- [ ] Keyboard-accessible forms; no console errors

**Tests:** component tests for revision-form logic and filter state (not pixel tests).
**Exit:** full flow against real seeded backend locally.
**CHECKPOINT 5 → report → STOP.**

---

## Phase 6 — Integration Hardening & Performance Sanity

**Goal:** Prove it holds at 10k before deploying.

- [ ] Playwright E2E smoke: login → search → revise salary → history shows it → dashboard reflects it
- [ ] Perf pass: list p95, dashboard p95, N+1 audit (SQL echo review)
- [ ] Failure drills: DB down → clean 503; hostile input on every form
- [ ] Update `artifacts/perf.md` with before/after if anything changed

**Fault rule:** defects originating in Phases 2–5 reopen *that* phase's branch. Phase 6 owns
only its own harness.
**Exit:** E2E green in CI; perf recorded; no known 500s.
**CHECKPOINT 6 → report → STOP.**

---

## Phase 7 — Deploy, Demo Video, Submission

- [ ] Deploy API+Postgres (Railway/Render); migrate + seed prod
- [ ] Deploy UI (Vercel); env API URL; CORS locked to UI origin
- [ ] Smoke-test the live URL from a different device/network — not localhost
- [ ] 4–6 min demo video: problem → the three screens → one revision end-to-end → one
      analytics question answered → 30s on architecture decisions
- [ ] README: live URL, local setup, test commands, link to ADRs
- [ ] Final artifact sweep: requirements, ADRs, ai-prompts.md, perf.md, this PLAN.md with
      checkpoints marked, one simple architecture diagram

**Exit:** a stranger with the repo link can open the live app, watch the video, and run it
locally from the README.
**CHECKPOINT 7 → final report → submit.**

---

## Phase-definition rule

All phases are defined above, before Phase 0 begins, as required. Any scope change is edited
into this file and committed *before* the affected phase starts — the diff history of PLAN.md
is itself an artifact of how the thinking evolved.
