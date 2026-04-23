import calendar
import logging
import random
from datetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import URLInputFile
from core.bot_constants import BotRemidersCfg
from core.crud import (get_all_active_activities, get_full_daily_stats,
                       get_next_level_exp, get_user_rank_info,
                       save_daily_statistics)
from core.models import SeasonRank
from handlers.tools import CAT_CAPTION, _fetch_cat_image
from services.crypto import get_crypto_rates
from services.currency import get_currency_rates
from services.gamification import generate_progress_bar
from services.it_news import fetch_it_news
from services.weather import get_weather
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 86_400
SECONDS_IN_HOUR = 3_600
SECONDS_IN_MINUTE = 60
MAX_ACHIEVEMENTS_DISPLAY = 3


def get_plural_days(n: int) -> str:
    """Правильно склоняет слово 'день' в зависимости от числа."""
    if n % 10 == 1 and n % 100 != 11:
        return "день"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "дня"
    else:
        return "дней"


async def send_transport_reminder(bot: Bot, chat_id: int):
    try:
        today = date.today()
        _, days_in_month = calendar.monthrange(today.year, today.month)
        days_left = days_in_month - today.day
        target_days = [7, 3, 2, 1]
        if days_left != 0 and days_left not in target_days:
            return

        if days_left == 0:
            text = "⏳ Сегодня последний день месяца! Не забудь проездной!"
        else:
            templates = BotRemidersCfg.TRANSPORT_REMINDER_TEMPLATES
            template = random.choice(templates)
            day_word = get_plural_days(days_left)
            is_single = days_left % 10 == 1 and days_left % 100 != 11
            verb = "Остался" if is_single else "Осталось"

            text = template.format(
                verb=verb,
                days=days_left,
                day_word=day_word
            )

        await bot.send_message(chat_id, text, parse_mode="HTML")
        logger.info(f"Напоминание отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания: {e}")


async def send_weather_briefing(bot: Bot, chat_id: int):
    """Отправляет развернутую погодную сводку."""
    try:
        weather_text = await get_weather()
        await bot.send_message(chat_id, weather_text, parse_mode="HTML")
        logger.info(f"Погода отправлена в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке погоды: {e}")


async def send_currency_briefing(bot: Bot, chat_id: int):
    """Отправляет сводку курсов валют."""
    try:
        text = await get_currency_rates()
        await bot.send_message(chat_id, text, parse_mode="HTML")
        logger.info(f"Курсы валют отправлены в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке валют: {e}")


async def send_crypto_briefing(bot: Bot, chat_id: int):
    """Отправляет сводку курсов криптовалют."""
    try:
        text = await get_crypto_rates()
        await bot.send_message(chat_id, text, parse_mode="HTML")
        logger.info(f"Крипта отправлена в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке крипты: {e}")


async def send_news_digest_task(bot: Bot, chat_id: int):
    """Задача: отправить кота, а затем 3 новости."""
    try:
        cat_url = await _fetch_cat_image()
        await bot.send_photo(
            chat_id=chat_id,
            photo=URLInputFile(cat_url),
            caption=f"{CAT_CAPTION}\n\n<b>А теперь к новостям IT:</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке кота в рассылке: {e}")
        await bot.send_message(chat_id, "🐱 Котики застряли в пробке, но новости на месте!")  # noqa
    news_list = await fetch_it_news(count=3)
    if not news_list:
        return await bot.send_message(chat_id, "🗞 Сегодня новостей не нашлось.")  # noqa

    msg_lines = ["🚀 <b>Топ-3 IT новости:</b>\n"]
    for i, news in enumerate(news_list, 1):
        msg_lines.append(f"{i}. <a href='{news['link']}'>{news['title']}</a>")

    await bot.send_message(
        chat_id=chat_id,
        text="\n".join(msg_lines),
        parse_mode="HTML",
        disable_web_page_preview=False
    )


def format_duration_clean(seconds: float) -> str:
    """
    Форматирует длительность в секундах в человекочитаемый вид.

    Args:
        seconds: Длительность в секундах.

    Returns:
        Строка в формате "Х ч У мин" или "У мин".
    """
    if seconds <= 0:
        return "0 мин"

    minutes = int(seconds // SECONDS_IN_MINUTE)
    if minutes >= SECONDS_IN_MINUTE:
        hours = minutes // SECONDS_IN_MINUTE
        remaining_minutes = minutes % SECONDS_IN_MINUTE
        return f"{hours} ч {remaining_minutes} мин"

    return f"{minutes} мин"


async def send_daily_statistics_task(
    bot: Bot,
    chat_id: int,
    session_maker: async_sessionmaker,
) -> None:
    """Отправляет ежедневную статистику в указанный чат и сохраняет её в БД."""
    async with session_maker() as session:
        data = await get_full_daily_stats(session)
        if not data:
            return
        await save_daily_statistics(session, data["user_stats"], data["today"])
        header = "📊 <b>Общая статистика за сегодня:</b>\n"
        season_info = _format_season_info(data["today"], data["season"])
        summary_block = _format_summary_block(
            season_info, data["total_exp_today"])
        user_blocks, total_trips, total_seconds = await _format_user_blocks(
            session, data["user_stats"], data["achievements"]
        )
        metrics = _format_global_metrics(total_trips, total_seconds)
        final_msg = (
            f"{header}\n"
            f"{summary_block}\n"
            f"{metrics}\n\n"
            f"🏅 <b>Участники:</b>\n\n" +
            "\n\n".join(user_blocks) +
            "\n\n<i>КотБот одобряет вашу продуктивность! 🐾</i>"
        )
        await bot.send_message(chat_id, final_msg, parse_mode="HTML")


def _format_season_info(today: date, season) -> str:
    """Форматирует информацию о сезоне."""
    if not season or not season.end_date:
        return "ℹ️ Сезон не активен или дата завершения не задана"

    days_left = (season.end_date.date() - today).days
    return (
        f"🏆 <b>Сезон: {season.name}</b>\n"
        f"⏳ До конца: <b>{days_left} дн.</b>"
    )


def _format_summary_block(season_info: str, total_exp: int) -> str:
    """Форматирует блок с общей сводкой."""
    return (
        f"{season_info}\n"
        f"⭐ <b>Общий опыт за день:</b> {total_exp}\n"
    )


async def _format_user_blocks(
    session,
    user_stats: list,
    achievements: list,
) -> tuple[list[str], int, int]:
    """
    Форматирует блоки статистики по пользователям.

    Returns:
        Кортеж: (список блоков, всего выездов, всего секунд).
    """
    user_blocks = []
    total_trips = 0
    total_seconds_global = 0

    for row in user_stats:
        total_sec = row.total_days * SECONDS_IN_DAY
        total_trips += row.trips
        total_seconds_global += total_sec

        avg_sec = total_sec / row.trips if row.trips > 0 else 0
        block = await _build_user_block(session, row, avg_sec, achievements)
        user_blocks.append(block)

    return user_blocks, total_trips, total_seconds_global


async def _build_user_block(
    session,
    row,
    avg_seconds: float,
    achievements: list,
) -> str:
    """Собирает блок статистики для одного пользователя."""
    rank = await get_user_rank_info(session, row.user_id)
    rank_text = await _format_rank_progress(session, rank) if rank else ""

    user_achievements = _filter_user_achievements(achievements, row.user_id)
    ach_str = ", ".join(user_achievements) if user_achievements else "Пока нет"

    username = row.username or f"user_{row.user_id}"
    return (
        f"👤 <b>@{username}</b>\n"
        f"{rank_text}"
        f"▸ Выездов сегодня: <b>{row.trips}</b> 🚗\n"
        f"▸ Среднее время: <b>{format_duration_clean(avg_seconds)}</b> ⏱\n"
        f"▸ Достижения: {ach_str}"
    )


async def _format_rank_progress(
    session,
    rank: SeasonRank,
) -> str:
    """Форматирует информацию об уровне и прогрессе пользователя."""
    if not rank or not rank.level_title:
        return ""

    next_exp = await get_next_level_exp(session, rank.level)
    min_exp = rank.level_title.min_experience
    current_exp = rank.experience - min_exp
    needed_exp = next_exp - min_exp

    if needed_exp <= 0:
        progress_percent = 100
        progress_bar = generate_progress_bar(1, 1)
    else:
        progress_percent = int((current_exp / needed_exp) * 100)
        progress_bar = generate_progress_bar(current_exp, needed_exp)

    title = rank.level_title.title
    return (
        f"▸ Уровень: <b>{rank.level}</b> | <b>{title}</b>\n"
        f"▸ Прогресс: <b>{progress_percent}%</b>\n"
        f"<code>[{progress_bar}]</code>\n"
    )


def _filter_user_achievements(
    achievements: list,
    user_id: int,
) -> list[str]:
    """Фильтрует и ограничивает достижения пользователя."""
    user_achs = [
        f"🏆 {ach.achievement_name}"
        for ach in achievements
        if ach.user_id == user_id
    ]
    return user_achs[:MAX_ACHIEVEMENTS_DISPLAY]


def _format_global_metrics(total_trips: int, total_seconds: int) -> str:
    """Форматирует общие показатели."""
    global_avg = total_seconds / total_trips if total_trips > 0 else 0

    return (
        f"📈 <b>Показатели:</b>\n"
        f" • Всего выездов: <b>{total_trips}</b>\n"
        f" • Общее время: <b>{format_duration_clean(total_seconds)}</b>\n"
        f" • Среднее время: <b>{format_duration_clean(global_avg)}</b>"
    )


async def send_leave_reminder_task(
    bot: Bot,
    chat_id: int,
    session_maker: async_sessionmaker,
):
    """Задача для напоминания пользователям о необходимости /leave."""
    try:
        async with session_maker() as session:
            active_activities = await get_all_active_activities(session)

        if not active_activities:
            return
        users = []
        for activity in active_activities:
            username = (
                f"@{activity.username}"
                if activity.username
                else f"ID: {activity.user_id}"
            )
            company_name = (
                activity.company.name if activity.company else "Неизвестно"
            )
            users.append(f"• {username} (<b>{company_name}</b>)")
        users_list_str = "\n".join(users)
        message = (
            "⚠️ <b>Внимание!</b> ⚠️\n\n"
            "Следующие сотрудники всё ещё находятся в организациях:\n"
            f"{users_list_str}\n\n"
            "🛠️ <b>Что нужно сделать?</b>\n"
            "1. Если вы уже покинули организацию — "
            "<b>проигнорируйте это сообщение</b>.\n"
            "2. Если ещё не ушли — выберите действие:\n\n"
            "📍 <b>Доступные команды:</b>\n"
            "• <code>/edit_start ЧЧ:ММ</code> — "
            "скорректировать время прибытия "
            "(пример: <code>/edit_start 09:30</code>)\n"
            "• <code>/edit_end ЧЧ:ММ</code> — изменить время убытия и "
            "завершить сессию (пример: <code>/edit_end 18:15</code>)\n"
            "<i>Команда работает как leave</i>\n\n"
            "❗ <b>Важно:</b>\n"
            "— Работает только для <b>активных</b> сессий "
            "(где вы сейчас числитесь программно)\n"
            "— Формат времени: 09:00, 14:30 (24-часовой)"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML"
        )
        logger.info(f"Напоминание о незакрытых выездах отправлено в {chat_id}")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка отправки (Bad Request): {e.message}")
        if "chat not found" in str(e).lower():
            logger.critical("Бот не добавлен в группу или chat_id неверный!")
    except TelegramForbiddenError as e:
        logger.error(f"Нет прав на отправку (Forbidden): {e.message}")
        if "bot was blocked" in str(e).lower():
            logger.critical("Бот заблокирован в группе!")
    except Exception as e:
        logger.error(
            f"Критическая ошибка в send_leave_reminder_task: {e}",
            exc_info=True
        )
