import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.schemas.auth import LoginRequest, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MeResponse)
def login(
    body: LoginRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> MeResponse:
    email_ok = secrets.compare_digest(body.email.lower(), settings.hr_email.lower())
    password_ok = secrets.compare_digest(body.password, settings.hr_password)
    if not (email_ok and password_ok):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    request.session["user"] = settings.hr_email
    return MeResponse(email=settings.hr_email)


@router.post("/logout")
def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"status": "ok"}


@router.get("/me", response_model=MeResponse)
def me(request: Request, settings: Settings = Depends(get_settings)) -> MeResponse:
    email = request.session.get("user")
    if not email or email != settings.hr_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return MeResponse(email=settings.hr_email)
