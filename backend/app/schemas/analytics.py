from decimal import Decimal

from pydantic import BaseModel, field_serializer

from app.schemas.money import money_json


class MoneyStat(BaseModel):
    value: Decimal

    @field_serializer("value")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class BreakdownRow(BaseModel):
    key: str
    headcount: int
    total_usd: Decimal
    mean_usd: Decimal

    @field_serializer("total_usd", "mean_usd")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class SummaryResponse(BaseModel):
    headcount: int
    total_annual_usd: Decimal
    mean_usd: Decimal
    median_usd: Decimal
    by_country: list[BreakdownRow]
    by_department: list[BreakdownRow]

    @field_serializer("total_annual_usd", "mean_usd", "median_usd")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class Bucket(BaseModel):
    bucket_usd: Decimal
    count: int

    @field_serializer("bucket_usd")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class DistributionResponse(BaseModel):
    bucket_size: Decimal
    buckets: list[Bucket]


class PercentileRow(BaseModel):
    key: str
    p10: Decimal
    p25: Decimal
    p50: Decimal
    p75: Decimal
    p90: Decimal
    headcount: int

    @field_serializer("p10", "p25", "p50", "p75", "p90")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class PercentilesResponse(BaseModel):
    by_band: list[PercentileRow]
    by_country: list[PercentileRow]


class TrendPoint(BaseModel):
    as_of: str
    total_usd: Decimal

    @field_serializer("total_usd")
    def _money(self, value: Decimal) -> str:
        return money_json(value)


class CostTrendResponse(BaseModel):
    points: list[TrendPoint]
