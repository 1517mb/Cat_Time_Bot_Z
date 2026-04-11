import re

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.tasks import send_transport_reminder

router = Router()


@router.message(Command("start_reminder"))
async def cmd_start_reminder(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/start_reminder ЧЧ:ММ`",
            parse_mode="Markdown",
        )

    time_str = command.args.strip()
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str)
    if not match:
        return await message.answer("❌ Неверный формат (нужно ЧЧ:ММ).")

    hour = int(match.group(1))
    minute = int(match.group(2))
    chat_id = message.chat.id
    job_id = f"reminder_{chat_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        send_transport_reminder,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        kwargs={"bot": bot, "chat_id": chat_id},
    )

    await message.answer(
        f"✅ Ежедневные напоминания включены на *{time_str}*!",
        parse_mode="Markdown",
    )


@router.message(Command("stop_scheduler"))
async def cmd_stop_scheduler(
    message: Message, scheduler: AsyncIOScheduler
):
    chat_id = message.chat.id
    job_id = f"reminder_{chat_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        await message.answer("🛑 Напоминания в этом чате отключены.")
    else:
        await message.answer("ℹ️ Активных напоминаний не найдено.")
