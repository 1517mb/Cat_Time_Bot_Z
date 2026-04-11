import datetime
import logging
import random

from aiogram import Bot
from core import models
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SEASON_IT_NAMES = {
    'winter': [
        "❄️ Морозный аптайм", "⛄ Зимнее шифрование",
        "🧊 Ледяной RAID-массив", "🛡️ Фаервол-мороз",
        "❄️ Снежный дата-центр", "🧣 Шарфо-сетевая инфраструктура",
        "🔥 Горячий кофе на холодном сервере", "🌨️ Снежный DNS-шторм",
        "💻 Зимняя дефрагментация", "❄️ Морозный бэкап"
    ],
    'spring': [
        "🌱 Весенний рефакторинг", "🌸 Цветущий деплой", "🌧️ Дождевой бэкап",
        "🐞 Сезон багфиксов", "🔄 Весенний ребут", "💾 Роса на SSD",
        "🌿 Зеленый код в производство", "🌼 Цветущий API-интерфейс",
        "🚿 Весенняя чистка кода", "🪴 Рост нагрузки на сервера"
    ],
    'summer': [
        "☀️ Летний оверклокинг", "🏖️ Песочное тестирование", "🌊 Волновой DDOS",
        "🔥 Жаркий процессор", "🍉 Арбузный компресс", "⛱️ Пляжный режим ядра",
        "🌴 Пальмовое дерево зависимостей", "🏄‍♂️ Серфинг по логам",
        "🌞 Солнечный аптайм", "🍦 Мороженое для серверов"
    ],
    'autumn': [
        "🍁 Листопадный Git Merge",
        "🍂 Осенний сбор мусора",
        "🌧️ Дождливый бэкап",
        "🦃 Индейский аптайм", "☕ Кофейный дебаггинг",
        "📉 Падающие листья и показатели",
        "🍄 Грибной рост нагрузки", "🌰 Жесткий диск с орехами",
        "🍎 Яблочный патч-вторник", "🕸️ Паутина зависимостей"
    ]
}


def determine_season_theme() -> str:
    """Определяет тему сезона по текущему месяцу"""
    month = datetime.datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


async def generate_season_name(session: AsyncSession, theme: str) -> str:
    """Генерирует уникальное IT-тематическое название для сезона"""
    year = datetime.datetime.now().year
    base_name = random.choice(
        SEASON_IT_NAMES.get(theme, [f"Сезон {theme.capitalize()}"]))
    season_name = f"{base_name} {year}"
    counter = 1

    while await session.scalar(select(models.Season).where(models.Season.name == season_name)):  # noqa: E501
        season_name = f"{base_name} {year} v{counter}"
        counter += 1

    return season_name


async def create_season_if_needed(
        session: AsyncSession) -> tuple[models.Season, bool]:
    """
    ЯДРО ЛОГИКИ: Работает с уже открытой сессией.
    Возвращает кортеж: (объект_сезона, был_ли_создан_новый_сезон_только_что)
    """
    today = datetime.datetime.now().date()
    active_season = await session.scalar(
        select(models.Season).where(models.Season.is_active)
    )
    if active_season:
        if active_season.end_date is not None:
            if isinstance(active_season.end_date, datetime.datetime):
                end_date = active_season.end_date.date()
            else:
                end_date = active_season.end_date
            if today <= end_date:
                return active_season, False
        active_season.is_active = False
        await session.commit()
        logger.info(f"🏁 Сезон '{active_season.name}' завершен.")
    theme = determine_season_theme()
    season_name = await generate_season_name(session, theme)
    new_season = models.Season(
        name=season_name,
        theme=theme,
        start_date=today,
        end_date=today + relativedelta(months=3),
        is_active=True
    )
    session.add(new_season)
    await session.commit()
    logger.info(f"🚀 Создан новый сезон: {season_name} (тема: {theme})")
    return new_season, True


async def check_and_update_seasons_task(
        session_maker, bot: Bot, chat_id: int):
    """
    Создает свою сессию, вызывает логику и шлет уведомление.
    """
    async with session_maker() as session:
        season, is_new = await create_season_if_needed(session)
        if is_new:
            msg = (
                f"🎉 <b>Внимание, смена сезона!</b> 🎉\n\n"
                f"Старый сезон официально завершен. Начинается новый этап:\n"
                f"🏆 <b>{season.name}</b>\n\n"
                f"Пора зарабатывать новый опыт и достижения. "
                "Всем удачного дня! 🚀"
            )
            try:
                await bot.send_message(chat_id=chat_id,
                                       text=msg, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление о сезоне: {e}")
