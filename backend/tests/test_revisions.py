from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.seed import seed


def _create(auth_client: TestClient, session: Session) -> int:
    seed(session, count=0, reset=True)
    session.commit()
    dept_id = auth_client.get("/departments").json()[0]["id"]
    created = auth_client.post(
        "/employees",
        json={
            "employee_code": "ACME-REV01",
            "full_name": "Rev Person",
            "email": "rev.person@acme.example",
            "country_code": "US",
            "department_id": dept_id,
            "job_title": "Analyst",
            "band": "IC3",
            "employment_type": "full_time",
            "hire_date": "2022-01-01",
            "salary": {
                "base_amount": "100000.00",
                "bonus_amount": "10000.00",
                "allowances_amount": "0.00",
                "currency": "USD",
                "effective_from": "2022-01-01",
            },
        },
    )
    assert created.status_code == 201
    return int(created.json()["id"])


def test_revision_happy_path(auth_client: TestClient, session: Session) -> None:
    employee_id = _create(auth_client, session)
    revised = auth_client.post(
        f"/employees/{employee_id}/salary-revisions",
        json={
            "base_amount": "120000.00",
            "bonus_amount": "15000.00",
            "allowances_amount": "2000.00",
            "currency": "USD",
            "effective_from": "2024-01-01",
            "revision_reason": "Annual compensation review",
        },
    )
    assert revised.status_code == 201
    detail = auth_client.get(f"/employees/{employee_id}").json()
    assert len(detail["salary_history"]) == 2
    assert detail["current_base"] == "120000.00"
    closed = [row for row in detail["salary_history"] if row["effective_to"] is not None]
    assert closed[0]["effective_to"] == "2023-12-31"


def test_revision_overlap_rejected(auth_client: TestClient, session: Session) -> None:
    employee_id = _create(auth_client, session)
    response = auth_client.post(
        f"/employees/{employee_id}/salary-revisions",
        json={
            "base_amount": "110000.00",
            "bonus_amount": "0.00",
            "allowances_amount": "0.00",
            "currency": "USD",
            "effective_from": "2021-06-01",
            "revision_reason": "Too early",
        },
    )
    assert response.status_code == 409
    detail = auth_client.get(f"/employees/{employee_id}").json()
    assert len(detail["salary_history"]) == 1


def test_revision_requires_reason(auth_client: TestClient, session: Session) -> None:
    employee_id = _create(auth_client, session)
    response = auth_client.post(
        f"/employees/{employee_id}/salary-revisions",
        json={
            "base_amount": "110000.00",
            "currency": "USD",
            "effective_from": "2024-01-01",
            "revision_reason": "",
        },
    )
    assert response.status_code == 422
