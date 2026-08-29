from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.seed import seed


def test_employees_require_auth(client: TestClient) -> None:
    assert client.get("/employees").status_code == 401


def test_list_search_filter_and_sort(auth_client: TestClient, session: Session) -> None:
    seed(session, count=12, reset=True)
    session.commit()
    page = auth_client.get("/employees", params={"page_size": 5, "sort": "employee_code"})
    assert page.status_code == 200
    body = page.json()
    assert body["meta"]["total"] == 12
    assert len(body["items"]) == 5
    assert body["items"][0]["employee_code"] == "ACME-00001"

    search = auth_client.get("/employees", params={"q": "ACME-00002"})
    assert search.json()["meta"]["total"] == 1

    country = auth_client.get("/employees", params={"country": "US"})
    assert country.json()["meta"]["total"] >= 1
    assert all(item["country_code"] == "US" for item in country.json()["items"])

    detail_id = body["items"][0]["id"]
    detail = auth_client.get(f"/employees/{detail_id}")
    assert detail.status_code == 200
    assert detail.json()["salary_history"]
    assert isinstance(detail.json()["current_base"], str)


def test_create_and_soft_delete(auth_client: TestClient, session: Session) -> None:
    seed(session, count=0, reset=True)
    session.commit()
    departments = auth_client.get("/departments").json()
    created = auth_client.post(
        "/employees",
        json={
            "employee_code": "ACME-NEW01",
            "full_name": "Test Person",
            "email": "test.person@acme.example",
            "country_code": "us",
            "department_id": departments[0]["id"],
            "job_title": "Analyst",
            "band": "IC2",
            "employment_type": "full_time",
            "hire_date": "2024-02-01",
            "salary": {
                "base_amount": "90000.00",
                "bonus_amount": "5000.00",
                "allowances_amount": "1000.00",
                "currency": "USD",
                "effective_from": "2024-02-01",
            },
        },
    )
    assert created.status_code == 201
    employee_id = created.json()["id"]
    patched = auth_client.patch(f"/employees/{employee_id}", json={"status": "inactive"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "inactive"
    still = auth_client.get(f"/employees/{employee_id}")
    assert still.json()["salary_history"]
    assert Decimal(still.json()["current_base"]) > 0
