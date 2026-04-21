import re

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.state import any_state
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import async_session_maker
from services.tasks import (send_crypto_briefing, send_currency_briefing,
                            send_daily_statistics_task,
                            send_transport_reminder, send_weather_briefing)

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
        return await message.answer(
            "❌ Неверный формат времени.\n\n"
            "Пожалуйста, укажите время в формате *ЧЧ:ММ*.\n"
            "👉 *Пример:* `08:30` или `18:45`",
            parse_mode="Markdown"
        )

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


@router.message(Command("start_weather"), StateFilter(any_state))
async def cmd_start_weather(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/start_weather ЧЧ:ММ`",
            parse_mode="Markdown",
        )
    time_str = command.args.strip()
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str)
    if not match:
        return await message.answer(
            "❌ Неверный формат времени для погоды.\n\n"
            "Пожалуйста, используйте формат *ЧЧ:ММ*.\n"
            "👉 *Пример:* `07:15` или `20:00`",
            parse_mode="Markdown"
        )

    hour = int(match.group(1))
    minute = int(match.group(2))
    chat_id = message.chat.id
    job_id = f"weather_{chat_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        send_weather_briefing,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        kwargs={"bot": bot, "chat_id": chat_id},
    )
    await message.answer(
        f"✅ Ежедневная сводка погоды включена на *{time_str}*!",
        parse_mode="Markdown",
    )


@router.message(Command("start_currency"), StateFilter(any_state))
async def cmd_start_currency(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/start_currency ЧЧ:ММ`"
        )

    time_str = command.args.strip()
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str)
    if not match:
        return await message.answer(
            "❌ Неверный формат времени.\n\n"
            "Пожалуйста, укажите время в формате <b>ЧЧ:ММ</b>.\n"
            "👉 <b>Пример:</b> <code>08:50</code> или <code>12:00</code>"
        )

    hour, minute = int(match.group(1)), int(match.group(2))
    chat_id = message.chat.id
    job_id = f"currency_{chat_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        send_currency_briefing,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        kwargs={"bot": bot, "chat_id": chat_id},
    )

    await message.answer(f"✅ Рассылка валют установлена на *{time_str}*!")


@router.message(Command("start_crypto"), StateFilter(any_state))
async def cmd_start_crypto(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/start_crypto ЧЧ:ММ`", parse_mode="Markdown"
        )

    time_str = command.args.strip()
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str)
    if not match:
        return await message.answer(
            "❌ Неверный формат времени.\n\n"
            "Пожалуйста, укажите время в формате *ЧЧ:ММ*.\n"
            "👉 *Пример:* `08:51` или `21:30`",
            parse_mode="Markdown"
        )

    hour, minute = int(match.group(1)), int(match.group(2))
    chat_id = message.chat.id
    job_id = f"crypto_{chat_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        send_crypto_briefing,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        kwargs={"bot": bot, "chat_id": chat_id},
    )

    await message.answer(
        f"✅ Рассылка криптовалют установлена на *{time_str}*!",
        parse_mode="Markdown"
    )


@router.message(Command("start_stats"))
async def cmd_start_stats(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler
):
    if not command.args:
        return await message.answer(
            "❌ Укажите время. Пример: <code>/start_stats 18:00</code>",
            parse_mode="HTML"
        )

    time_pattern = r"^([0-1]?[0-9]|2[0-3]):([0-5]\d)$"
    time_match = re.match(time_pattern, command.args.strip())

    if not time_match:
        return await message.answer(
            "❌ Неверный формат времени для статистики.\n\n"
            "Пожалуйста, укажите время в формате <b>ЧЧ:ММ</b>.\n"
            "👉 <b>Пример:</b> <code>18:15</code> или "
            "<code>20:00</code>",
            parse_mode="HTML"
        )

    hour, minute = time_match.groups()
    chat_id = message.chat.id
    job_id = f"daily_stats_{chat_id}"

    scheduler.add_job(
        send_daily_statistics_task,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        args=[message.bot, chat_id, async_session_maker],
        replace_existing=True
    )

    await message.answer(
        "📊 <b>Сводка активирована!</b>\n"
        f"Отчет по выездам ежедневно в <code>{hour}:{minute}</code>.",
        parse_mode="HTML"
    )


@router.message(Command("stop_stats"))
async def cmd_stop_stats(message: Message, scheduler: AsyncIOScheduler):
    job_id = f"daily_stats_{message.chat.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        await message.answer("📊 Рассылка статистики отключена.")
    else:
        await message.answer("❓ Статистика не была настроена.")


@router.message(Command("stop_scheduler"))
async def cmd_stop_scheduler(
    message: Message, scheduler: AsyncIOScheduler
):
    chat_id = message.chat.id
    suffix = f"_{chat_id}"
    removed_count = 0
    for job in scheduler.get_jobs():
        if job.id.endswith(suffix):
            scheduler.remove_job(job.id)
            removed_count += 1

    if removed_count > 0:
        await message.answer(
            f"🛑 Все автоматические рассылки ({removed_count} шт.) "
            f"в этом чате отключены."
        )
    else:
        await message.answer("ℹ️ Активных рассылок в этом чате не найдено.")
