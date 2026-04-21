import datetime
import re
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, any_state
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from core import crud, models
from services import gamification
from services.gamification import generate_progress_bar
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


class JoinProcess(StatesGroup):
    select_company = State()
    add_new_company = State()


def parse_time(time_str: str) -> Optional[datetime.time]:
    match = re.match(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$", time_str)
    if match:
        return datetime.time(
            hour=int(match.group(1)), minute=int(match.group(2))
        )
    return None


@router.message(Command("cancel"), StateFilter(any_state))
@router.message(F.text == "❌ Отмена", StateFilter(any_state))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.", reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("join"), StateFilter(any_state))
async def cmd_join(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"

    active = await crud.get_active_activity(session, user_id)
    if active:
        return await message.answer(
            "❌ Вы ещё не покинули предыдущую организацию."
        )

    if not command.args:
        return await message.answer(
            "❌ Укажите название: `/join Название`", parse_mode="Markdown"
        )

    company_name = command.args.strip()
    company = await crud.get_company_by_name(session, company_name)
    current_time_str = datetime.datetime.now().strftime("%H:%M")

    if company:
        await crud.create_activity(session, user_id, username, company.id)
        global_today_total = await crud.get_global_today_trips_count(session)
        if global_today_total == 1:
            session.add(
                models.Achievement(
                    user_id=user_id,
                    username=username,
                    achievement_name="Первая кровь",
                )
            )
            await message.answer("🏆 Получено: *Первая кровь*!",
                                 parse_mode="Markdown")

        await session.commit()
        await message.answer(
            f"🐱‍💻 Прибыли в: *{company.name}*\n"
            f"⏳ Время прибытия: {current_time_str}",
            parse_mode="Markdown"
        )
    else:
        similar = await crud.get_similar_companies(session, company_name)
        if similar:
            kb = [[KeyboardButton(text=name)] for name in similar]
            kb.append([KeyboardButton(text="➕ Добавить новую")])
            kb.append([KeyboardButton(text="❌ Отмена")])
            keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

            await message.answer(
                f"🚨 Организация *{company_name}* не найдена.\nМожет быть одна из этих?",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await state.set_state(JoinProcess.select_company)
        else:
            new_company = await crud.create_company(session, company_name)
            await crud.create_activity(session, user_id, username, new_company.id)
            global_today_total = await crud.get_global_today_trips_count(session)
            if global_today_total == 1:
                session.add(
                    models.Achievement(
                        user_id=user_id,
                        username=username,
                        achievement_name="Первая кровь",
                    )
                )
                await message.answer("🏆 Получено: *Первая кровь*!", 
                                     parse_mode="Markdown")

            await session.commit()
            await message.answer(
                f"✅ Создана новая организация: `{new_company.name}`\n"
                f"🐱‍💻 Вы прибыли в: *{new_company.name}*\n"
                f"⏳ Время прибытия: {current_time_str}",
                parse_mode="Markdown",
            )


@router.message(StateFilter(
        JoinProcess.select_company), F.text == "➕ Добавить новую")
async def btn_add_new_company(message: Message, state: FSMContext):
    await message.answer(
        "🐾 Введите название новой организации:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(JoinProcess.add_new_company)


@router.message(StateFilter(JoinProcess.select_company))
async def process_existing_company(
    message: Message, session: AsyncSession, state: FSMContext
):
    text = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"

    company = await crud.get_company_by_name(session, text)
    if not company:
        return await message.answer("❌ Ошибка: организация не найдена.")

    await crud.create_activity(session, user_id, username, company.id)
    global_today_total = await crud.get_global_today_trips_count(session)
    if global_today_total == 1:
        session.add(
            models.Achievement(
                user_id=user_id,
                username=username,
                achievement_name="Первая кровь",
            )
        )
        await message.answer("🏆 Получено: *Первая кровь*!", 
                             parse_mode="Markdown")

    await session.commit()
    await message.answer(
        f"🐱‍💻 Прибыли в: *{company.name}*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    await state.clear()


@router.message(StateFilter(JoinProcess.add_new_company))
async def process_new_company(
    message: Message, session: AsyncSession, state: FSMContext
):
    company_name = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"

    new_company = await crud.create_company(session, company_name)
    await crud.create_activity(session, user_id, username, new_company.id)
    global_today_total = await crud.get_global_today_trips_count(session)
    if global_today_total == 1:
        session.add(
            models.Achievement(
                user_id=user_id,
                username=username,
                achievement_name="Первая кровь",
            )
        )
        await message.answer("🏆 Получено: *Первая кровь*!", 
                             parse_mode="Markdown")

    await session.commit()
    await message.answer(
        f"✅ Создана новая организация: `{new_company.name}`\n"
        f"🐱‍💻 Вы прибыли в: *{new_company.name}*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    await state.clear()


@router.message(Command("leave"), StateFilter(any_state))
async def cmd_leave(
    message: Message, session: AsyncSession, state: FSMContext
):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"

    active = await crud.get_active_activity(session, user_id)
    if not active:
        return await message.answer("❌ У вас нет активного выезда.")

    active.leave_time = datetime.datetime.now(datetime.timezone.utc)
    daily_visits = await crud.get_today_trips_count(session, user_id)
    join_naive = active.join_time.replace(tzinfo=None)
    leave_naive = active.leave_time.replace(tzinfo=None)

    exp_earned = gamification.calculate_experience(
        join_naive, leave_naive, daily_visits
    )
    active.experience_gained = exp_earned

    new_achievements = await gamification.check_achievements(
        session, user_id, username, active
    )
    time_spent_td = leave_naive - join_naive
    rank, level_up, new_lvl = await crud.update_user_rank(
        session=session,
        user_id=user_id,
        username=username,
        exp_added=exp_earned,
        time_added=time_spent_td,
    )
    await session.commit()
    await session.refresh(active, ["company"])
    if rank:
        await session.refresh(rank, ["level_title"])
    spent_time = active.get_spent_time
    local_time = datetime.datetime.now().strftime("%H:%M")

    current_exp = rank.experience if rank else 0
    current_level = rank.level if rank else 1
    current_level_min = (
        rank.level_title.min_experience if rank and rank.level_title else 0
    )
    next_exp = await crud.get_next_level_exp(session, current_level)
    exp_in_level = current_exp - current_level_min
    exp_needed = next_exp - current_level_min if next_exp > 0 else 0
    if exp_needed > 0:
        p_bar = generate_progress_bar(exp_in_level, exp_needed)
    else:
        p_bar = generate_progress_bar(1, 1)
    msg_text = (
        f"🐾👋 *Вы покинули `{active.company.name}`*\n"
        f"⌛️ Время ухода: {local_time}.\n"
        f"⏳ Затраченное время: {spent_time}.\n"
        f"🔰 Получено опыта: +{exp_earned}\n"
        f"📊 Прогресс: {current_exp}/{next_exp}\n"
        f"`[{p_bar}]`"
    )

    if new_achievements:
        ach_lines = [f"• {ach}" for ach in new_achievements]
        ach_str = "\n".join(ach_lines)
        msg_text += f"\n\n🏆 *Достижения:*\n{ach_str}"

    if level_up and rank:
        title = rank.level_title.title if rank.level_title else "Неизвестно"
        msg_text += f"\n\n🎉 *Новый уровень: {new_lvl} lvl - {title}* 🎉"

    await message.answer(
        msg_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )


@router.message(Command("edit_start"), StateFilter(any_state))
async def cmd_edit_start(
    message: Message, command: CommandObject, 
    session: AsyncSession, state: FSMContext
):
    await state.clear()
    user_id = message.from_user.id
    active = await crud.get_active_activity(session, user_id)

    if not active:
        return await message.answer("❌ Нет активного выезда.")
    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/edit_start ЧЧ:ММ`", parse_mode="Markdown"
        )

    parsed = parse_time(command.args.strip())
    if not parsed:
        return await message.answer("❌ Неверный формат.")

    local_now = datetime.datetime.now().astimezone()
    local_new_join = local_now.replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )
    utc_new_join = local_new_join.astimezone(
        datetime.timezone.utc).replace(tzinfo=None)
    utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if utc_new_join > utc_now:
        return await message.answer(
            "❌ Ошибка: Время прибытия не может быть в будущем!")
    active.join_time = utc_new_join
    active.edited = True
    active.edit_count += 1
    await session.commit()
    await message.answer(
        f"✅ Время прибытия изменено на *{parsed.strftime('%H:%M')}*.",
        parse_mode="Markdown"
    )


@router.message(Command("edit_end"), StateFilter(any_state))
async def cmd_edit_end(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"

    active = await crud.get_active_activity(session, user_id)
    if not active:
        return await message.answer("❌ Нет активного выезда.")

    if not command.args:
        return await message.answer(
            "❌ Укажите время: `/edit_end ЧЧ:ММ`",
            parse_mode="Markdown",
        )

    parsed = parse_time(command.args.strip())
    if not parsed:
        return await message.answer("❌ Неверный формат.")

    local_now = datetime.datetime.now().astimezone()
    local_new_leave = local_now.replace(
        hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
    )
    utc_new_leave = local_new_leave.astimezone(datetime.timezone.utc).replace(
        tzinfo=None
    )
    join_utc = active.join_time.replace(tzinfo=None)

    if utc_new_leave < join_utc:
        return await message.answer(
            "❌ Время ухода не может быть раньше прибытия!"
        )

    utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if utc_new_leave > utc_now:
        return await message.answer("❌ Нельзя уйти в будущем!")

    active.leave_time = utc_new_leave
    active.edited = True
    active.edit_count += 1
    daily_visits = await crud.get_today_trips_count(session, user_id)
    exp_earned = gamification.calculate_experience(
        join_utc, utc_new_leave, daily_visits
    )
    active.experience_gained = exp_earned
    new_achievements = await gamification.check_achievements(
        session, user_id, username, active
    )

    time_spent_td = utc_new_leave - join_utc
    rank, level_up, new_lvl = await crud.update_user_rank(
        session=session,
        user_id=user_id,
        username=username,
        exp_added=exp_earned,
        time_added=time_spent_td,
    )
    await session.commit()
    await session.refresh(active, ["company"])
    if rank:
        await session.refresh(rank, ["level_title"])
    spent_time = active.get_spent_time
    leave_time_str = parsed.strftime("%H:%M")

    current_exp = rank.experience if rank else 0
    current_level = rank.level if rank else 1
    current_level_min = (
        rank.level_title.min_experience if rank and rank.level_title else 0
    )
    next_exp = await crud.get_next_level_exp(session, current_level)
    exp_in_level = current_exp - current_level_min
    exp_needed = next_exp - current_level_min if next_exp > 0 else 0
    if exp_needed > 0:
        p_bar = generate_progress_bar(exp_in_level, exp_needed)
    else:
        p_bar = generate_progress_bar(1, 1)

    msg_text = (
        f"🐾👋 *Вы покинули `{active.company.name}`* 📝 _(ручной ввод)_\n"
        f"⌛️ Время ухода: {leave_time_str}.\n"
        f"⏳ Затраченное время: {spent_time}.\n"
        f"🔰 Получено опыта: +{exp_earned}\n"
        f"📊 Прогресс: {current_exp}/{next_exp}\n"
        f"`[{p_bar}]`"
    )

    if new_achievements:
        ach_lines = [f"• {a}" for a in new_achievements]
        ach_str = "\n".join(ach_lines)
        msg_text += f"\n\n🏆 *Достижения:*\n{ach_str}"

    if level_up and rank:
        title = rank.level_title.title if rank.level_title else "Неизвестно"
        msg_text += f"\n\n🎉 *Новый уровень: {new_lvl} lvl - {title}* 🎉"

    await message.answer(
        msg_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
