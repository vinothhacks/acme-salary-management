from typing import Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from starlette.middleware.sessions import SessionMiddleware

from app.api.analytics import router as analytics_router
from app.api.ask import router as ask_router
from app.api.auth import router as auth_router
from app.api.employees import router as employees_router
from app.api.health import router as health_router
from app.core.config import Settings, get_settings
from app.db.session import make_engine, make_session_factory
from app.models import Department, Employee, FxRate, SalaryRecord  # noqa: F401


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    production = settings.environment == "production"
    cookie_same_site: Literal["lax", "strict", "none"] = "none" if production else "lax"
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie_name,
        same_site=cookie_same_site,
        https_only=production or settings.session_https_only,
    )
    db_engine = engine or make_engine(settings.database_url)
    app.state.engine = db_engine
    app.state.session_factory = make_session_factory(db_engine)
    app.state.settings = settings
    app.dependency_overrides[get_settings] = lambda: settings
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(employees_router)
    app.include_router(analytics_router)
    app.include_router(ask_router)

    @app.exception_handler(OperationalError)
    async def database_unavailable(_request: Request, _exc: OperationalError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    return app


app = create_app()
