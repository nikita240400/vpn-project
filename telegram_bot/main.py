import asyncio
import logging

from aiogram import Bot, Dispatcher

from telegram_bot.config import BOT_TOKEN
from telegram_bot.handlers.devices import router as devices_router
from telegram_bot.handlers.start import router as start_router
from telegram_bot.handlers.account import router as account_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(devices_router)
    dp.include_router(account_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())