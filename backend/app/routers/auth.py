from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User
from app.schemas import TelegramAuthIn, TokenOut, UserOut
from app.security import create_token, current_user
from app.telegram_auth import InitDataError, validate_init_data

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TokenOut)
def telegram_login(body: TelegramAuthIn, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        tg_user = validate_init_data(body.init_data, settings.bot_token, settings.init_data_max_age_seconds)
    except InitDataError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = db.scalar(select(User).where(User.telegram_id == tg_user["id"]))
    if user is None:
        user = User(telegram_id=tg_user["id"])
        db.add(user)
    user.first_name = tg_user.get("first_name", "")
    user.last_name = tg_user.get("last_name")
    user.username = tg_user.get("username")
    db.commit()
    return TokenOut(access_token=create_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
