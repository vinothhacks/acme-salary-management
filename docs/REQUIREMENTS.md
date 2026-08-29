# ACME Salary Management — Requirements

**Persona:** one HR manager. **Scale:** 10,000 employees across countries. **Replace:** Excel.

## Goal

Give one HR manager a single system to view, edit, audit, and ask questions of pay data — without running payroll.

## In scope

- Employee directory: search (name / code / email), filter (country, department, band, status), paginate, sort
- Salary records with full effective-dated history (current + past revisions)
- Multi-currency amounts; org-wide totals normalized to USD via a seeded rates table
- Analytics: headcount, cost, distribution, percentiles, cost trend
- CSV import (messy Excel exports) with row-level errors; CSV export
- Deterministic 10,000-employee seed
- Single-user login gate (session cookie)

## Deliberately out of scope

| Out | Why |
|---|---|
| Payroll (tax, payslips, bank transfers) | Different domain and risk class |
| RBAC / multi-user | One HR manager; a login gate is enough |
| Approval workflows | No second persona exists to approve |
| Live FX feeds | External dependency with no assessment value; seeded table is enough |
| Employee self-service | Out of persona |

## Non-negotiable design positions

- Money is `DECIMAL(14,2)` (or `Decimal` in Python). Never float.
- A salary is an effective-dated row (`effective_from`, `effective_to` NULL = current).
- Country views stay in local currency. Org aggregates convert to USD via `fx_rates`.

## Success

A stranger can run the repo locally, log in, find an employee, revise pay, see history, and answer “what does this org cost?” from the dashboard.
