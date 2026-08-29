"""Seed a small SQLite file and serve the API for Playwright."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{(ROOT / 'e2e-data.db').as_posix()}")
os.environ.setdefault("HR_EMAIL", "hr@acme.example")
os.environ.setdefault("HR_PASSWORD", "acme-hr-change-me")
os.environ.setdefault("SECRET_KEY", "e2e-secret")

from sqlalchemy import func, select  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import make_engine, make_session_factory  # noqa: E402
from app.models import Department, Employee, FxRate, SalaryRecord  # noqa: E402, F401
from app.services.seed import seed  # noqa: E402

engine = make_engine(os.environ["DATABASE_URL"])
Base.metadata.create_all(engine)
factory = make_session_factory(engine)
with factory() as session:
    count = int(session.scalar(select(func.count()).select_from(Employee)) or 0)
    if count == 0:
        seed(session, count=80, reset=True)
        session.commit()
engine.dispose()

import uvicorn  # noqa: E402

uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
