from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Department, Employee, FxRate, SalaryRecord  # noqa: F401
from app.services.seed import dataset_checksum, seed, verify_counts


def _fresh() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_seed_determinism() -> None:
    first = _fresh()
    second = _fresh()
    a = seed(first, count=80, reset=True)
    first.commit()
    b = seed(second, count=80, reset=True)
    second.commit()
    assert a["checksum"] == b["checksum"]
    assert dataset_checksum(first) == dataset_checksum(second)
    assert verify_counts(first)["employees"] == 80
    assert verify_counts(first)["open_salaries"] == 80
    assert verify_counts(first)["fx_rates"] == 8
    assert verify_counts(first)["departments"] == 10


def test_seed_reset_is_idempotent() -> None:
    session = _fresh()
    first = seed(session, count=40, reset=True)
    session.commit()
    second = seed(session, count=40, reset=True)
    session.commit()
    assert first["checksum"] == second["checksum"]
    assert verify_counts(session)["employees"] == 40
