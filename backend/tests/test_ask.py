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
    assert plan["specific"] is True


INTENTS = [
    ("go to dashboard", "navigateTo"),
    ("go to the dashboard", "navigateTo"),
    ("go to employees", "navigateTo"),
    ("go to import", "navigateTo"),
    ("pay distribution", "barChart"),
    ("mean pay IN vs US", "barChart"),
    ("cost over time", "lineChart"),
    ("percentiles by band", "table"),
    ("share of headcount", "pieChart"),
    ("mean pay by department", "barChart"),
]


def test_ten_intents_are_specific() -> None:
    for message, fn in INTENTS:
        plan = keyword_plan(message)
        assert plan["specific"] is True, message
        assert plan["actions"][0]["fn"] == fn, message


def test_ask_navigates_to_dashboard(auth_client: TestClient, session: Session) -> None:
    _seed(session)
    body = auth_client.post("/ask/chat", json={"message": "please go to dashboard"}).json()
    assert body["actions"][0]["fn"] == "navigateTo"
    assert body["actions"][0]["path"] == "/"


def test_specific_intents_skip_llm(
    auth_client: TestClient, session: Session, monkeypatch: object
) -> None:
    _seed(session)

    def boom(*_a: object, **_k: object) -> dict:
        raise AssertionError("llm should not run for known intents")

    monkeypatch.setattr("app.services.ask.llm_plan", boom)
    history = [
        {"role": "user", "content": "mean pay IN vs US"},
        {"role": "assistant", "content": "Here is what the ledger shows."},
    ]
    for message, fn in INTENTS:
        body = auth_client.post(
            "/ask/chat", json={"message": message, "history": history}
        ).json()
        assert body["actions"][0]["fn"] == fn, message
        if fn == "navigateTo":
            assert body["actions"][0]["path"] in {"/", "/employees", "/import"}
        else:
            assert body["actions"][0]["rows"]


def test_pay_distribution_after_compare_history(
    auth_client: TestClient, session: Session, monkeypatch: object
) -> None:
    _seed(session)
    monkeypatch.setattr(
        "app.services.ask.llm_plan",
        lambda *_a, **_k: {
            "say": "Here is what the ledger shows.",
            "actions": [{"fn": "barChart", "source": "by_country", "title": "Mean USD by country"}],
        },
    )
    body = auth_client.post(
        "/ask/chat",
        json={
            "message": "pay distribution",
            "history": [
                {"role": "user", "content": "mean pay IN vs US"},
                {"role": "assistant", "content": "Here is what the ledger shows."},
            ],
        },
    ).json()
    assert body["actions"][0]["title"] == "Pay distribution"

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
