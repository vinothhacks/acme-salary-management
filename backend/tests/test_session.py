from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import (
    make_engine,
    make_session_factory,
    normalize_database_url,
    session_dependency,
)


def test_session_factory_executes() -> None:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    factory = make_session_factory(engine)
    with factory() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1
    engine.dispose()


def test_session_dependency_closes() -> None:
    settings = Settings(database_url="sqlite+pysqlite:///:memory:")
    gen = session_dependency(settings)
    session = next(gen)
    assert session.execute(text("SELECT 1")).scalar() == 1
    gen.close()


def test_file_sqlite_allows_concurrent_sessions(tmp_path: Path) -> None:
    url = f"sqlite+pysqlite:///{(tmp_path / 'pool.db').resolve().as_posix()}"
    engine = make_engine(url)
    factory = make_session_factory(engine)

    def ping() -> int:
        with factory() as session:
            return int(session.execute(text("SELECT 1")).scalar_one())

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(ping) for _ in range(4)]
        assert [f.result(timeout=5) for f in as_completed(futures)] == [1, 1, 1, 1]
    engine.dispose()


def test_normalize_render_postgres_url() -> None:
    assert (
        normalize_database_url("postgres://acme:secret@dpg-xx:5432/acme_salary")
        == "postgresql+psycopg://acme:secret@dpg-xx:5432/acme_salary"
    )
