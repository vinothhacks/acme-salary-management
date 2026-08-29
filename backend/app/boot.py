"""Migrate, seed if empty, then serve. Used as the Render web start command."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import make_engine, make_session_factory, normalize_database_url
from app.models import Employee
from app.services.seed import seed


def _run_migrations(database_url: str) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", normalize_database_url(database_url).replace("%", "%%"))
    command.upgrade(cfg, "head")


def main() -> None:
    settings = get_settings()
    url = settings.database_url
    _run_migrations(url)
    engine = make_engine(url)
    factory = make_session_factory(engine)
    seed_count = int(os.environ.get("SEED_COUNT", "10000"))
    with factory() as session:
        existing = int(session.scalar(select(func.count()).select_from(Employee)) or 0)
        if existing == 0:
            seed(session, count=seed_count, reset=True)
            session.commit()
    engine.dispose()

    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, factory=False)


if __name__ == "__main__":
    main()
