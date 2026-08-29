from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.seed import seed

HEADER = (
    "employee_code,full_name,email,country_code,department,job_title,band,"
    "employment_type,hire_date,base_amount,bonus_amount,allowances_amount,"
    "currency,effective_from,revision_reason,status\n"
)


def test_import_mixed_rows(auth_client: TestClient, session: Session) -> None:
    seed(session, count=0, reset=True)
    session.commit()
    csv = HEADER + (
        "ACME-IMP01,New Hire,new.hire@acme.example,US,Engineering,Analyst,IC2,"
        "full_time,2024-03-01,80000,4000,0,USD,2024-03-01,,active\n"
        "ACME-BAD,Nope,nope@acme.example,US,NotADept,Analyst,IC2,"
        "full_time,2024-03-01,-5,0,0,USD,2024-03-01,,active\n"
        "ACME-BAD2,Nope2,nope2@acme.example,US,Engineering,Analyst,IC2,"
        "full_time,2024-03-01,10,0,0,ZZZ,2024-03-01,,active\n"
    )
    response = auth_client.post(
        "/employees/import",
        files={"file": ("hire.csv", csv, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["failed"] == 2
    listing = auth_client.get("/employees", params={"q": "ACME-IMP01"})
    assert listing.json()["meta"]["total"] == 1
