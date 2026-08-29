from sqlalchemy import text

from app.core.config import Settings
from app.db.session import make_engine, make_session_factory, session_dependency


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
