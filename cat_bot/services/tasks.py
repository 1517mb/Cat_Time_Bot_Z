import logging
import random

from aiogram import Bot
from core.bot_constants import BotRemidersCfg
from services.crypto import get_crypto_rates
from services.currency import get_currency_rates
from services.weather import get_weather

logger = logging.getLogger(__name__)


async def send_transport_reminder(bot: Bot, chat_id: int):
    """Отправляет напоминание о транспортных расходах в чат."""
    try:
        template = random.choice(
            BotRemidersCfg.TRANSPORT_REMINDER_TEMPLATES
        )
        days_left = random.choice(list(BotRemidersCfg.TRANSPORT_REMINDER_DAYS))
        day_word = "дня" if days_left in [2, 4] else "дней"
        text = template.format(
            verb="Осталось",
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
