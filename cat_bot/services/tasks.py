import logging
import random

from aiogram import Bot
from core.bot_constants import BotRemidersCfg

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
