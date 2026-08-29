from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings


def make_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # StaticPool is required so in-memory DBs share one connection.
        # File SQLite must not use it — concurrent request threads deadlock
        # on a single pooled connection (dashboard fires four analytics GETs).
        if ":memory:" in url:
            return create_engine(url, connect_args=connect_args, poolclass=StaticPool)
        return create_engine(url, connect_args=connect_args)
    return create_engine(url, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_dependency(settings: Settings) -> Generator[Session, None, None]:
    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
