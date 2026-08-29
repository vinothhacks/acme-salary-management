from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, func, literal, or_, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models import Department, Employee, FxRate, SalaryRecord

ZERO = Decimal("0.00")
BUCKET = Decimal("25000.00")


def _current_comp() -> Select[tuple[int, str, int, str, str, str, Decimal]]:
    local = SalaryRecord.base_amount + SalaryRecord.bonus_amount + SalaryRecord.allowances_amount
    usd = local * FxRate.rate_to_usd
    return (
        select(
            Employee.id.label("employee_id"),
            Employee.country_code.label("country_code"),
            Employee.department_id.label("department_id"),
            Department.name.label("department_name"),
            Employee.band.label("band"),
            Employee.status.label("status"),
            usd.label("usd_total"),
        )
        .join(
            SalaryRecord,
            and_(SalaryRecord.employee_id == Employee.id, SalaryRecord.effective_to.is_(None)),
        )
        .join(FxRate, FxRate.currency == SalaryRecord.currency)
        .join(Department, Department.id == Employee.department_id)
    )


def _apply_filters(
    stmt: Select[tuple[int, str, int, str, str, str, Decimal]],
    *,
    country: str | None,
    department_id: int | None,
    band: str | None,
    status: str | None,
) -> Select[tuple[int, str, int, str, str, str, Decimal]]:
    if country:
        stmt = stmt.where(Employee.country_code == country.upper())
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if band:
        stmt = stmt.where(Employee.band == band)
    if status:
        stmt = stmt.where(Employee.status == status)
    return stmt


def _median(session: Session, src: object) -> Decimal:
    dialect = session.get_bind().dialect.name
    amount = src.c.usd_total  # type: ignore[attr-defined]
    if dialect == "postgresql":
        value = session.scalar(select(func.percentile_cont(0.5).within_group(amount)))
        return Decimal(str(value or 0))
    ranked = select(
        amount.label("v"),
        func.row_number().over(order_by=amount).label("rn"),
        func.count().over().label("n"),
    ).subquery()
    target = func.round((ranked.c.n - 1) * 0.5) + 1
    value = session.scalar(select(ranked.c.v).where(ranked.c.rn == target))
    return Decimal(str(value or 0))


def _pick_expr(ranked: object, p: float) -> object:
    target = func.round((ranked.c.n - 1) * p) + 1  # type: ignore[attr-defined]
    return func.max(case((ranked.c.rn == target, ranked.c.v)))  # type: ignore[attr-defined]


def _grouped_percentiles(
    session: Session, source: Any, group_col: Any
) -> list[dict[str, object]]:
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        amount = source.c.usd_total
        stmt = (
            select(
                group_col,
                func.percentile_cont(0.10).within_group(amount),
                func.percentile_cont(0.25).within_group(amount),
                func.percentile_cont(0.50).within_group(amount),
                func.percentile_cont(0.75).within_group(amount),
                func.percentile_cont(0.90).within_group(amount),
                func.count(),
            )
            .group_by(group_col)
            .order_by(group_col)
        )
        return [
            {
                "key": str(row[0]),
                "p10": Decimal(str(row[1] or 0)),
                "p25": Decimal(str(row[2] or 0)),
                "p50": Decimal(str(row[3] or 0)),
                "p75": Decimal(str(row[4] or 0)),
                "p90": Decimal(str(row[5] or 0)),
                "headcount": int(row[6]),
            }
            for row in session.execute(stmt)
        ]

    ranked = select(
        group_col.label("g"),
        source.c.usd_total.label("v"),
        func.row_number().over(partition_by=group_col, order_by=source.c.usd_total).label("rn"),
        func.count().over(partition_by=group_col).label("n"),
    ).subquery()
    stmt = (
        select(
            ranked.c.g,
            _pick_expr(ranked, 0.10),
            _pick_expr(ranked, 0.25),
            _pick_expr(ranked, 0.50),
            _pick_expr(ranked, 0.75),
            _pick_expr(ranked, 0.90),
            func.max(ranked.c.n),
        )
        .group_by(ranked.c.g)
        .order_by(ranked.c.g)
    )
    return [
        {
            "key": str(row[0]),
            "p10": Decimal(str(row[1] or 0)),
            "p25": Decimal(str(row[2] or 0)),
            "p50": Decimal(str(row[3] or 0)),
            "p75": Decimal(str(row[4] or 0)),
            "p90": Decimal(str(row[5] or 0)),
            "headcount": int(row[6] or 0),
        }
        for row in session.execute(stmt)
    ]


def summary(
    session: Session,
    *,
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status: str | None = "active",
) -> dict[str, object]:
    src = _apply_filters(
        _current_comp(), country=country, department_id=department_id, band=band, status=status
    ).subquery()
    headcount = int(session.scalar(select(func.count()).select_from(src)) or 0)
    if headcount == 0:
        return {
            "headcount": 0,
            "total_annual_usd": ZERO,
            "mean_usd": ZERO,
            "median_usd": ZERO,
            "by_country": [],
            "by_department": [],
        }
    total = Decimal(str(session.scalar(select(func.coalesce(func.sum(src.c.usd_total), 0))) or 0))
    mean = Decimal(str(session.scalar(select(func.avg(src.c.usd_total))) or 0))
    median = _median(session, src)

    def breakdown(key_col: object) -> list[dict[str, object]]:
        stmt = (
            select(
                key_col,
                func.count(),
                func.coalesce(func.sum(src.c.usd_total), 0),
                func.avg(src.c.usd_total),
            )
            .group_by(key_col)
            .order_by(key_col)
        )
        return [
            {
                "key": str(row[0]),
                "headcount": int(row[1]),
                "total_usd": Decimal(str(row[2] or 0)),
                "mean_usd": Decimal(str(row[3] or 0)),
            }
            for row in session.execute(stmt)
        ]

    return {
        "headcount": headcount,
        "total_annual_usd": total,
        "mean_usd": mean,
        "median_usd": median,
        "by_country": breakdown(src.c.country_code),
        "by_department": breakdown(src.c.department_name),
    }


def distribution(
    session: Session,
    *,
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status: str | None = "active",
    bucket_size: Decimal = BUCKET,
) -> dict[str, object]:
    src = _apply_filters(
        _current_comp(), country=country, department_id=department_id, band=band, status=status
    ).subquery()
    bucket = func.floor(src.c.usd_total / bucket_size) * bucket_size
    stmt = select(bucket, func.count()).group_by(bucket).order_by(bucket)
    buckets = [
        {"bucket_usd": Decimal(str(row[0] or 0)), "count": int(row[1])}
        for row in session.execute(stmt)
    ]
    return {"bucket_size": bucket_size, "buckets": buckets}


def percentiles(
    session: Session,
    *,
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status: str | None = "active",
) -> dict[str, object]:
    src = _apply_filters(
        _current_comp(), country=country, department_id=department_id, band=band, status=status
    ).subquery()
    return {
        "by_band": _grouped_percentiles(session, src, src.c.band),
        "by_country": _grouped_percentiles(session, src, src.c.country_code),
    }


def cost_trend(session: Session, months: int = 24) -> dict[str, object]:
    today = date(2026, 8, 1)
    starts: list[date] = []
    year, month = today.year, today.month
    for _ in range(months):
        starts.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    starts.reverse()
    dates = union_all(*[select(literal(day).label("as_of")) for day in starts]).subquery("dates")
    local = SalaryRecord.base_amount + SalaryRecord.bonus_amount + SalaryRecord.allowances_amount
    active = (
        select(
            SalaryRecord.effective_from.label("effective_from"),
            SalaryRecord.effective_to.label("effective_to"),
            (local * FxRate.rate_to_usd).label("usd"),
        )
        .join(Employee, and_(Employee.id == SalaryRecord.employee_id, Employee.status == "active"))
        .join(FxRate, FxRate.currency == SalaryRecord.currency)
        .subquery("active_pay")
    )
    still_open = or_(active.c.effective_to.is_(None), active.c.effective_to >= dates.c.as_of)
    stmt = (
        select(dates.c.as_of, func.coalesce(func.sum(active.c.usd), 0))
        .select_from(dates)
        .outerjoin(
            active,
            and_(active.c.effective_from <= dates.c.as_of, still_open),
        )
        .group_by(dates.c.as_of)
        .order_by(dates.c.as_of)
    )
    return {
        "points": [
            {"as_of": row[0].isoformat(), "total_usd": Decimal(str(row[1] or 0))}
            for row in session.execute(stmt)
        ]
    }
