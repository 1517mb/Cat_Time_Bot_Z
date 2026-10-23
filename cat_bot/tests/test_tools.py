import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import SendMessage, SendPhoto
from handlers.tools import CAT_CAPTION, CAT_ERROR_MSG, cmd_mew

CAT_URL = "https://cdn.example.com/cat.jpg"


@pytest.mark.asyncio
async def test_mew_sends_public_url_to_telegram():
    message = AsyncMock()

    with patch("handlers.tools._fetch_cat_image", return_value=CAT_URL):
        await cmd_mew(message)

    message.answer_photo.assert_awaited_once_with(
        photo=CAT_URL, caption=CAT_CAPTION, parse_mode="HTML"
    )
    message.answer.assert_not_awaited()


@pytest.mark.parametrize(
    "error",
    [asyncio.TimeoutError(), aiohttp.ClientConnectionError("Connection failed")],
)
@pytest.mark.asyncio
async def test_mew_reports_cat_api_network_failure(error):
    message = AsyncMock()

    with patch("handlers.tools._fetch_cat_image", side_effect=error):
        await cmd_mew(message)

    message.answer_photo.assert_not_awaited()
    message.answer.assert_awaited_once_with(CAT_ERROR_MSG)


@pytest.mark.parametrize("error_type", [TelegramNetworkError, TelegramBadRequest])
@pytest.mark.asyncio
async def test_mew_reports_photo_send_failure_without_retry(error_type):
    message = AsyncMock()
    message.answer_photo.side_effect = error_type(
        method=SendPhoto(chat_id=123, photo=CAT_URL), message="Photo unavailable"
    )

    with patch("handlers.tools._fetch_cat_image", return_value=CAT_URL):
        await cmd_mew(message)

    message.answer_photo.assert_awaited_once()
    message.answer.assert_awaited_once_with(CAT_ERROR_MSG)


@pytest.mark.asyncio
async def test_mew_logs_failure_to_send_error_message(caplog):
    message = AsyncMock()
    message.answer.side_effect = TelegramNetworkError(
        method=SendMessage(chat_id=123, text=CAT_ERROR_MSG),
        message="Request timeout error",
    )

    with patch("handlers.tools._fetch_cat_image", side_effect=asyncio.TimeoutError()):
        await cmd_mew(message)

    message.answer.assert_awaited_once_with(CAT_ERROR_MSG)
    assert "Failed to send cat error message" in caplog.text


@pytest.mark.parametrize(
    "payload",
    [[], {}, None, [{}], [{"url": None}], [{"url": 42}], [{"url": ""}]],
)
@pytest.mark.asyncio
async def test_mew_reports_invalid_cat_api_response(payload):
    message = AsyncMock()
    response = MagicMock()
    response.json = AsyncMock(return_value=payload)
    session = MagicMock()
    session.get.return_value.__aenter__.return_value = response

    with patch("handlers.tools.aiohttp.ClientSession") as client_session:
        client_session.return_value.__aenter__.return_value = session
        await cmd_mew(message)

    message.answer_photo.assert_not_awaited()
    message.answer.assert_awaited_once_with(CAT_ERROR_MSG)


@pytest.mark.asyncio
async def test_mew_preserves_cancellation():
    message = AsyncMock()

    with patch("handlers.tools._fetch_cat_image", side_effect=asyncio.CancelledError()):
        with pytest.raises(asyncio.CancelledError):
            await cmd_mew(message)

    message.answer_photo.assert_not_awaited()
    message.answer.assert_not_awaited()
