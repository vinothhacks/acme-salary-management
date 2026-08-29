import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.db.session import make_engine, make_session_factory
from app.main import create_app
from app.models import Department, Employee, FxRate, SalaryRecord  # noqa: F401


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        secret_key="test-secret",
        hr_email="hr@acme.example",
        hr_password="test-password",
    )


@pytest.fixture
def engine():
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: object) -> Session:
    factory = make_session_factory(engine)  # type: ignore[arg-type]
    with factory() as db:
        yield db


@pytest.fixture
def client(settings: Settings, engine: object) -> TestClient:
    return TestClient(create_app(settings, engine=engine))  # type: ignore[arg-type]


@pytest.fixture
def auth_client(client: TestClient, settings: Settings) -> TestClient:
    response = client.post(
        "/auth/login",
        json={"email": settings.hr_email, "password": settings.hr_password},
    )
    assert response.status_code == 200
    return client
