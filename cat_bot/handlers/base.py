from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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
