from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.models import Department, Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeDetail,
    EmployeeListItem,
    EmployeePage,
    EmployeeUpdate,
    ImportResult,
    PageMeta,
    SalaryOut,
    SalaryRevisionIn,
)
from app.services.employees import create_employee, get_employee, list_employees, update_employee
from app.services.imports import import_csv
from app.services.salaries import revise_salary

router = APIRouter(tags=["employees"])


def _item(employee: Employee, department: Department, salary: object) -> EmployeeListItem:
    current_base: Decimal | None = getattr(salary, "base_amount", None)
    current_currency: str | None = getattr(salary, "currency", None)
    return EmployeeListItem(
        id=employee.id,
        employee_code=employee.employee_code,
        full_name=employee.full_name,
        email=employee.email,
        country_code=employee.country_code,
        department_id=department.id,
        department_name=department.name,
        job_title=employee.job_title,
        band=employee.band,
        employment_type=employee.employment_type,
        hire_date=employee.hire_date,
        status=employee.status,
        current_base=current_base,
        current_currency=current_currency,
    )


@router.get("/departments")
def departments(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> list[dict[str, int | str]]:
    rows = session.scalars(select(Department).order_by(Department.name)).all()
    return [{"id": row.id, "name": row.name} for row in rows]


@router.post("/employees/import", response_model=ImportResult)
async def employees_import(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> ImportResult:
    raw = (await file.read()).decode("utf-8-sig")
    return import_csv(session, raw)


@router.get("/employees", response_model=EmployeePage)
def employees(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: str | None = None,
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = "employee_code",
) -> EmployeePage:
    rows, total = list_employees(
        session,
        page=page,
        page_size=page_size,
        q=q,
        country=country,
        department_id=department_id,
        band=band,
        status=status_filter,
        sort=sort,
    )
    items = [_item(employee, department, salary) for employee, department, salary in rows]
    return EmployeePage(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/employees/{employee_id}", response_model=EmployeeDetail)
def employee_detail(
    employee_id: int,
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> EmployeeDetail:
    employee = get_employee(session, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    department = session.get(Department, employee.department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    history = sorted(employee.salary_records, key=lambda row: row.effective_from, reverse=True)
    current = next((row for row in history if row.effective_to is None), None)
    item = _item(employee, department, current)
    return EmployeeDetail(
        **item.model_dump(),
        salary_history=[SalaryOut.model_validate(row) for row in history],
    )


@router.post("/employees", response_model=EmployeeDetail, status_code=status.HTTP_201_CREATED)
def employee_create(
    body: EmployeeCreate,
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> EmployeeDetail:
    try:
        employee = create_employee(session, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return employee_detail(employee.id, _, session)


@router.patch("/employees/{employee_id}", response_model=EmployeeDetail)
def employee_update(
    employee_id: int,
    body: EmployeeUpdate,
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> EmployeeDetail:
    employee = get_employee(session, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        update_employee(session, employee, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return employee_detail(employee_id, _, session)


@router.post("/employees/{employee_id}/salary-revisions", response_model=SalaryOut, status_code=201)
def salary_revision(
    employee_id: int,
    body: SalaryRevisionIn,
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> SalaryOut:
    if get_employee(session, employee_id) is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = revise_salary(session, employee_id, body)
    return SalaryOut.model_validate(record)
