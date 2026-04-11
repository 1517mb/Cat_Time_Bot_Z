import datetime

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import any_state
from aiogram.types import Message
from core import crud
from services.gamification import generate_progress_bar
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(Command("profile"), StateFilter(any_state))
async def cmd_profile(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    season = await crud.get_current_season(session)
    season_text = ""
    if season:
        days_left = (season.end_date - datetime.datetime.now()).days if season.end_date else 0
        season_text = (
            f"🏆 <b>Текущий сезон:</b> {season.name}\n"
            f"⏳ <b>До конца сезона:</b> {days_left} дней\n\n"
        )
    rank_info = await crud.get_user_rank_info(session, user_id)

    if not rank_info:
        return await message.answer(
            "📭 Ваш профиль пока пуст. Сделайте первый выезд через `/join`!",
            parse_mode="Markdown",
        )
    current_level = rank_info.level
    current_exp = rank_info.experience

    level_title_obj = rank_info.level_title
    title = level_title_obj.title if level_title_obj else "Без звания"
    current_level_min = (
        level_title_obj.min_experience if level_title_obj else 0
    )

    next_level_exp = await crud.get_next_level_exp(session, current_level)
    exp_in_level = current_exp - current_level_min
    exp_needed = (
        next_level_exp - current_level_min if next_level_exp > 0 else 0
    )

    if exp_needed > 0:
        progress_bar = generate_progress_bar(exp_in_level, exp_needed)
        percent = int((exp_in_level / exp_needed) * 100)
    else:
        progress_bar = generate_progress_bar(1, 1)
        percent = 100
        next_level_exp = "MAX"
    total_time_seconds = rank_info.total_time.total_seconds() if rank_info.total_time else 0
    total_hours = int(total_time_seconds // 3600)
    total_minutes = int((total_time_seconds % 3600) // 60)
    time_str = f"{total_hours}ч {total_minutes}м"
    visits_count = rank_info.visits_count
    achievements = await crud.get_user_achievements(session, user_id)
    today = datetime.datetime.now().date()
    today_achievements = [
        a for a in achievements
        if getattr(a, 'acquired_at', datetime.datetime.now()).date() == today
    ]
    recent_achievements = today_achievements[-3:]
    if recent_achievements:
        ach_lines = [f"🏆 {a.achievement_name}" for a in recent_achievements]
        ach_text = "\n".join(ach_lines)
    else:
        ach_text = "Пока нет 😢"

    user_name = message.from_user.username or message.from_user.first_name
    msg_text = (
        f"{season_text}"
        f"👤 <b>Профиль: @{user_name}</b>\n\n"
        f"🎖 <b>Уровень:</b> {current_level}\n"
        f"🔰 <b>Звание:</b> {title}\n\n"
        f"📊 <b>Опыт:</b> {current_exp} / {next_level_exp}\n"
        f"`[{progress_bar}]` {percent}%\n\n"
        f"⏱ <b>Всего времени:</b> {time_str}\n"
        f"💼 <b>Всего выездов:</b> {visits_count}\n\n"
        f"🏅 <b>Достижения:</b>\n{ach_text}"
    )

    await message.answer(msg_text, parse_mode="HTML")
