from typing import Any, Literal

from pydantic import BaseModel, Field

UiFn = Literal["barChart", "lineChart", "pieChart", "table", "navigateTo"]


class AskTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[AskTurn] = Field(default_factory=list, max_length=8)


class UiAction(BaseModel):
    fn: UiFn
    title: str = ""
    path: str | None = None
    x_key: str = "name"
    y_key: str = "value"
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AskResponse(BaseModel):
    say: str
    actions: list[UiAction]
    model: str | None = None
