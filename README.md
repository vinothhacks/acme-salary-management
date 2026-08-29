# ACME Salary Management

Replace Excel for one HR manager: 10,000 employees, effective-dated pay history,
multi-currency analytics, CSV import.

## Local setup

**Option A — Docker**

```bash
docker compose up --build
```

- UI: http://localhost:5173
- API health: http://localhost:8000/health
- OpenAPI: http://localhost:8000/docs

**Option B — local processes**

1. Copy `.env.example` to `.env`
2. Start Postgres (`docker compose up db -d`) or set `DATABASE_URL`
3. Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload --port 8000
```

4. Frontend:

```bash
cd frontend
npm install
npm test
npm run dev
```

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

## Docs

- [Requirements](docs/REQUIREMENTS.md)
- [ADRs](docs/adr/)
- [Plan](PLAN.md)

Demo login (after Phase 3): `hr@acme.test` / value of `HR_PASSWORD`.
