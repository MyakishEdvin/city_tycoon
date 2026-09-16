"""
CITY TYCOON bot entrypoint.

Run with:  python -m bot.main
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import common, profile, start
from bot.middlewares.database import DatabaseSessionMiddleware

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("city_tycoon.bot")


async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(DatabaseSessionMiddleware())

    # Order matters only where filters could overlap; these don't.
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(common.router)

    logger.info(
        "Starting CITY TYCOON bot | environment=%s | webapp_configured=%s",
        settings.ENVIRONMENT,
        settings.webapp_configured,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down CITY TYCOON bot")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
