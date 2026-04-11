import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from core import crud, models
from services import gamification
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


class JoinProcess(StatesGroup):
    select_company = State()
    add_new_company = State()


def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена любого действия"""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove())


@router.message(Command("join"))
async def cmd_join(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    active = await crud.get_active_activity(session, user_id)
    if active:
        return await message.answer(
            "❌ Вы ещё не покинули предыдущую организацию."
        )

    if not command.args:
        return await message.answer(
            "❌ Укажите название организации: `/join Название`",
            parse_mode="Markdown",
        )

    company_name = command.args.strip()
    company = await crud.get_company_by_name(session, company_name)

    if company:
        await crud.create_activity(
            session, user_id, username, company.id
        )
        today_total = await crud.get_today_trips_count(session, user_id)
        if today_total == 1:
            session.add(
                models.Achievement(
                    user_id=user_id,
                    username=username,
                    achievement_name="Первая кровь",
                )
            )
            await message.answer(
                "🏆 Получено достижение: *Первая кровь*!",
                parse_mode="Markdown",
            )

        await session.commit()
        await message.answer(
            f"🐱‍💻 Прибыли в: *{company.name}*",
            parse_mode="Markdown",
        )

    else:
        similar = await crud.get_similar_companies(session, company_name)
        if similar:
            kb = [[KeyboardButton(text=name)] for name in similar]
            kb.append([KeyboardButton(text="➕ Добавить новую")])
            keyboard = ReplyKeyboardMarkup(
                keyboard=kb, resize_keyboard=True
            )

            await message.answer(
                f"🚨 Организация *{company_name}* не найдена. "
                f"Может быть одна из этих?",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            await state.set_state(JoinProcess.select_company)
        else:
            new_company = await crud.create_company(session, company_name)
            await crud.create_activity(
                session, user_id, username, new_company.id
            )
            today_total = await crud.get_today_trips_count(
                session, user_id
            )
            if today_total == 1:
                session.add(
                    models.Achievement(
                        user_id=user_id,
                        username=username,
                        achievement_name="Первая кровь",
                    )
                )
                await message.answer(
                    "🏆 Получено достижение: *Первая кровь*!",
                    parse_mode="Markdown",
                )

            await session.commit()
            await message.answer(
                f"✅ Создана новая организация: `{new_company.name}`\n"
                f"🐱‍💻 Вы прибыли в: *{new_company.name}*",
                parse_mode="Markdown",
            )


@router.message(JoinProcess.select_company)
async def process_company_selection(message: Message,
                                    session: AsyncSession,
                                    state: FSMContext):
    """Обрабатываем нажатие на кнопку выбора компании"""
    user_id = message.from_user.id
    selected_text = message.text

    if selected_text == "➕ Добавить новую организацию":
        await message.answer(
            "🐾 Пожалуйста, введите название новой организации:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(JoinProcess.add_new_company)
        return

    company = await crud.get_company_by_name(session, selected_text)
    if not company:
        await message.answer(
            "Ошибка: организация не найдена."
            " Попробуйте еще раз или нажмите Отмена.")
        return
    await crud.create_activity(session, user_id, message.from_user.username, company.id)
    local_time = datetime.datetime.now().strftime('%H:%M')

    await message.answer(
        f"🐱‍💻 *Вы прибыли в организацию `{company.name}`*\n"
        f"⏳ Время прибытия: {local_time}.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await state.clear()


@router.message(JoinProcess.add_new_company)
async def process_new_company(message: Message, 
                              session: AsyncSession,
                              state: FSMContext):
    """Обрабатываем создание новой компании"""
    if message.text.startswith("Создать: "):
        company_name = message.text.replace("Создать: ", "").strip()
    else:
        company_name = message.text.strip()
    new_company = await crud.create_company(session, company_name)
    await crud.create_activity(session,
                               message.from_user.id,
                               message.from_user.username, new_company.id)
    local_time = datetime.datetime.now().strftime('%H:%M')
    await message.answer(
        f"✅ Организация `{company_name}` успешно создана!\n\n"
        f"🐱‍💻 *Вы прибыли в `{company_name}`*\n"
        f"⏳ Время прибытия: {local_time}.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await state.clear()


@router.message(Command("leave"))
async def cmd_leave(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    active_activity = await crud.get_active_activity(session, user_id)
    if not active_activity:
        return await message.answer("❌ *Ошибка!*\nВы не прибыли ни к одной организации.", parse_mode="Markdown")
    current_time = datetime.datetime.now(datetime.timezone.utc)
    active_activity.leave_time = current_time
    daily_visits = await crud.get_today_trips_count(session, user_id)
    exp_earned = gamification.calculate_experience(
        active_activity.join_time.replace(tzinfo=None),
        active_activity.leave_time.replace(tzinfo=None),
        daily_visits
    )
    active_activity.experience_gained = exp_earned
    new_achievements = await gamification.check_achievements(
        session, user_id, username, active_activity)
    time_spent_td = active_activity.leave_time.replace(tzinfo=None) - active_activity.join_time.replace(tzinfo=None)
    rank, level_up, new_level = await crud.update_user_rank(
        session=session,
        user_id=user_id,
        username=username,
        exp_added=exp_earned,
        time_added=time_spent_td
    )
    await session.commit()
    await session.refresh(active_activity, ['company'])

    spent_time = active_activity.get_spent_time
    local_time = datetime.datetime.now().strftime('%H:%M')
    msg_text = (
        f"🐾👋 *Вы покинули организацию `{active_activity.company.name}`*\n"
        f"⌛️ Время ухода: {local_time}.\n"
        f"⏳ Затраченное время: {spent_time}.\n"
        f"🔰 Получено опыта: {exp_earned}"
    )
    if new_achievements:
        achievements_str = "\n".join([f"• {ach}" for ach in new_achievements])
        msg_text += f"\n\n🏆 *Получены новые достижения:*\n{achievements_str}"
    if level_up and rank:
        await session.refresh(rank, ['level_title'])
        title_name = rank.level_title.title if rank.level_title else "Неизвестно"
        msg_text += (
            f"\n\n🎉 *Поздравляем с повышением уровня!* 🎉\n"
            f"🏆 Новый уровень: *{new_level} lvl - {title_name}*"
        )

    await message.answer(msg_text, parse_mode="Markdown")
