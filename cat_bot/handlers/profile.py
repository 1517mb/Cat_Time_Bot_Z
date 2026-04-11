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
    rank_info = await crud.get_user_rank_info(session, user_id)
    if not rank_info:
        return await message.answer(
            "📭 Ваш профиль пока пуст. Сделайте первый выезд через `/join`!",
            parse_mode="Markdown"
        )

    # Достаем переменные (адаптируй под свои названия полей в БД)
    current_level = rank_info.level
    current_exp = rank_info.experience
    # Опыт, необходимый для перехода на следующий уровень 
    # (в gamification.py у тебя должна быть формула, например: level * 1000)
    next_level_exp = await crud.get_next_level_exp(session, current_level)
    title = rank_info.level_title.title if rank_info.level_title else "Стажер"

    # 2. Генерируем прогресс-бар
    progress_bar = generate_progress_bar(current_exp, next_level_exp)

    # 3. Собираем статистику выездов (если есть такой метод)
    total_trips = await crud.get_total_trips_count(session, user_id)
    
    # 4. Получаем достижения
    achievements = await crud.get_user_achievements(session, user_id)
    ach_text = "\n".join([f"🏆 {a.achievement_name}" for a in achievements]) if achievements else "Пока нет 😢"

    # 5. Формируем красивую карточку
    msg_text = (
        f"👤 <b>Личное дело: @{message.from_user.username or message.from_user.first_name}</b>\n\n"
        f"🎖 <b>Звание:</b> {title} (Уровень {current_level})\n"
        f"📊 <b>Опыт:</b> {current_exp} / {next_level_exp}\n"
        f"[{progress_bar}]\n\n"
        f"💼 <b>Всего выездов:</b> {total_trips}\n\n"
        f"🏅 <b>Достижения:</b>\n{ach_text}"
    )

    await message.answer(msg_text, parse_mode="HTML")