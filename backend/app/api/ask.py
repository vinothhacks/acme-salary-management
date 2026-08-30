from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core.config import Settings, get_settings
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask import answer

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/chat", response_model=AskResponse)
def chat(
    body: AskRequest,
    _: str = Depends(require_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AskResponse:
    say, actions, model = answer(session, body.message, body.history, settings)
    return AskResponse(say=say, actions=actions, model=model)
