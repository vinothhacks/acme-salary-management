from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Department, Employee
from app.schemas.employee import ImportError, ImportResult, SalaryIn, SalaryRevisionIn
from app.services.employees import create_employee
from app.services.salaries import revise_salary, validate_currency

REQUIRED = [
    "employee_code",
    "full_name",
    "email",
    "country_code",
    "department",
    "job_title",
    "band",
    "employment_type",
    "hire_date",
    "base_amount",
    "currency",
    "effective_from",
]


def _date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def _money(value: str, field: str) -> Decimal:
    try:
        amount = Decimal(value.strip() or "0")
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not a number") from exc
    if amount < 0:
        raise ValueError(f"{field} must be zero or positive")
    return amount


def import_csv(session: Session, raw: str) -> ImportResult:
    reader = csv.DictReader(io.StringIO(raw))
    if reader.fieldnames is None:
        return ImportResult(created=0, revised=0, failed=1, errors=[
            ImportError(row=1, field=None, message="CSV has no header row")
        ])
    headers = [name.strip() for name in reader.fieldnames]
    missing = [col for col in REQUIRED if col not in headers]
    if missing:
        return ImportResult(
            created=0,
            revised=0,
            failed=1,
            errors=[
                ImportError(row=1, field=None, message=f"Missing columns: {', '.join(missing)}")
            ],
        )

    created = 0
    revised = 0
    errors: list[ImportError] = []
    departments = {row.name.lower(): row for row in session.scalars(select(Department))}

    for index, row in enumerate(reader, start=2):
        try:
            code = row["employee_code"].strip()
            dept_name = row["department"].strip()
            dept = departments.get(dept_name.lower())
            if dept is None:
                raise ValueError(f"unknown department '{dept_name}'")
            currency = validate_currency(session, row["currency"].strip())
            salary = SalaryIn(
                base_amount=_money(row["base_amount"], "base_amount"),
                bonus_amount=_money(row.get("bonus_amount", "0"), "bonus_amount"),
                allowances_amount=_money(row.get("allowances_amount", "0"), "allowances_amount"),
                currency=currency,
                effective_from=_date(row["effective_from"]),
                revision_reason=(row.get("revision_reason") or "").strip() or None,
            )
            existing = session.scalar(select(Employee).where(Employee.employee_code == code))
            if existing is None:
                from app.schemas.employee import EmployeeCreate

                create_employee(
                    session,
                    EmployeeCreate(
                        employee_code=code,
                        full_name=row["full_name"].strip(),
                        email=row["email"].strip(),
                        country_code=row["country_code"].strip(),
                        department_id=dept.id,
                        job_title=row["job_title"].strip(),
                        band=row["band"].strip(),
                        employment_type=row["employment_type"].strip(),
                        hire_date=_date(row["hire_date"]),
                        status=(row.get("status") or "active").strip() or "active",
                        salary=salary,
                    ),
                )
                created += 1
            else:
                if not salary.revision_reason:
                    raise ValueError("revision_reason is required when employee already exists")
                revise_salary(
                    session,
                    existing.id,
                    SalaryRevisionIn(
                        base_amount=salary.base_amount,
                        bonus_amount=salary.bonus_amount,
                        allowances_amount=salary.allowances_amount,
                        currency=salary.currency,
                        effective_from=salary.effective_from,
                        revision_reason=salary.revision_reason,
                    ),
                )
                revised += 1
        except Exception as exc:
            session.rollback()
            errors.append(ImportError(row=index, field=None, message=str(exc)))

    return ImportResult(created=created, revised=revised, failed=len(errors), errors=errors)
