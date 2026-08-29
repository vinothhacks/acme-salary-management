from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Department, Employee, SalaryRecord


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _employee(session: Session) -> Employee:
    dept = Department(name="Engineering")
    session.add(dept)
    session.flush()
    employee = Employee(
        employee_code="ACME-00001",
        full_name="Ada Berg",
        email="ada.berg.1@acme.test",
        country_code="US",
        department_id=dept.id,
        job_title="Staff Engineering",
        band="IC4",
        employment_type="full_time",
        hire_date=date(2020, 1, 15),
        status="active",
    )
    session.add(employee)
    session.flush()
    return employee


def test_one_open_salary_per_employee() -> None:
    session = _session()
    employee = _employee(session)
    session.add(
        SalaryRecord(
            employee_id=employee.id,
            base_amount=Decimal("100000.00"),
            bonus_amount=Decimal("10000.00"),
            allowances_amount=Decimal("1000.00"),
            currency="USD",
            effective_from=date(2024, 1, 1),
            effective_to=None,
            revision_reason=None,
        )
    )
    session.commit()
    session.add(
        SalaryRecord(
            employee_id=employee.id,
            base_amount=Decimal("110000.00"),
            bonus_amount=Decimal("11000.00"),
            allowances_amount=Decimal("1100.00"),
            currency="USD",
            effective_from=date(2025, 1, 1),
            effective_to=None,
            revision_reason="Should fail",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_closed_then_open_is_allowed() -> None:
    session = _session()
    employee = _employee(session)
    session.add(
        SalaryRecord(
            employee_id=employee.id,
            base_amount=Decimal("100000.00"),
            bonus_amount=Decimal("10000.00"),
            allowances_amount=Decimal("1000.00"),
            currency="USD",
            effective_from=date(2023, 1, 1),
            effective_to=date(2023, 12, 31),
            revision_reason="Prior",
        )
    )
    session.add(
        SalaryRecord(
            employee_id=employee.id,
            base_amount=Decimal("110000.00"),
            bonus_amount=Decimal("11000.00"),
            allowances_amount=Decimal("1100.00"),
            currency="USD",
            effective_from=date(2024, 1, 1),
            effective_to=None,
            revision_reason="Current",
        )
    )
    session.commit()
    opens = session.query(SalaryRecord).filter(SalaryRecord.effective_to.is_(None)).count()
    assert opens == 1
