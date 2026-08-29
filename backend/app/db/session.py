from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


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
