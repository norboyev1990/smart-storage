import hmac

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import get_settings

router = APIRouter(prefix="/telegram", tags=["telegram"], include_in_schema=False)


@router.post("/webhook")
async def webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(default="")):
    secret = get_settings().webhook_secret
    if not secret or not hmac.compare_digest(x_telegram_bot_api_secret_token, secret):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bad secret token")
    # aiogram takes seconds to import; load it only when the bot gets an update, not on every app start
    from app.bot import process_update

    await process_update(await request.json())
    return {"ok": True}
