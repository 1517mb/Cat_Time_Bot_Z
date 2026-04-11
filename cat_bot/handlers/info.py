import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crud, models

router = Router()


def create_progress_bar(progress: float, length: int = 10) -> str:
    filled = min(length, max(0, int(progress / 100 * length)))
    return f"[{'■' * filled}{'□' * (length - filled)}]"


@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    season = await crud.get_current_season(session)
    if not season:
        return await message.answer(
            "ℹ️ В данный момент сезон не активен. "
            "Ожидайте начала нового сезона!")
    stmt = select(models.SeasonRank).where(
        models.SeasonRank.user_id == user_id,
        models.SeasonRank.season_id == season.id
    )
    rank = await session.scalar(stmt)
    if not rank:
        return await message.answer(
            "👤 *Ваш профиль*\n\n"
            "Вы ещё не совершали выездов в текущем сезоне.\n"
            "Используйте команду /join чтобы начать!",
            parse_mode="Markdown"
        )
    await session.refresh(rank, ['level_title'])
    total_hours = int(rank.total_time.total_seconds() // 3600)
    total_minutes = int((rank.total_time.total_seconds() % 3600) // 60)
    time_str = f"{total_hours}ч {total_minutes}м"
    days_left = (season.end_date - datetime.datetime.now().date()).days if season.end_date else 0  # noqa: E501
    next_level_exp = rank.level_title.min_experience if rank.level_title else 100  # noqa: E501
    progress = min(100, max(0, (rank.experience / next_level_exp) * 100)) if next_level_exp else 100  # noqa: E501
    progress_bar = create_progress_bar(progress)

    title_name = rank.level_title.title if rank.level_title else "Без звания"
    category = rank.level_title.category if rank.level_title else "legend"

    msg_text = (
        f"🏆 *Текущий сезон: {season.name}*\n"
        f"⏳ До конца сезона: *{days_left} дней*\n\n"
        "👤 *Ваш профиль*\n\n"
        f"🎯 Уровень: *{rank.level}*\n"
        f"🎖 Звание: *{title_name}*\n"
        f"📚 Категория: *{category}*\n"
        f"⭐ Опыт: *{rank.experience}*\n"
        f"📊 Прогресс: {progress_bar} {int(progress)}%\n"
        f"⏱ Всего времени в организациях: *{time_str}*\n"
        f"🚗 Всего выездов: *{rank.visits_count}*"
    )
    await message.answer(msg_text, parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession):
    stmt = select(models.UserActivity).where(
        models.UserActivity.leave_time.is_(None))
    result = await session.scalars(stmt)
    active_activities = result.all()

    if not active_activities:
        return await message.answer(
            "ℹ️ *Статус:* В данный момент никто не находится в организациях.",
            parse_mode="Markdown")

    companies = {}
    for activity in active_activities:
        await session.refresh(activity, ['company'])
        company_name = activity.company.name
        join_time = activity.join_time.strftime("%H:%M")
        username = f"@{activity.username}" if activity.username else f"ID:{activity.user_id}"  # noqa: E501

        if company_name not in companies:
            companies[company_name] = []
        companies[company_name].append((username, join_time))

    message_lines = ["🚀 *Сотрудники в организациях:*\n"]
    for company, users in companies.items():
        message_lines.append(f"\n🏢 *{company}*:")
        for i, (username, join_time) in enumerate(users, 1):
            message_lines.append(f"{i}. {username} - прибыл в {join_time}")

    await message.answer("\n".join(message_lines), parse_mode="Markdown")
