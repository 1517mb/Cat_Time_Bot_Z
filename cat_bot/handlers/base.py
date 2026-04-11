from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.bot_constants import BoteCfg

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(BoteCfg.HELP_TEXT, parse_mode="HTML")
