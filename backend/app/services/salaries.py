from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FxRate, SalaryRecord
from app.schemas.employee import SalaryIn, SalaryRevisionIn
from app.schemas.money import KNOWN_CURRENCIES


def validate_currency(session: Session, code: str) -> str:
    currency = code.upper()
    seeded = session.get(FxRate, currency)
    if seeded is None and currency not in KNOWN_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown currency {currency}",
        )
    return currency


def open_salary(session: Session, employee_id: int) -> SalaryRecord | None:
    return session.scalar(
        select(SalaryRecord).where(
            SalaryRecord.employee_id == employee_id,
            SalaryRecord.effective_to.is_(None),
        )
    )


def create_open_salary(session: Session, employee_id: int, body: SalaryIn) -> SalaryRecord:
    currency = validate_currency(session, body.currency)
    record = SalaryRecord(
        employee_id=employee_id,
        base_amount=body.base_amount,
        bonus_amount=body.bonus_amount,
        allowances_amount=body.allowances_amount,
        currency=currency,
        effective_from=body.effective_from,
        effective_to=None,
        revision_reason=body.revision_reason,
    )
    session.add(record)
    session.flush()
    return record


def revise_salary(session: Session, employee_id: int, body: SalaryRevisionIn) -> SalaryRecord:
    currency = validate_currency(session, body.currency)
    current = open_salary(session, employee_id)
    if current is None:
        raise HTTPException(status_code=409, detail="Employee has no open salary record")
    if body.effective_from <= current.effective_from:
        raise HTTPException(
            status_code=409,
            detail="effective_from must be after the current record start",
        )
    close_on = body.effective_from - timedelta(days=1)
    if close_on < current.effective_from:
        raise HTTPException(status_code=409, detail="Revision overlaps the current interval")
    current.effective_to = close_on
    incoming = SalaryRecord(
        employee_id=employee_id,
        base_amount=body.base_amount,
        bonus_amount=body.bonus_amount,
        allowances_amount=body.allowances_amount,
        currency=currency,
        effective_from=body.effective_from,
        effective_to=None,
        revision_reason=body.revision_reason,
    )
    session.add(incoming)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(incoming)
    return incoming
