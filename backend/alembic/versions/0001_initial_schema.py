"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_departments_name", "departments", ["name"])

    op.create_table(
        "fx_rates",
        sa.Column("currency", sa.String(3), primary_key=True),
        sa.Column("rate_to_usd", sa.Numeric(18, 8), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_code", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(180), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("job_title", sa.String(120), nullable=False),
        sa.Column("band", sa.String(8), nullable=False),
        sa.Column("employment_type", sa.String(20), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("employee_code"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_employees_country_code", "employees", ["country_code"])
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_index("ix_employees_full_name", "employees", ["full_name"])
    op.create_index("ix_employees_status", "employees", ["status"])
    op.create_index("ix_employees_band", "employees", ["band"])

    op.create_table(
        "salary_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("base_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("bonus_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("allowances_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("revision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_salary_records_employee_id", "salary_records", ["employee_id"])
    op.create_index("ix_salary_employee_effective", "salary_records", ["employee_id", "effective_to"])
    op.execute(
        "CREATE UNIQUE INDEX uq_one_open_salary ON salary_records (employee_id) "
        "WHERE effective_to IS NULL"
    )


def downgrade() -> None:
    op.drop_index("uq_one_open_salary", table_name="salary_records")
    op.drop_index("ix_salary_employee_effective", table_name="salary_records")
    op.drop_index("ix_salary_records_employee_id", table_name="salary_records")
    op.drop_table("salary_records")
    op.drop_index("ix_employees_band", table_name="employees")
    op.drop_index("ix_employees_status", table_name="employees")
    op.drop_index("ix_employees_full_name", table_name="employees")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_index("ix_employees_country_code", table_name="employees")
    op.drop_table("employees")
    op.drop_table("fx_rates")
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("departments")
