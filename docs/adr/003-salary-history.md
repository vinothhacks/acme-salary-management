# ADR 003 — Salary history

**Status:** Accepted  
**Date:** 2026-08-29

## Context

“How the org pays people” includes how that changed. Overwriting a single `current_salary` column destroys the audit trail HR actually needs.

## Decision

`salary_records` are immutable facts except for closing the open interval:

- `effective_from` DATE (required)
- `effective_to` DATE NULL = current
- Partial unique index: one open record per employee (`WHERE effective_to IS NULL`)
- A revision, in one transaction: set `effective_to` on the open row, insert the new open row, require `revision_reason`
- Reject overlapping intervals
- Soft-delete employees (`status=inactive`); never hard-delete salary rows

## Rejected

- Single current-salary column + optional audit log: history becomes a second-class dump.
- Event-sourced ledger: overbuilt for one HR manager and 10k people.

## Consequences

- “Current pay” is always `effective_to IS NULL`.
- Cost-over-time queries reconstruct pay from overlapping-free intervals.
- Import and seed must close prior rows before opening a new one.
