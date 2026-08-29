from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.seed import seed


def test_negative_salary_rejected(auth_client: TestClient, session: Session) -> None:
    seed(session, count=0, reset=True)
    session.commit()
    dept_id = auth_client.get("/departments").json()[0]["id"]
    response = auth_client.post(
        "/employees",
        json={
            "employee_code": "ACME-NEG01",
            "full_name": "Neg Person",
            "email": "neg.person@acme.example",
            "country_code": "US",
            "department_id": dept_id,
            "job_title": "Analyst",
            "band": "IC1",
            "employment_type": "full_time",
            "hire_date": "2024-01-01",
            "salary": {
                "base_amount": "-10.00",
                "currency": "USD",
                "effective_from": "2024-01-01",
            },
        },
    )
    assert response.status_code == 422


def test_unknown_currency_rejected(auth_client: TestClient, session: Session) -> None:
    seed(session, count=0, reset=True)
    session.commit()
    dept_id = auth_client.get("/departments").json()[0]["id"]
    response = auth_client.post(
        "/employees",
        json={
            "employee_code": "ACME-CUR01",
            "full_name": "Cur Person",
            "email": "cur.person@acme.example",
            "country_code": "US",
            "department_id": dept_id,
            "job_title": "Analyst",
            "band": "IC1",
            "employment_type": "full_time",
            "hire_date": "2024-01-01",
            "salary": {
                "base_amount": "10.00",
                "currency": "ZZZ",
                "effective_from": "2024-01-01",
            },
        },
    )
    assert response.status_code == 422


def test_health_still_public(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
