import argparse
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import async_session_maker, engine
from core.logger import setup_logging
from core.models import Base
from dotenv import load_dotenv
from handlers import base, info, news, profile, scheduling, tools, visits
from middlewares.db import DbSessionMiddleware
from services.seasons import (check_and_update_seasons_task,
                              create_season_if_needed)

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")

setup_logging()


async def init_db():
    """Создает таблицы в базе данных (если их еще нет)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info("База данных инициализирована.")


async def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Токен бота не найден в .env!")
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_maker))
    dp.include_router(profile.router)
    dp.include_router(visits.router)
    dp.include_router(news.router)
    dp.include_router(scheduling.router)
    dp.include_router(tools.router)
    dp.include_router(base.router)
    dp.include_router(info.router)
    await init_db()
    async with async_session_maker() as session:
        await create_season_if_needed(session)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        check_and_update_seasons_task,
        trigger="cron",
        hour=0,
        minute=1,
        id="check_seasons_daily",
        args=[async_session_maker, bot, CHAT_ID],
        replace_existing=True
    )
    scheduler.start()
    logging.info("🤖 Бот запущен и готов к работе! (Ctrl+C для остановки)")
    try:
        await dp.start_polling(bot, scheduler=scheduler)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cat_Time_Bot_Z Management Console")
    parser.add_argument(
        "--init_levels",
        action="store_true",
        help="Заполнить базу данных начальными уровнями и выйти"
    )
    args = parser.parse_args()
    if args.init_levels:
        print("🛠 Запуск скрипта инициализации уровней...")
        from scripts.init_level import init_levels
        try:
            asyncio.run(init_levels())
        except Exception as e:
            print(f"❌ Ошибка при инициализации: {e}")
        sys.exit(0)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
    except Exception:
        import traceback
        print("\n" + "="*50)
        print("❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ:")
        traceback.print_exc()
        print("="*50 + "\n")
        input("Нажмите Enter, чтобы закрыть окно...")
