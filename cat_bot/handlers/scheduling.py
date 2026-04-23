import re

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.state import any_state
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import async_session_maker
from services.tasks import (send_crypto_briefing, send_currency_briefing,
                            send_daily_statistics_task,
                            send_leave_reminder_task, send_transport_reminder,
                            send_weather_briefing)

router = Router()


async def _enable_job(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    job_prefix: str,
    job_func,
    success_text: str,
    job_kwargs: dict | None = None,
    job_args: list | None = None,
):
    """Универсальная функция для включения любой рассылки по времени."""
    if not command.args:
        return await message.answer(
            f"❌ Укажите время: <code>/start_{job_prefix} ЧЧ:ММ</code>",
            parse_mode="HTML",
        )

    time_str = command.args.strip()
    pattern = r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$"
    match = re.match(pattern, time_str)

    if not match:
        return await message.answer(
            "❌ Неверный формат времени.\n\n"
            "Пожалуйста, укажите время в формате <b>ЧЧ:ММ</b>.\n"
            "👉 <b>Пример:</b> <code>08:30</code> или <code>18:45</code>",
            parse_mode="HTML",
        )

    hour, minute = int(match.group(1)), int(match.group(2))
    job_id = f"{job_prefix}_{message.chat.id}"

    scheduler.add_job(
        job_func,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        args=job_args or [],
        kwargs=job_kwargs or {},
        replace_existing=True,
    )

    await message.answer(
        f"✅ {success_text} <b>{time_str}</b>!",
        parse_mode="HTML",
    )


async def _disable_job(
    message: Message,
    scheduler: AsyncIOScheduler,
    job_prefix: str,
    desc: str,
):
    """Универсальная функция для отключения рассылки."""
    job_id = f"{job_prefix}_{message.chat.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        await message.answer(f"🛑 {desc} отключена.")
    else:
        await message.answer(f"❓ {desc} не была настроена.")


@router.message(Command("start_reminder"))
async def cmd_start_reminder(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="reminder",
        job_func=send_transport_reminder,
        success_text="Ежедневные напоминания включены на",
        job_kwargs={"bot": bot, "chat_id": message.chat.id},
    )


@router.message(Command("stop_reminder"))
async def cmd_stop_reminder(message: Message, scheduler: AsyncIOScheduler):
    await _disable_job(
        message, scheduler, "reminder", "Напоминание о проездном"
    )


@router.message(Command("start_weather"), StateFilter(any_state))
async def cmd_start_weather(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="weather",
        job_func=send_weather_briefing,
        success_text="Ежедневная сводка погоды включена на",
        job_kwargs={"bot": bot, "chat_id": message.chat.id},
    )


@router.message(Command("stop_weather"))
async def cmd_stop_weather(message: Message, scheduler: AsyncIOScheduler):
    await _disable_job(message, scheduler, "weather", "Сводка погоды")


@router.message(Command("start_currency"), StateFilter(any_state))
async def cmd_start_currency(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="currency",
        job_func=send_currency_briefing,
        success_text="Рассылка валют установлена на",
        job_kwargs={"bot": bot, "chat_id": message.chat.id},
    )


@router.message(Command("stop_currency"))
async def cmd_stop_currency(message: Message, scheduler: AsyncIOScheduler):
    await _disable_job(message, scheduler, "currency", "Рассылка валют")


@router.message(Command("start_crypto"), StateFilter(any_state))
async def cmd_start_crypto(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="crypto",
        job_func=send_crypto_briefing,
        success_text="Рассылка криптовалют установлена на",
        job_kwargs={"bot": bot, "chat_id": message.chat.id},
    )


@router.message(Command("stop_crypto"))
async def cmd_stop_crypto(message: Message, scheduler: AsyncIOScheduler):
    await _disable_job(message, scheduler, "crypto", "Рассылка криптовалют")


@router.message(Command("start_stats"))
async def cmd_start_stats(
    message: Message, command: CommandObject, scheduler: AsyncIOScheduler
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="daily_stats",
        job_func=send_daily_statistics_task,
        success_text="Сводка по выездам активирована на",
        job_args=[message.bot, message.chat.id, async_session_maker],
    )


@router.message(Command("stop_stats"))
async def cmd_stop_stats(message: Message, scheduler: AsyncIOScheduler):
    await _disable_job(
        message, scheduler, "daily_stats", "Рассылка статистики"
    )


@router.message(Command("start_leave_reminder"))
async def cmd_start_leave_reminder(
    message: Message,
    command: CommandObject,
    scheduler: AsyncIOScheduler,
    bot: Bot,
):
    await _enable_job(
        message,
        command,
        scheduler,
        job_prefix="leave_reminder",
        job_func=send_leave_reminder_task,
        success_text="Напоминание о незакрытых выездах включено на",
        job_args=[bot, message.chat.id, async_session_maker],
    )


@router.message(Command("stop_leave_reminder"))
async def cmd_stop_leave_reminder(message: Message,
                                  scheduler: AsyncIOScheduler):
    await _disable_job(
        message, scheduler,
        "leave_reminder", "Напоминание о незакрытых выездах"
    )


@router.message(Command("stop_scheduler"))
async def cmd_stop_scheduler(message: Message, scheduler: AsyncIOScheduler):
    chat_id = message.chat.id
    suffix = f"_{chat_id}"
    removed_count = 0
    for job in scheduler.get_jobs():
        if job.id.endswith(suffix):
            scheduler.remove_job(job.id)
            removed_count += 1

    if removed_count > 0:
        msg = (
            f"🛑 Все автоматические рассылки ({removed_count} шт.) "
            f"в этом чате отключены."
        )
        await message.answer(msg)
    else:
        await message.answer("ℹ️ Активных рассылок в этом чате не найдено.")
