from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Department, Employee, FxRate, SalaryRecord
from app.services.ask import keyword_plan


def _seed(session: Session) -> None:
    session.add(FxRate(currency="USD", rate_to_usd=Decimal("1"), as_of_date=date(2026, 1, 1)))
    eng = Department(name="Engineering")
    session.add(eng)
    session.flush()
    person = Employee(
        employee_code="E1",
        full_name="Ada",
        email="e1@acme.example",
        country_code="US",
        department_id=eng.id,
        job_title="Role",
        band="IC3",
        employment_type="full_time",
        hire_date=date(2022, 1, 1),
        status="active",
    )
    session.add(person)
    session.flush()
    session.add(
        SalaryRecord(
            employee_id=person.id,
            base_amount=Decimal("100000.00"),
            bonus_amount=Decimal("0.00"),
            allowances_amount=Decimal("0.00"),
            currency="USD",
            effective_from=date(2022, 1, 1),
            effective_to=None,
            revision_reason=None,
        )
    )
    session.commit()


def test_ask_requires_login(client: TestClient) -> None:
    assert client.post("/ask/chat", json={"message": "go to dashboard"}).status_code == 401


def test_keyword_go_to_dashboard() -> None:
    plan = keyword_plan("go to the dashboard")
    assert plan["actions"][0]["fn"] == "navigateTo"
    assert plan["actions"][0]["path"] == "/"


def test_ask_navigates_to_dashboard(auth_client: TestClient, session: Session) -> None:
    _seed(session)
    body = auth_client.post("/ask/chat", json={"message": "please go to dashboard"}).json()
    assert body["actions"][0]["fn"] == "navigateTo"
    assert body["actions"][0]["path"] == "/"


def test_ask_compare_countries_bar(auth_client: TestClient, session: Session) -> None:
    _seed(session)
    body = auth_client.post("/ask/chat", json={"message": "mean pay IN vs US"}).json()
    chart = next(row for row in body["actions"] if row["fn"] == "barChart")
    names = {row["name"] for row in chart["rows"]}
    assert "US" in names


def test_ask_distribution_bar(auth_client: TestClient, session: Session) -> None:
    _seed(session)
    body = auth_client.post("/ask/chat", json={"message": "show the pay distribution"}).json()
    chart = body["actions"][0]
    assert chart["fn"] == "barChart"
    assert chart["rows"]
