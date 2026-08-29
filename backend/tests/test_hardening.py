from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app
from app.services.seed import seed


def test_database_unavailable_returns_503(settings: Settings, engine: object) -> None:
    app = create_app(settings, engine=engine)  # type: ignore[arg-type]

    def boom() -> Session:
        raise OperationalError("SELECT 1", {}, Exception("down"))

    app.state.session_factory = boom  # type: ignore[assignment]
    client = TestClient(app)
    client.post("/auth/login", json={"email": settings.hr_email, "password": settings.hr_password})
    response = client.get("/employees")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"


def test_hostile_inputs_do_not_500(auth_client: TestClient) -> None:
    assert auth_client.get("/employees", params={"page_size": 9999}).status_code == 422
    bad_login = auth_client.post("/auth/login", json={"email": "not-an-email", "password": "x"})
    assert bad_login.status_code == 422
    assert (
        auth_client.post(
            "/employees",
            json={
                "employee_code": "<script>alert(1)</script>",
                "full_name": "x" * 400,
                "email": "bad",
                "country_code": "USA",
                "department_id": 1,
                "job_title": "Dev",
                "band": "IC2",
                "employment_type": "full_time",
                "hire_date": "2020-01-01",
                "salary": {
                    "base_amount": "-1",
                    "bonus_amount": "0",
                    "allowances_amount": "0",
                    "currency": "USD",
                    "effective_from": "2020-01-01",
                },
            },
        ).status_code
        == 422
    )
    binary = auth_client.post(
        "/employees/import",
        files={"file": ("x.bin", b"\xff\xfe\x00\x01", "application/octet-stream")},
    )
    assert binary.status_code == 400


def test_list_and_detail_are_constant_query(
    auth_client: TestClient, session: Session, engine: object
) -> None:
    seed(session, count=20, reset=True)
    session.commit()
    statements: list[str] = []

    def before_cursor(
        _conn: object, _cursor: object, statement: str, *_args: object, **_kwargs: object
    ) -> None:
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor)
    try:
        listing = auth_client.get("/employees", params={"page_size": 10})
        list_count = len(statements)
        statements.clear()
        detail_id = listing.json()["items"][0]["id"]
        auth_client.get(f"/employees/{detail_id}")
        detail_count = len(statements)
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor)

    assert listing.status_code == 200
    assert list_count <= 4
    assert detail_count <= 4
