import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from core.database import async_session_maker, engine
from core.models import Base
from dotenv import load_dotenv
from handlers import base
from middlewares.db import DbSessionMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


async def init_db():
    """Создает таблицы в базе данных (если их еще нет)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info("База данных инициализирована.")


async def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Токен бота не найден в .env!")
    bot = Bot(token=bot_token, default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_maker))
    dp.include_router(base.router)
    await init_db()

    logging.info("Бот запущен и готов к работе! "
                 "(Нажмите Ctrl+C для остановки)")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
