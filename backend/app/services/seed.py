from __future__ import annotations

import hashlib
import math
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.models import Department, Employee, FxRate, SalaryRecord

RNG_SEED = 42
DEFAULT_COUNT = 10_000

COUNTRIES: list[tuple[str, str, Decimal]] = [
    ("US", "USD", Decimal("1.00000000")),
    ("GB", "GBP", Decimal("1.27000000")),
    ("IN", "INR", Decimal("0.01200000")),
    ("DE", "EUR", Decimal("1.08000000")),
    ("SG", "SGD", Decimal("0.74000000")),
    ("AE", "AED", Decimal("0.27200000")),
    ("AU", "AUD", Decimal("0.65000000")),
    ("JP", "JPY", Decimal("0.00670000")),
]

DEPARTMENTS = [
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Finance",
    "People",
    "Operations",
    "Legal",
    "Support",
]

BANDS = ["IC1", "IC2", "IC3", "IC4", "IC5", "IC6", "M1", "M2", "M3"]
BAND_MULT = {
    "IC1": 0.55,
    "IC2": 0.75,
    "IC3": 1.00,
    "IC4": 1.30,
    "IC5": 1.70,
    "IC6": 2.20,
    "M1": 1.50,
    "M2": 2.00,
    "M3": 2.70,
}
# log(typical IC3 annual base) in local currency
COUNTRY_MU = {
    "US": math.log(125_000),
    "GB": math.log(72_000),
    "IN": math.log(2_200_000),
    "DE": math.log(78_000),
    "SG": math.log(115_000),
    "AE": math.log(290_000),
    "AU": math.log(135_000),
    "JP": math.log(8_400_000),
}
TITLES = {
    "IC1": "Associate",
    "IC2": "Specialist",
    "IC3": "Senior Specialist",
    "IC4": "Staff",
    "IC5": "Principal",
    "IC6": "Distinguished",
    "M1": "Manager",
    "M2": "Senior Manager",
    "M3": "Director",
}
FIRST_NAMES = [
    "Ada", "Amir", "Amina", "Anika", "Carlos", "Chen", "Diego", "Elena", "Farah", "Grace",
    "Hiro", "Imani", "Jonas", "Kai", "Leila", "Mateo", "Nadia", "Omar", "Priya", "Quinn",
    "Ravi", "Sofia", "Tariq", "Uma", "Viktor", "Wei", "Yara", "Zane", "Nora", "Luca",
    "Mei", "Noor", "Pavel", "Rosa", "Soren", "Tessa",
]
LAST_NAMES = [
    "Abebe", "Alvarez", "Berg", "Chaudhary", "Diaz", "Ekene", "Fujimoto", "Garcia",
    "Hassan", "Ivanov", "Jansen", "Khan", "Lopez", "Mwangi", "Nguyen", "Okoye",
    "Patel", "Qureshi", "Rahman", "Silva", "Tanaka", "Ueda", "Varga", "Wright",
    "Xu", "Young", "Zhang", "Costa", "Dubois", "Eriksson",
]
EMPLOYMENT = ["full_time", "full_time", "full_time", "full_time", "part_time", "contract"]
AS_OF = date(2026, 1, 1)


def money(value: float) -> Decimal:
    return Decimal(str(round(value, 2))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dataset_checksum(session: Session) -> str:
    digest = hashlib.sha256()
    emp_stmt = select(
        Employee.employee_code,
        Employee.full_name,
        Employee.email,
        Employee.country_code,
        Employee.band,
        Employee.status,
    ).order_by(Employee.employee_code)
    for emp_row in session.execute(emp_stmt).all():
        digest.update("|".join(str(part) for part in emp_row).encode())
    sal_stmt = select(
        SalaryRecord.employee_id,
        SalaryRecord.base_amount,
        SalaryRecord.currency,
        SalaryRecord.effective_from,
        SalaryRecord.effective_to,
    ).order_by(SalaryRecord.employee_id, SalaryRecord.effective_from, SalaryRecord.id)
    for sal_row in session.execute(sal_stmt).all():
        digest.update("|".join("" if part is None else str(part) for part in sal_row).encode())
    return digest.hexdigest()


def reset_tables(session: Session) -> None:
    session.execute(delete(SalaryRecord))
    session.execute(delete(Employee))
    session.execute(delete(Department))
    session.execute(delete(FxRate))
    session.flush()


def _pay(rng: random.Random, country: str, band: str) -> tuple[Decimal, Decimal, Decimal]:
    mu = COUNTRY_MU[country] + math.log(BAND_MULT[band])
    base = money(math.exp(rng.gauss(mu, 0.18)))
    bonus = money(float(base) * rng.uniform(0.08, 0.22))
    allowances = money(float(base) * rng.uniform(0.0, 0.08))
    return base, bonus, allowances


def seed(session: Session, *, count: int = DEFAULT_COUNT, reset: bool = False) -> dict[str, Any]:
    rng = random.Random(RNG_SEED)
    if reset:
        reset_tables(session)

    for _country, currency, rate in COUNTRIES:
        session.merge(FxRate(currency=currency, rate_to_usd=rate, as_of_date=AS_OF))
    session.flush()

    existing = session.scalar(select(func.count()).select_from(Department)) or 0
    if existing == 0:
        session.add_all([Department(name=name) for name in DEPARTMENTS])
        session.flush()
    departments = list(session.scalars(select(Department).order_by(Department.id)))

    employees: list[Employee] = []
    for i in range(1, count + 1):
        country, currency, _rate = COUNTRIES[(i - 1) % len(COUNTRIES)]
        dept = departments[(i - 1) % len(departments)]
        band = BANDS[(i + rng.randrange(0, 3)) % len(BANDS)]
        first = FIRST_NAMES[(i + rng.randrange(0, len(FIRST_NAMES))) % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 7 + rng.randrange(0, len(LAST_NAMES))) % len(LAST_NAMES)]
        hire = date(2014, 1, 1) + timedelta(days=rng.randrange(0, 365 * 11))
        status = "inactive" if rng.random() < 0.06 else "active"
        employee = Employee(
            employee_code=f"ACME-{i:05d}",
            full_name=f"{first} {last}",
            email=f"{first.lower()}.{last.lower()}.{i}@acme.test",
            country_code=country,
            department_id=dept.id,
            job_title=f"{TITLES[band]} {dept.name.rstrip('s')}",
            band=band,
            employment_type=EMPLOYMENT[rng.randrange(len(EMPLOYMENT))],
            hire_date=hire,
            status=status,
        )
        employees.append(employee)
    session.add_all(employees)
    session.flush()

    salaries: list[SalaryRecord] = []
    for employee in employees:
        currency = next(cur for code, cur, _ in COUNTRIES if code == employee.country_code)
        revisions = 1
        if rng.random() < 0.30:
            revisions = rng.randint(2, 4)
        start = employee.hire_date
        for rev in range(revisions):
            base, bonus, allowances = _pay(rng, employee.country_code, employee.band)
            is_last = rev == revisions - 1
            if is_last:
                effective_to = None
                effective_from = start
                reason = None if revisions == 1 else "Annual compensation review"
            else:
                span = rng.randint(180, 500)
                effective_from = start
                effective_to = start + timedelta(days=span)
                start = effective_to + timedelta(days=1)
                reason = "Market adjustment" if rev == 0 else "Promotion / band refresh"
            salaries.append(
                SalaryRecord(
                    employee_id=employee.id,
                    base_amount=base,
                    bonus_amount=bonus,
                    allowances_amount=allowances,
                    currency=currency,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    revision_reason=reason,
                )
            )
    session.add_all(salaries)
    session.flush()

    return {
        "employees": len(employees),
        "departments": len(departments),
        "salary_records": len(salaries),
        "fx_rates": len(COUNTRIES),
        "checksum": dataset_checksum(session),
    }


def verify_counts(session: Session) -> dict[str, int]:
    return {
        "employees": int(session.scalar(select(func.count()).select_from(Employee)) or 0),
        "departments": int(session.scalar(select(func.count()).select_from(Department)) or 0),
        "salary_records": int(session.scalar(select(func.count()).select_from(SalaryRecord)) or 0),
        "open_salaries": int(
            session.scalar(
                select(func.count()).select_from(SalaryRecord).where(SalaryRecord.effective_to.is_(None))
            )
            or 0
        ),
        "fx_rates": int(session.scalar(select(func.count()).select_from(FxRate)) or 0),
    }


def sqlite_integrity(session: Session) -> None:
    """Ensure SQLite actually enforces the partial unique index during tests."""
    session.execute(text("PRAGMA foreign_keys=ON"))
