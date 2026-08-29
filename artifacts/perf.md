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

