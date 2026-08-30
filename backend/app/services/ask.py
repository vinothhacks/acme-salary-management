from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.ask import AskTurn, UiAction
from app.services import analytics as analytics_svc
from app.services.employees import list_employees

COUNTRIES = {"AE", "AU", "DE", "GB", "IN", "JP", "SG", "US"}
PATHS = {
    "/": "/",
    "dashboard": "/",
    "board": "/",
    "home": "/",
    "employees": "/employees",
    "import": "/import",
    "ask": "/ask",
    "/employees": "/employees",
    "/import": "/import",
    "/ask": "/ask",
}
OPENROUTER_MODELS = (
    "poolside/laguna-s-2.1:free",
    "openai/gpt-oss-20b",
    "mistralai/mistral-7b-instruct:free",
)
LLM_ERRORS = (
    urllib.error.HTTPError,
    urllib.error.URLError,
    KeyError,
    ValueError,
    json.JSONDecodeError,
)
SYSTEM = (
    "You are the ACME Salary HR assistant. Reply with JSON only. "
    "fn: barChart, lineChart, pieChart, table, navigateTo. "
    "source: distribution, by_country, by_department, percentiles_band, "
    "percentiles_country, cost_trend, employees, compare_countries. "
    "Use navigateTo with path /, /employees, or /import. Never invent numbers."
)


def _ui_chart(fn: str, title: str, rows: list[dict[str, Any]]) -> UiAction:
    chart: str = fn if fn in {"barChart", "pieChart"} else "barChart"
    return UiAction(fn=chart, title=title, rows=rows)  # type: ignore[arg-type]


def _num(value: object) -> float:
    return float(Decimal(str(value or 0)))


def _path(raw: str | None) -> str:
    if not raw:
        return "/"
    key = raw.strip().lower().rstrip("/")
    if key == "":
        return "/"
    return PATHS.get(key, PATHS.get("/" + key, "/"))


def _countries_in(text: str) -> list[str]:
    found = [code for code in COUNTRIES if re.search(rf"\b{code}\b", text.upper())]
    return list(dict.fromkeys(found))


def keyword_plan(message: str) -> dict[str, Any]:
    text = message.strip()
    lower = text.lower()
    actions: list[dict[str, Any]] = []
    navigating = bool(re.search(r"\b(go to|open|take me to|navigate)\b", lower))
    specific = False

    if re.search(r"\b(dashboard|board|home)\b", lower) and navigating:
        actions.append({"fn": "navigateTo", "path": "/"})
        specific = True
    elif re.search(r"\bemployees\b", lower) and navigating:
        actions.append({"fn": "navigateTo", "path": "/employees"})
        specific = True
    elif re.search(r"\bimport\b", lower) and navigating:
        actions.append({"fn": "navigateTo", "path": "/import"})
        specific = True

    codes = _countries_in(text)
    if re.search(r"\b(distribution|histogram|bucket|pay spread|spread of pay)\b", lower):
        actions.append(
            {
                "fn": "barChart",
                "source": "distribution",
                "metric": "count",
                "title": "Pay distribution",
                "country": codes[0] if len(codes) == 1 else None,
            }
        )
        say = "Pay distribution from current compensation rows."
        specific = True
    elif re.search(r"\b(trend|over time|cost over|history of cost)\b", lower):
        actions.append({"fn": "lineChart", "source": "cost_trend", "title": "Cost over time"})
        say = "Annual cost in USD over effective-dated history."
        specific = True
    elif re.search(r"\b(percentile|p10|p50|p90|by band)\b", lower):
        actions.append(
            {"fn": "table", "source": "percentiles_band", "title": "Percentiles by band"}
        )
        say = "Percentiles of current USD pay by band."
        specific = True
    elif re.search(r"\bpie\b", lower) or re.search(r"\bshare of (people|headcount)\b", lower):
        actions.append(
            {
                "fn": "pieChart",
                "source": "by_country",
                "metric": "headcount",
                "title": "Headcount by country",
            }
        )
        say = "Headcount share by country."
        specific = True
    elif len(codes) >= 2 or re.search(r"\b(vs|versus|compared?|compare)\b", lower):
        pair = codes[:2] if len(codes) >= 2 else ["IN", "US"]
        actions.append(
            {
                "fn": "barChart",
                "source": "compare_countries",
                "metric": "mean_usd",
                "countries": pair,
                "title": f"Mean USD: {' vs '.join(pair)}",
            }
        )
        say = f"Mean current pay in USD for {' and '.join(pair)}."
        specific = True
    elif re.search(r"\bdepartment\b", lower):
        actions.append(
            {
                "fn": "barChart",
                "source": "by_department",
                "metric": "mean_usd",
                "title": "Mean USD by department",
            }
        )
        say = "Mean current pay by department."
        specific = True
    elif re.search(r"\bemployee(s)? list\b|\bwho is in\b", lower):
        actions.append(
            {
                "fn": "table",
                "source": "employees",
                "title": "Employees",
                "country": codes[0] if codes else None,
            }
        )
        say = "First page of the employee list for that filter."
        specific = True
    elif navigating and actions:
        say = "Opening that page."
    else:
        country = codes[0] if len(codes) == 1 else None
        actions.append(
            {
                "fn": "barChart",
                "source": "by_country",
                "metric": "mean_usd",
                "title": "Mean USD by country" if not country else f"Mean USD ({country})",
                "country": country,
            }
        )
        say = (
            "Mean current pay in USD by country."
            if not country
            else f"Filtered view for {country}."
        )

    if not actions:
        actions.append(
            {
                "fn": "barChart",
                "source": "by_country",
                "metric": "mean_usd",
                "title": "Mean USD by country",
            }
        )
        say = "Mean current pay in USD by country."
    return {"say": say, "actions": actions, "specific": specific}


def _http_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("json not object")
    return parsed


def _complete_openrouter(key: str, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    data = _http_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"model": model, "messages": messages, "temperature": 0.1},
        {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://acme-salary-eight.vercel.app",
            "X-Title": "ACME Ask",
        },
    )
    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    parsed["_model"] = model
    return parsed


def _complete_mistral(key: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    data = _http_json(
        "https://api.mistral.ai/v1/chat/completions",
        {"model": "open-mistral-nemo", "messages": messages, "temperature": 0.1},
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    parsed["_model"] = "mistral/open-mistral-nemo"
    return parsed


def llm_plan(message: str, history: list[AskTurn], settings: Settings) -> dict[str, Any] | None:
    messages = [{"role": "system", "content": SYSTEM}]
    for turn in history[-6:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": message})
    if settings.openrouter_api_key:
        try:
            return _complete_openrouter(
                settings.openrouter_api_key, OPENROUTER_MODELS[0], messages
            )
        except LLM_ERRORS:
            pass
    if settings.mistral_api_key:
        try:
            return _complete_mistral(settings.mistral_api_key, messages)
        except LLM_ERRORS:
            return None
    return None


def _metric_rows(rows: list[dict[str, Any]], metric: str) -> list[dict[str, Any]]:
    key = metric if metric in {"headcount", "mean_usd", "total_usd", "count", "p50"} else "mean_usd"
    out: list[dict[str, Any]] = []
    for row in rows:
        value: object
        if key == "headcount":
            value = row.get("headcount", 0)
        elif key == "count":
            value = row.get("count", 0)
        elif key == "p50":
            value = row.get("p50", 0)
        elif key == "total_usd":
            value = row.get("total_usd", 0)
        else:
            value = row.get("mean_usd", 0)
        out.append({"name": str(row.get("key") or row.get("name") or ""), "value": _num(value)})
    return out


def hydrate(session: Session, plan: dict[str, Any]) -> tuple[str, list[UiAction], str | None]:
    say = str(plan.get("say") or "Here is what the ledger shows.")
    model = plan.get("_model")
    raw_actions = plan.get("actions") or []
    if isinstance(raw_actions, dict):
        raw_actions = [raw_actions]
    filled: list[UiAction] = []
    for item in raw_actions:
        if not isinstance(item, dict):
            continue
        fn = str(item.get("fn") or "barChart")
        if fn not in {"barChart", "lineChart", "pieChart", "table", "navigateTo"}:
            fn = "barChart"
        if fn == "navigateTo":
            filled.append(UiAction(fn="navigateTo", path=_path(str(item.get("path") or "/"))))
            continue
        source = str(item.get("source") or "by_country")
        metric = str(item.get("metric") or "mean_usd")
        country = item.get("country")
        country_s = str(country).upper() if country else None
        band = str(item["band"]) if item.get("band") else None
        countries = item.get("countries") or []
        if not isinstance(countries, list):
            countries = []
        codes = [str(c).upper() for c in countries if str(c).upper() in COUNTRIES]
        title = str(item.get("title") or source.replace("_", " "))
        status = "active"

        if source == "distribution":
            data = analytics_svc.distribution(session, country=country_s, band=band, status=status)
            buckets = data["buckets"] if isinstance(data["buckets"], list) else []
            rows = [
                {"name": str(row["bucket_usd"]), "value": int(row["count"])}  # type: ignore[index]
                for row in buckets
            ]
            filled.append(_ui_chart(fn, title, rows))
        elif source == "cost_trend":
            data = analytics_svc.cost_trend(session)
            points = data["points"] if isinstance(data["points"], list) else []
            rows = [{"name": str(row["as_of"]), "value": _num(row["total_usd"])} for row in points]  # type: ignore[index]
            filled.append(UiAction(fn="lineChart", title=title, rows=rows))
        elif source in {"percentiles_band", "percentiles_country"}:
            data = analytics_svc.percentiles(session, country=country_s, band=band, status=status)
            group = data["by_band"] if source == "percentiles_band" else data["by_country"]
            rows = []
            if isinstance(group, list):
                for row in group:
                    rows.append(
                        {
                            "name": str(row["key"]),
                            "p10": _num(row["p10"]),
                            "p25": _num(row["p25"]),
                            "p50": _num(row["p50"]),
                            "p75": _num(row["p75"]),
                            "p90": _num(row["p90"]),
                            "value": _num(row["p50"]),
                        }
                    )
            if fn == "table":
                filled.append(
                    UiAction(
                        fn="table",
                        title=title,
                        columns=["name", "p10", "p25", "p50", "p75", "p90"],
                        rows=rows,
                    )
                )
            else:
                filled.append(_ui_chart(fn, title, rows))
        elif source == "employees":
            pairs, _total = list_employees(
                session,
                page=1,
                page_size=15,
                q=None,
                country=country_s,
                department_id=None,
                band=band,
                status=status,
                sort="employee_code",
            )
            rows = []
            for employee, department, salary in pairs:
                rows.append(
                    {
                        "name": employee.employee_code,
                        "full_name": employee.full_name,
                        "country": employee.country_code,
                        "band": employee.band,
                        "department": department.name,
                        "base": "" if salary is None else str(salary.base_amount),
                    }
                )
            filled.append(
                UiAction(
                    fn="table",
                    title=title,
                    columns=["name", "full_name", "country", "band", "department", "base"],
                    rows=rows,
                )
            )
        else:
            summary = analytics_svc.summary(session, country=country_s, band=band, status=status)
            if source == "compare_countries" and codes:
                countries = summary["by_country"]
                by_country = countries if isinstance(countries, list) else []
                wanted = {row["key"]: row for row in by_country if str(row["key"]) in codes}  # type: ignore[index]
                selected = [wanted[code] for code in codes if code in wanted]
                rows = _metric_rows(selected, metric)  # type: ignore[arg-type]
                filled.append(_ui_chart(fn, title, rows))
            else:
                group = (
                    summary["by_department"] if source == "by_department" else summary["by_country"]
                )
                group_list = group if isinstance(group, list) else []
                rows = _metric_rows(group_list, metric)  # type: ignore[arg-type]
                filled.append(_ui_chart(fn, title, rows))
            if source == "by_country" and not any(a.fn == "table" for a in filled):
                say = f"{say} Headcount {summary['headcount']}, mean USD {summary['mean_usd']}."
    if not filled:
        filled.append(UiAction(fn="barChart", title="Mean USD by country", rows=[]))
    return say, filled, str(model) if model else None


def answer(
    session: Session,
    message: str,
    history: list[AskTurn],
    settings: Settings,
) -> tuple[str, list[UiAction], str | None]:
    plan = keyword_plan(message)
    if not plan.get("specific"):
        llm = llm_plan(message, history, settings)
        if llm is not None:
            plan = llm
    return hydrate(session, plan)
