# AI usage log

Real prompts and what was accepted, rewritten, or rejected. Evidence of intentional use.

| When | Prompt (summary) | Outcome |
|---|---|---|
| 2026-08-29 | Implement `plan 1.md` with Playwright MCP E2E, Chrome DevTools perf, GitHub versioning, loop until done | Accepted as operating contract. Rewritten into gated Phases 0–6 with a hard stop before deploy. Stack locked to FastAPI + React after candidate confirmation. |
| 2026-08-29 | Phase 0 docs: requirements + ADRs | Accepted. Money as Decimal, effective-dated salaries, seeded FX — as specified. No feature code in this commit. |
| 2026-08-29 | Scaffold FastAPI + Vite + CI + compose | Accepted. Split vite/vitest configs after Vite 6 vs Vitest 2 type clash. Coverage gate 70%. |
| 2026-08-29 | Schema, Alembic, 10k seed | Accepted. Partial unique index via raw SQL for SQLite+Postgres. Seed 10k in 6.7s. |
| 2026-08-29 | Core API: auth, employees, revisions, CSV import | Accepted. `.test` emails rejected by email-validator; switched to `.example`. List p95 21ms / 10k. |
| 2026-08-29 | Analytics SQL endpoints | Accepted. SQLite nearest-rank percentiles; cost-trend via date spine + active-pay subquery. |
| 2026-08-29 | Paper/ink UI for dashboard, directory, detail, import | Accepted custom CSS over full shadcn install to keep the visual system tight. |
