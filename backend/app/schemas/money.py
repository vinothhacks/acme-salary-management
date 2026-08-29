from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator

KNOWN_CURRENCIES = {"USD", "GBP", "INR", "EUR", "SGD", "AED", "AUD", "JPY"}


def as_money(value: Decimal) -> Decimal:
    if value < 0:
        raise ValueError("amount must be zero or positive")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


Money = Annotated[Decimal, AfterValidator(as_money)]


def money_json(value: Decimal) -> str:
    return f"{as_money(value):.2f}"
