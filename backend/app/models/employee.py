from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.salary import SalaryRecord


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_country_code", "country_code"),
        Index("ix_employees_department_id", "department_id"),
        Index("ix_employees_full_name", "full_name"),
        Index("ix_employees_status", "status"),
        Index("ix_employees_band", "band"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(180), unique=True)
    country_code: Mapped[str] = mapped_column(String(2))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    job_title: Mapped[str] = mapped_column(String(120))
    band: Mapped[str] = mapped_column(String(8))
    employment_type: Mapped[str] = mapped_column(String(20))
    hire_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    department: Mapped[Department] = relationship("Department", back_populates="employees")
    salary_records: Mapped[list[SalaryRecord]] = relationship(
        "SalaryRecord", back_populates="employee", order_by="SalaryRecord.effective_from.desc()"
    )
