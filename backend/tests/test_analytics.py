from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Department, Employee, FxRate, SalaryRecord


def _fixture(session: Session) -> None:
    session.add_all(
        [
            FxRate(currency="USD", rate_to_usd=Decimal("1.00000000"), as_of_date=date(2026, 1, 1)),
            FxRate(currency="GBP", rate_to_usd=Decimal("2.00000000"), as_of_date=date(2026, 1, 1)),
        ]
    )
    eng = Department(name="Engineering")
    product = Department(name="Product")
    sales = Department(name="Sales")
    session.add_all([eng, product, sales])
    session.flush()

    people = [
        ("E1", "US", eng.id, "IC3", Decimal("100000.00"), "USD", date(2022, 1, 1)),
        ("E2", "US", eng.id, "IC3", Decimal("200000.00"), "USD", date(2022, 1, 1)),
        ("E3", "GB", product.id, "IC3", Decimal("50000.00"), "GBP", date(2022, 1, 1)),
        ("E4", "US", sales.id, "IC5", Decimal("300000.00"), "USD", date(2025, 6, 1)),
    ]
    for code, country, dept_id, band, base, currency, start in people:
        employee = Employee(
            employee_code=code,
            full_name=code,
            email=f"{code.lower()}@acme.example",
            country_code=country,
            department_id=dept_id,
            job_title="Role",
            band=band,
            employment_type="full_time",
            hire_date=start,
            status="active",
        )
        session.add(employee)
        session.flush()
        session.add(
            SalaryRecord(
                employee_id=employee.id,
                base_amount=base,
                bonus_amount=Decimal("0.00"),
                allowances_amount=Decimal("0.00"),
                currency=currency,
                effective_from=start,
                effective_to=None,
                revision_reason=None,
            )
        )
    ghost = Employee(
        employee_code="E5",
        full_name="Inactive",
        email="e5@acme.example",
        country_code="US",
        department_id=eng.id,
        job_title="Role",
        band="IC3",
        employment_type="full_time",
        hire_date=date(2022, 1, 1),
        status="inactive",
    )
    session.add(ghost)
    session.flush()
    session.add(
        SalaryRecord(
            employee_id=ghost.id,
            base_amount=Decimal("999999.00"),
            bonus_amount=Decimal("0.00"),
            allowances_amount=Decimal("0.00"),
            currency="USD",
            effective_from=date(2022, 1, 1),
            effective_to=None,
            revision_reason=None,
        )
    )
    session.commit()


def test_summary_fx_and_median(auth_client: TestClient, session: Session) -> None:
    _fixture(session)
    body = auth_client.get("/analytics/summary").json()
    assert body["headcount"] == 4
    assert body["total_annual_usd"] == "700000.00"
    assert body["mean_usd"] == "175000.00"
    assert body["median_usd"] == "200000.00"
    us = next(row for row in body["by_country"] if row["key"] == "US")
    assert us["headcount"] == 3
    assert us["total_usd"] == "600000.00"


def test_percentiles_match_hand_computed(auth_client: TestClient, session: Session) -> None:
    _fixture(session)
    body = auth_client.get("/analytics/percentiles").json()
    ic3 = next(row for row in body["by_band"] if row["key"] == "IC3")
    assert ic3["headcount"] == 3
    assert ic3["p10"] == "100000.00"
    assert ic3["p50"] == "100000.00"
    assert ic3["p90"] == "200000.00"
    us = next(row for row in body["by_country"] if row["key"] == "US")
    assert us["p10"] == "100000.00"
    assert us["p50"] == "200000.00"
    assert us["p90"] == "300000.00"


def test_distribution_and_empty_filter(auth_client: TestClient, session: Session) -> None:
    _fixture(session)
    dist = auth_client.get("/analytics/distribution").json()
    counts = {row["bucket_usd"]: row["count"] for row in dist["buckets"]}
    assert counts["100000.00"] == 2
    assert counts["200000.00"] == 1
    assert counts["300000.00"] == 1
    empty = auth_client.get("/analytics/summary", params={"country": "ZZ"}).json()
    assert empty["headcount"] == 0
    assert empty["total_annual_usd"] == "0.00"


def test_cost_trend_respects_effective_dates(auth_client: TestClient, session: Session) -> None:
    _fixture(session)
    trend = auth_client.get("/analytics/cost-trend").json()
    points = {row["as_of"]: row["total_usd"] for row in trend["points"]}
    assert points["2024-09-01"] == "400000.00"
    assert points["2026-08-01"] == "700000.00"
