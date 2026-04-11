import re

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.tasks import send_news_digest_task

router = Router()


@router.message(Command("start_news"))
async def cmd_start_news(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler
):
    """Регистрирует ежедневную рассылку новостей и котиков."""
    if not command.args:
        return await message.answer(
            "❌ Укажите время в формате ЧЧ:ММ\nПример: <code>/start_news 09:30</code>",  # noqa
            parse_mode="HTML"
        )
    time_match = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", command.args.strip())
    if not time_match:
        return await message.answer("❌ Неверный формат времени. Нужно ЧЧ:ММ (от 00:00 до 23:59).") # noqa

    hour, minute = time_match.groups()
    chat_id = message.chat.id
    job_id = f"news_digest_{chat_id}"
    scheduler.add_job(
        send_news_digest_task,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        args=[message.bot, chat_id],
        replace_existing=True
    )

    await message.answer(
        "✅ <b>Рассылка новостей активирована!</b>\n",
        parse_mode="HTML"
    )


@router.message(Command("stop_news"))
async def cmd_stop_news(message: Message, scheduler: AsyncIOScheduler):
    """Удаляет задачу рассылки."""
    job_id = f"news_digest_{message.chat.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        await message.answer("📴 Рассылка новостей отключена.")
    else:
        await message.answer("❓ У вас не была настроена рассылка новостей.")
