"""Telegram bot: opens the Mini App. Run with `python -m app.bot`."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

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


async def main() -> None:
    settings = get_settings()
    await dp.start_polling(Bot(settings.bot_token))


if __name__ == "__main__":
    asyncio.run(main())
