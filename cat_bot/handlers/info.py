from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


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
