from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.schemas.money import Money, money_json


class SalaryIn(BaseModel):
    base_amount: Money
    bonus_amount: Money = Decimal("0.00")
    allowances_amount: Money = Decimal("0.00")
    currency: str = Field(min_length=3, max_length=3)
    effective_from: date
    revision_reason: str | None = None

    @field_serializer("base_amount", "bonus_amount", "allowances_amount")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class SalaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base_amount: Decimal
    bonus_amount: Decimal
    allowances_amount: Decimal
    currency: str
    effective_from: date
    effective_to: date | None
    revision_reason: str | None
    created_at: datetime | None = None

    @field_serializer("base_amount", "bonus_amount", "allowances_amount")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=3, max_length=20)
    full_name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    country_code: str = Field(min_length=2, max_length=2)
    department_id: int
    job_title: str = Field(min_length=1, max_length=120)
    band: str = Field(min_length=2, max_length=8)
    employment_type: str = Field(pattern="^(full_time|part_time|contract)$")
    hire_date: date
    status: str = Field(default="active", pattern="^(active|inactive)$")
    salary: SalaryIn


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    department_id: int | None = None
    job_title: str | None = None
    band: str | None = None
    employment_type: str | None = Field(default=None, pattern="^(full_time|part_time|contract)$")
    status: str | None = Field(default=None, pattern="^(active|inactive)$")


class EmployeeListItem(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: str
    country_code: str
    department_id: int
    department_name: str
    job_title: str
    band: str
    employment_type: str
    hire_date: date
    status: str
    current_base: Decimal | None = None
    current_currency: str | None = None

    @field_serializer("current_base")
    def _money(self, value: Decimal | None) -> str | None:
        return None if value is None else money_json(value)


class EmployeeDetail(EmployeeListItem):
    salary_history: list[SalaryOut]


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class EmployeePage(BaseModel):
    items: list[EmployeeListItem]
    meta: PageMeta


class SalaryRevisionIn(BaseModel):
    base_amount: Money
    bonus_amount: Money = Decimal("0.00")
    allowances_amount: Money = Decimal("0.00")
    currency: str = Field(min_length=3, max_length=3)
    effective_from: date
    revision_reason: str = Field(min_length=3, max_length=500)

    @field_serializer("base_amount", "bonus_amount", "allowances_amount")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class ImportError(BaseModel):
    row: int
    field: str | None = None
    message: str


class ImportResult(BaseModel):
    created: int
    revised: int
    failed: int
    errors: list[ImportError]
