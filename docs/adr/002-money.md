# ADR 002 — Money

**Status:** Accepted  
**Date:** 2026-08-29

## Context

Compensation is the product. Float rounding would make totals lie and fail an interview in one sentence.

## Decision

- Persist as `NUMERIC(14,2)` / `DECIMAL(14,2)`.
- Application type is `decimal.Decimal`. Never `float`.
- JSON wire format is a string (`"87500.00"`) so clients cannot silently coerce.
- Currency is an ISO 4217 `CHAR(3)` on each salary row, not implied by country.
- Display uses tabular figures; country views stay in the row’s currency.

## Rejected

- Integer minor units (cents): cleaner for FX math, worse to read in SQL and CSV for HR.
- `float` / `DOUBLE`: non-negotiable no.

## Consequences

- Pydantic validators reject negative amounts and unknown currencies.
- Analytics convert via `fx_rates` using Decimal multiplication, then `ROUND_HALF_UP` to 2 places for display totals.
