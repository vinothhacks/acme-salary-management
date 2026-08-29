from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FxRate(Base):
    __tablename__ = "fx_rates"

    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    rate_to_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    as_of_date: Mapped[date] = mapped_column(Date)
