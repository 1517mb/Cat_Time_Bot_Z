from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from core import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "*CatBot v2.0 (FastAPI Edition)*\n\n"
        "😺👋 Привет! Вот список доступных команд:\n"
        "/help - Показать это сообщение\n"
        "/join <Организация> - Прибыть к указанной организации\n"
        "/leave - Покинуть текущую организацию\n"
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("join"))
async def cmd_join(message: Message,
                   command: CommandObject,
                   session: AsyncSession):
    if not command.args:
        await message.answer(
            "❌ *Ошибка!*\n"
            "Пожалуйста, укажите название организации после команды /join.",
            parse_mode="Markdown"
        )
        return

    company_name = command.args.strip()
    stmt = select(models.Company).where(models.Company.name == company_name)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()

    if company:
        await message.answer(f"🐱‍💻 *Вы прибыли в организацию `{company.name}`*",  # noqa
                             parse_mode="Markdown")
    else:
        await message.answer(f"🚨 Организация *{company_name}* не найдена. "
                             f"Добавим клавиатуру с выбором позже.",
                             parse_mode="Markdown")
