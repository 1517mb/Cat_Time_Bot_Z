import logging

import aiohttp
from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import Message, URLInputFile

CAT_API_URL = "https://api.thecatapi.com/v1/images/search"
CAT_ERROR_MSG = "😿 Кот-сервис временно недоступен (код: MEOW_503)."
CAT_CAPTION = "🐾 <i>Образец мурчания успешно получен!</i>"
GROUP_TYPES = {"group", "supergroup", "channel"}

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("get_chat_info"))
async def cmd_get_chat_info(message: Message) -> None:
    """Отправляет подробную информацию о чате."""
    chat_id = message.chat.id

    try:
        full_chat = await message.bot.get_chat(chat_id)
    except TelegramAPIError as error:
        logger.warning("Failed to get chat %s: %s", chat_id, error)
        await message.answer(
            f"❌ Ошибка доступа к чату: <code>{error}</code>",
            parse_mode="HTML"
        )
        return

    info = _build_basic_info(full_chat, chat_id)
    _add_username_or_name(info, full_chat)
    _add_description(info, full_chat)
    await _add_member_count(info, message.bot, chat_id, full_chat.type)
    _add_technical_params(info, full_chat)

    await message.answer(
        "\n".join(info),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


def _build_basic_info(chat, chat_id: int) -> list[str]:
    """Формирует базовую информацию о чате."""
    return [
        "<b>📊 Полная информация о чате:</b>",
        f"🆔 <b>ID:</b> <code>{chat_id}</code>",
        f"📦 Тип: <code>{chat.type}</code>",
        f"📝 Название: <b>{chat.title or '—'}</b>",
    ]


def _add_username_or_name(info: list[str], chat) -> None:
    """Добавляет username или имя пользователя."""
    if chat.username:
        info.append(f"🔗 Username: <code>@{chat.username}</code>")
    elif chat.type == "private":
        first = chat.first_name or ""
        last = chat.last_name or ""
        name = f"{first} {last}".strip()
        info.append(f"👤 Имя: <b>{name or '—'}</b>")


def _add_description(info: list[str], chat) -> None:
    """Добавляет описание чата, если есть."""
    if chat.description:
        info.append(f"📖 Описание: {chat.description}")


async def _add_member_count(
    info: list[str],
    bot,
    chat_id: int,
    chat_type: str
) -> None:
    """Добавляет количество участников для групп/каналов."""
    if chat_type not in GROUP_TYPES:
        return

    try:
        count = await bot.get_chat_member_count(chat_id)
        info.append(f"👥 Участников: <code>{count}</code>")
    except TelegramAPIError as error:
        logger.debug("Cannot get member count for %s: %s", chat_id, error)
        info.append("👥 Участников: <i>нет доступа</i>")


def _add_technical_params(info: list[str], chat) -> None:
    """Добавляет технические параметры чата."""
    tech = []

    if chat.slow_mode_delay:
        tech.append(
            f"⏱ Медленный режим: "
            f"<code>{chat.slow_mode_delay} сек</code>"
        )
    if chat.message_auto_delete_time:
        tech.append(
            f"🗑 Автоудаление: "
            f"<code>{chat.message_auto_delete_time} сек</code>"
        )
    if chat.has_protected_content:
        tech.append("🛡 Защита контента: <b>ВКЛ</b>")
    if chat.has_visible_history is not None:
        status = "Видна" if chat.has_visible_history else "Скрыта"
        tech.append(f"👁 История: <b>{status}</b>")
    if chat.invite_link:
        tech.append(f"🔗 Ссылка: <code>{chat.invite_link}</code>")
    if chat.linked_chat_id:
        tech.append(f"🔗 Связанный чат: <code>{chat.linked_chat_id}</code>")
    if chat.sticker_set_name:
        tech.append(f"🎨 Стикеры: <code>{chat.sticker_set_name}</code>")

    if tech:
        info.append("\n<b>⚙️ Технические параметры:</b>")
        info.extend(tech)


@router.message(Command("mew"))
async def cmd_mew(message: Message) -> None:
    """Отправляет случайное фото котика."""
    try:
        cat_url = await _fetch_cat_image()
        photo = URLInputFile(cat_url)
        await message.answer_photo(
            photo,
            caption=CAT_CAPTION,
            parse_mode="HTML"
        )
    except aiohttp.ClientError as error:
        logger.error("Cat API request failed: %s", error)
        await message.answer(CAT_ERROR_MSG)
    except (KeyError, IndexError) as error:
        logger.error("Unexpected Cat API response: %s", error)
        await message.answer(CAT_ERROR_MSG)


async def _fetch_cat_image() -> str:
    """Загружает URL случайного котика из API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(CAT_API_URL) as response:
            response.raise_for_status()
            data = await response.json()
            return data[0]["url"]
