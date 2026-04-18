import asyncio
import datetime
import logging
import os
import sqlite3
import sys

from core import models
from core.database import async_session_maker, engine
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

OLD_DB_PATH = "old_bot_database.db"


def get_old_db_connection():
    """Подключение к старой базе с возвратом строк в виде словарей."""
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_dt(dt_string):
    """Безопасный парсинг дат из SQLite (с учетом таймзон)."""
    if not dt_string:
        return None
    try:
        dt = datetime.datetime.fromisoformat(dt_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        try:
            dt = datetime.datetime.strptime(
                dt_string, "%Y-%m-%d %H:%M:%S"
            )
            return dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            try:
                dt = datetime.datetime.strptime(
                    dt_string, "%Y-%m-%d"
                ).date()
                return dt
            except ValueError:
                return None


def parse_timedelta(td_value):
    """Парсинг интервалов времени (total_time)."""
    if td_value is None:
        return datetime.timedelta()
    if isinstance(td_value, (int, float)):
        return datetime.timedelta(microseconds=float(td_value))
    elif isinstance(td_value, str):
        return datetime.timedelta()
    return datetime.timedelta()


def get_val(row, key, default=None):
    """Безопасное извлечение значения из sqlite3.Row."""
    return row[key] if key in row.keys() else default


async def migrate_table(
    session, conn, table_name, model_class, row_mapper_func
):
    """Универсальная функция для миграции таблицы."""
    logger.info(f"⏳ Перенос таблицы: {table_name}...")
    try:
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        count = 0
        for row in rows:
            stmt = select(model_class).where(
                model_class.id == row["id"]
            )
            existing = await session.scalar(stmt)

            if not existing:
                new_obj = row_mapper_func(row)
                session.add(new_obj)
                count += 1

        await session.commit()
        logger.info(f"✅ {table_name}: перенесено {count} записей.")
    except sqlite3.OperationalError:
        logger.warning(f"⚠️ {table_name} пропущена (не найдена).")
    except Exception as e:
        logger.error(f"❌ Ошибка при переносе {table_name}: {e}")


async def main():
    if not os.path.exists(OLD_DB_PATH):
        logger.error(f"❌ ОШИБКА: Файл '{OLD_DB_PATH}' не найден!")
        logger.info("👉 Поместите старую БД в корень и повторите.")
        sys.exit(1)
    logger.info("🛠 Инициализация таблиц в новой базе данных...")
    async with engine.begin() as db_conn:
        await db_conn.run_sync(models.Base.metadata.create_all)
    logger.info("🚀 Запуск миграции данных...")

    with get_old_db_connection() as conn:
        async with async_session_maker() as session:

            # 1.1 Компании (Django: bot_company)
            await migrate_table(
                session,
                conn,
                "bot_company",
                models.Company,
                lambda r: models.Company(
                    id=r["id"],
                    name=r["name"]
                ),
            )

            # 1.2 Титулы уровней (Django: bot_leveltitle)
            await migrate_table(
                session,
                conn,
                "bot_leveltitle",
                models.LevelTitle,
                lambda r: models.LevelTitle(
                    id=r["id"],
                    level=r["level"],
                    title=r["title"],
                    description=r["description"],
                    category=r["category"],
                    min_experience=r["min_experience"],
                ),
            )

            # 1.3 Сезоны (Django: bot_season)
            await migrate_table(
                session,
                conn,
                "bot_season",
                models.Season,
                lambda r: models.Season(
                    id=r["id"],
                    name=r["name"],
                    theme=r["theme"],
                    start_date=parse_dt(r["start_date"]),
                    end_date=parse_dt(r["end_date"]),
                    is_active=bool(r["is_active"]),
                ),
            )

            # 1.4 Курсы валют (Django: bot_currencyrate)
            await migrate_table(
                session,
                conn,
                "bot_currencyrate",
                models.CurrencyRate,
                lambda r: models.CurrencyRate(
                    id=r["id"],
                    currency=r["currency"],
                    rate=float(r["rate"]),
                    date=parse_dt(r["date"]),
                ),
            )

            # 2.1 Выезды (Django: bot_useractivity)
            await migrate_table(
                session,
                conn,
                "bot_useractivity",
                models.UserActivity,
                lambda r: models.UserActivity(
                    id=r["id"],
                    user_id=r["user_id"],
                    username=r["username"],
                    company_id=r["company_id"],
                    join_time=parse_dt(r["join_time"]),
                    leave_time=parse_dt(r["leave_time"]),
                    edited=bool(get_val(r, "edited", False)),
                    edit_count=get_val(r, "edit_count", 0),
                    experience_gained=get_val(
                        r, "experience_gained", 0
                    ),
                ),
            )

            # 2.2 Ранги сезонов (Django: bot_seasonrank)
            await migrate_table(
                session,
                conn,
                "bot_seasonrank",
                models.SeasonRank,
                lambda r: models.SeasonRank(
                    id=r["id"],
                    user_id=r["user_id"],
                    username=r["username"],
                    season_id=r["season_id"],
                    experience=r["experience"],
                    level=r["level"],
                    total_time=parse_timedelta(r["total_time"]),
                    visits_count=r["visits_count"],
                    level_title_id=r["level_title_id"],
                    achieved_at=parse_dt(r["achieved_at"]),
                ),
            )

            # 2.3 Ачивки (Django: bot_achievement)
            await migrate_table(
                session,
                conn,
                "bot_achievement",
                models.Achievement,
                lambda r: models.Achievement(
                    id=r["id"],
                    user_id=r["user_id"],
                    username=r["username"],
                    achievement_name=r["achievement_name"],
                    achieved_at=parse_dt(r["achieved_at"]),
                ),
            )

            # 2.4 Ежедневная статистика (Django: bot_dailystatistics)
            await migrate_table(
                session,
                conn,
                "bot_dailystatistics",
                models.DailyStatistics,
                lambda r: models.DailyStatistics(
                    id=r["id"],
                    user_id=r["user_id"],
                    username=r["username"],
                    date=parse_dt(r["date"]),
                    total_time=parse_timedelta(r["total_time"]),
                    total_trips=r["total_trips"],
                ),
            )

    logger.info("🎉 Миграция успешно завершена!")


if __name__ == "__main__":
    asyncio.run(main())
