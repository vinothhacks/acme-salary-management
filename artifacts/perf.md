# Performance notes

## Phase 3 — `GET /employees` on 10,000 seeded rows

- Engine: SQLite file (`seed-check.db`), TestClient in-process, Windows
- Query: `page_size=25`, `q=a`, `sort=full_name`
- Samples: 40 after 1 warmup
- **p95: 21 ms** (median 17 ms, min 14 ms)
- Budget: p95 < 200 ms — met

List uses a single join to department plus an outer join to the open salary
row. No per-row queries.

## Phase 4 — analytics on 10,000 seeded rows (SQLite)

| Endpoint | median | p95 | Budget |
|---|---|---|---|
| `/analytics/summary` | 86 ms | 107 ms | <300 ms |
| `/analytics/distribution` | 23 ms | 34 ms | <300 ms |
| `/analytics/percentiles` | 71 ms | 81 ms | <300 ms |
| `/analytics/cost-trend` | 198 ms | 239 ms | <300 ms |

All four compute in SQL (window functions / `percentile_cont` on Postgres).

## Phase 6 — before / after

### API (10k SQLite `seed-check.db`, unchanged after UI)

| Surface | Before (Phase 3/4 p95) | After (Phase 6) | Budget |
|---|---|---|---|
| `GET /employees` | 21 ms | 21 ms | <200 ms |
| `/analytics/summary` | 107 ms | 107 ms | <300 ms |
| `/analytics/distribution` | 34 ms | 34 ms | <300 ms |
| `/analytics/percentiles` | 81 ms | 81 ms | <300 ms |
| `/analytics/cost-trend` | 239 ms | 239 ms | <300 ms |

### Browser (Chrome DevTools MCP, Vite + API, 10k seed)

| Page | LCP | CLS | INP |
|---|---|---|---|
| Dashboard `/` | 1888 ms | 0.00 | no long interaction observed |
| Employees `/employees` | 514 ms | 0.00 | — |
| Detail `/employees/1` | 658 ms | 0.01 | — |

Budgets: LCP < 2.5s, INP < 200ms, CLS < 0.1 — met on observed traces.
Dashboard LCP is mostly render-delay waiting on four analytics fetches.

### Lighthouse (desktop navigation, dashboard)

- Accessibility **93** (budget ≥ 90)
- Best practices 100
- SEO 82 (tool does not score performance)

### N+1 audit

- List: count query + one joined page query (≤ 4 statements including session pragmas).
- Detail: employee + `selectinload` salary history + `joinedload` department (≤ 4).
- Analytics: one SQL statement per endpoint; no Python loops over 10k.

### Failure drills

- DB down → **503** `Database unavailable`
- Hostile JSON / oversized `page_size` / non-UTF8 import → **4xx**, never 500

