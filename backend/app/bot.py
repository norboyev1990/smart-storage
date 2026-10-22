"""Telegram bot: opens the Mini App.

Locally run `python -m app.bot` (polling). On hosting without long-running
processes the API receives updates at /telegram/webhook; register it with
`python manage.py set-webhook`.
"""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update, WebAppInfo

from app.config import get_settings

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть Smart Storage", web_app=WebAppInfo(url=get_settings().webapp_url))]
        ]
    )
    await message.answer("Учёт смартфонов: склад, покупки, продажи и отчёты.", reply_markup=keyboard)


async def process_update(data: dict) -> None:
    # A new Bot per update: under WSGI the event loop is not guaranteed to outlive a request
    async with Bot(get_settings().bot_token) as bot:
        await dp.feed_update(bot, Update.model_validate(data, context={"bot": bot}))


async def set_webhook() -> str:
    settings = get_settings()
    url = settings.api_url.rstrip("/") + "/telegram/webhook"
    async with Bot(settings.bot_token) as bot:
        await bot.set_webhook(url, secret_token=settings.webhook_secret or None, drop_pending_updates=True)
    return url


async def main() -> None:
    settings = get_settings()
    async with Bot(settings.bot_token) as bot:
        await bot.delete_webhook()
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
