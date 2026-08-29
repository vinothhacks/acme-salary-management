from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.schemas.analytics import (
    CostTrendResponse,
    DistributionResponse,
    PercentilesResponse,
    SummaryResponse,
)
from app.services import analytics as svc

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryResponse)
def summary(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status_filter: str | None = Query(default="active", alias="status"),
) -> SummaryResponse:
    return SummaryResponse.model_validate(
        svc.summary(
            session, country=country, department_id=department_id, band=band, status=status_filter
        )
    )


@router.get("/distribution", response_model=DistributionResponse)
def distribution(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status_filter: str | None = Query(default="active", alias="status"),
) -> DistributionResponse:
    return DistributionResponse.model_validate(
        svc.distribution(
            session, country=country, department_id=department_id, band=band, status=status_filter
        )
    )


@router.get("/percentiles", response_model=PercentilesResponse)
def percentiles(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    country: str | None = None,
    department_id: int | None = None,
    band: str | None = None,
    status_filter: str | None = Query(default="active", alias="status"),
) -> PercentilesResponse:
    return PercentilesResponse.model_validate(
        svc.percentiles(
            session, country=country, department_id=department_id, band=band, status=status_filter
        )
    )


@router.get("/cost-trend", response_model=CostTrendResponse)
def cost_trend(
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
) -> CostTrendResponse:
    return CostTrendResponse.model_validate(svc.cost_trend(session))
