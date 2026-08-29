from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings

BACKEND = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_and_downgrade(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "migrate.db"
    url = f"sqlite+pysqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert {"departments", "employees", "salary_records", "fx_rates"} <= tables

    command.downgrade(cfg, "base")
    tables_after = set(inspect(engine).get_table_names())
    assert "employees" not in tables_after

    command.upgrade(cfg, "head")
    tables_again = set(inspect(engine).get_table_names())
    assert "salary_records" in tables_again
    get_settings.cache_clear()
