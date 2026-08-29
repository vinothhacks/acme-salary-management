from __future__ import annotations

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import Department, Employee, SalaryRecord
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.salaries import create_open_salary, validate_currency

SORTABLE = {
    "employee_code": Employee.employee_code,
    "full_name": Employee.full_name,
    "country_code": Employee.country_code,
    "band": Employee.band,
    "hire_date": Employee.hire_date,
    "status": Employee.status,
}


def get_employee(session: Session, employee_id: int) -> Employee | None:
    return session.get(Employee, employee_id)


def list_employees(
    session: Session,
    *,
    page: int,
    page_size: int,
    q: str | None,
    country: str | None,
    department_id: int | None,
    band: str | None,
    status: str | None,
    sort: str,
) -> tuple[list[tuple[Employee, Department, SalaryRecord | None]], int]:
    descending = sort.startswith("-")
    key = sort.lstrip("-")
    column = SORTABLE.get(key, Employee.employee_code)
    current = aliased(SalaryRecord)
    filters = []
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Employee.full_name.ilike(like),
                Employee.employee_code.ilike(like),
                Employee.email.ilike(like),
            )
        )
    if country:
        filters.append(Employee.country_code == country.upper())
    if department_id:
        filters.append(Employee.department_id == department_id)
    if band:
        filters.append(Employee.band == band)
    if status:
        filters.append(Employee.status == status)

    base: Select[tuple[Employee]] = select(Employee)
    if filters:
        base = base.where(and_(*filters))
    total = int(session.scalar(select(func.count()).select_from(base.subquery())) or 0)

    query = (
        select(Employee, Department, current)
        .join(Department, Department.id == Employee.department_id)
        .outerjoin(
            current,
            and_(current.employee_id == Employee.id, current.effective_to.is_(None)),
        )
    )
    if filters:
        query = query.where(and_(*filters))
    query = query.order_by(column.desc() if descending else column.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = list(session.execute(query).all())
    return [(row[0], row[1], row[2]) for row in rows], total


def create_employee(session: Session, body: EmployeeCreate) -> Employee:
    validate_currency(session, body.salary.currency)
    if session.scalar(select(Employee.id).where(Employee.employee_code == body.employee_code)):
        raise ValueError("employee_code already exists")
    if session.scalar(select(Employee.id).where(Employee.email == str(body.email))):
        raise ValueError("email already exists")
    if session.get(Department, body.department_id) is None:
        raise ValueError("department not found")
    employee = Employee(
        employee_code=body.employee_code,
        full_name=body.full_name,
        email=str(body.email),
        country_code=body.country_code.upper(),
        department_id=body.department_id,
        job_title=body.job_title,
        band=body.band,
        employment_type=body.employment_type,
        hire_date=body.hire_date,
        status=body.status,
    )
    session.add(employee)
    session.flush()
    create_open_salary(session, employee.id, body.salary)
    session.commit()
    session.refresh(employee)
    return employee


def update_employee(session: Session, employee: Employee, body: EmployeeUpdate) -> Employee:
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])
    if "country_code" in data and data["country_code"] is not None:
        data["country_code"] = data["country_code"].upper()
    if "department_id" in data and data["department_id"] is not None:
        if session.get(Department, data["department_id"]) is None:
            raise ValueError("department not found")
    for key, value in data.items():
        setattr(employee, key, value)
    session.commit()
    session.refresh(employee)
    return employee


def current_salary(employee: Employee) -> SalaryRecord | None:
    for record in employee.salary_records:
        if record.effective_to is None:
            return record
    return None


