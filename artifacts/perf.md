# Performance notes

## Phase 3 — `GET /employees` on 10,000 seeded rows

- Engine: SQLite file (`seed-check.db`), TestClient in-process, Windows
- Query: `page_size=25`, `q=a`, `sort=full_name`
- Samples: 40 after 1 warmup
- **p95: 21 ms** (median 17 ms, min 14 ms)
- Budget: p95 < 200 ms — met

List uses a single join to department plus an outer join to the open salary
row. No per-row queries.
