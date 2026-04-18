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
from services.tasks import (send_currency_briefing, send_daily_statistics_task,
                            send_news_digest_task, send_transport_reminder,
                            send_weather_briefing)

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")
CHAT_ID_INT = int(CHAT_ID) if CHAT_ID else 0

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
    # --- 00:01 (Сезоны) ---
    scheduler.add_job(
        check_and_update_seasons_task,
        trigger="cron", hour=0, minute=1,
        id="check_seasons_daily",
        args=[async_session_maker, bot, CHAT_ID_INT],
        replace_existing=True
    )
    # --- 07:30 (Погода) ---
    scheduler.add_job(
        send_weather_briefing,
        trigger="cron", hour=7, minute=30,
        id=f"weather_{CHAT_ID}",
        kwargs={"bot": bot, "chat_id": CHAT_ID_INT},
        replace_existing=True
    )
    # --- 18:15 (Статистика) ---
    scheduler.add_job(
        send_daily_statistics_task,
        trigger="cron", hour=18, minute=15,
        id=f"daily_stats_{CHAT_ID}",
        args=[bot, CHAT_ID_INT, async_session_maker],
        replace_existing=True
    )
    # --- 21:00 (Напоминания) ---
    scheduler.add_job(
        send_transport_reminder,
        trigger="cron", hour=21, minute=0,
        id=f"reminder_{CHAT_ID}",
        kwargs={"bot": bot, "chat_id": CHAT_ID_INT},
        replace_existing=True
    )
    # --- 08:50 (Валюта) ---
    scheduler.add_job(
        send_currency_briefing,
        trigger="cron", hour=8, minute=50,
        id=f"currency_{CHAT_ID}",
        kwargs={"bot": bot, "chat_id": CHAT_ID_INT},
        replace_existing=True
    )
    # --- 07:25 (Новости) ---
    scheduler.add_job(
        send_news_digest_task,
        trigger="cron", hour=7, minute=25,
        id=f"news_digest_{CHAT_ID}",
        args=[bot, CHAT_ID_INT],
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
