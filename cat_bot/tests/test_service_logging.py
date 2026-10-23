import asyncio
import logging
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import SendMessage
from services import crypto, currency, it_news, seasons, tasks, weather


FETCH_CASES = [
    (currency, "fetch_currency_data", "cbr", "fetch_currency"),
    (crypto, "fetch_crypto_data", "coingecko", "fetch_crypto"),
    (it_news, "fetch_it_news", "habr", "fetch_it_news"),
    (weather, "fetch_owm_weather", "openweather", "fetch_weather"),
    (weather, "fetch_owm_forecast", "openweather", "fetch_forecast"),
    (weather, "fetch_mag_data", "noaa", "fetch_magnetic_data"),
]


async def _fetch(module, name, session, monkeypatch):
    monkeypatch.setattr(module.aiohttp, "ClientSession", lambda: session)
    if name in ("fetch_owm_weather", "fetch_owm_forecast"):
        return await getattr(module, name)(session, "Zelenograd", "test-key")
    if name == "fetch_mag_data":
        return await weather.fetch_mag_data(session)
    return await getattr(module, name)()


def _mock_session():
    session = MagicMock()
    session.__aenter__.return_value = session
    response = AsyncMock()
    response.status = 200
    response.raise_for_status = MagicMock()
    session.get.return_value.__aenter__.return_value = response
    return session, response


@pytest.mark.parametrize("module,name,provider,operation", FETCH_CASES)
async def test_fetch_timeout_is_warning_without_traceback(
    module, name, provider, operation, monkeypatch, caplog
):
    session, _ = _mock_session()
    session.get.return_value.__aenter__.side_effect = asyncio.TimeoutError(
        "Upstream timed out"
    )

    result = await _fetch(module, name, session, monkeypatch)

    assert result == ([] if module is it_news else None)
    record, = caplog.records
    assert record.name == module.__name__
    assert record.levelno == logging.WARNING
    assert record.exc_info is None
    assert record.provider == provider
    assert record.operation == operation
    assert "TimeoutError" in record.getMessage()
    assert "Upstream timed out" in record.getMessage()


@pytest.mark.parametrize("module,name,provider,operation", FETCH_CASES)
async def test_unexpected_fetch_error_preserves_traceback(
    module, name, provider, operation, monkeypatch, caplog
):
    session, response = _mock_session()
    response.json.side_effect = ValueError("Malformed JSON")
    response.text.return_value = "<rss>"

    result = await _fetch(module, name, session, monkeypatch)

    assert result == ([] if module is it_news else None)
    record, = caplog.records
    assert record.name == module.__name__
    assert record.levelno == logging.ERROR
    assert record.exc_info[0] is (ET.ParseError if module is it_news else ValueError)
    assert record.provider == provider
    assert record.operation == operation


@pytest.mark.parametrize("module,name,provider,operation", FETCH_CASES)
async def test_http_status_is_logged_without_response_body(
    module, name, provider, operation, monkeypatch, caplog
):
    session, response = _mock_session()
    response.status = 503
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=503,
        message="Response body must not be logged",
    )

    result = await _fetch(module, name, session, monkeypatch)

    assert result == ([] if module is it_news else None)
    record, = caplog.records
    assert record.levelno == logging.WARNING
    assert record.exc_info is None
    assert "503" in record.getMessage()
    assert "Response body" not in record.getMessage()
    assert record.provider == provider
    assert record.operation == operation
    response.json.assert_not_awaited()
    response.text.assert_not_awaited()


@pytest.mark.parametrize(
    "parse,data,provider,operation",
    [
        (weather.parse_current_weather, {"cod": 200, "weather": [{}]},
         "openweather", "parse_weather"),
        (weather.parse_forecast, {"cod": "200", "list": [{"weather": [{}]}]},
         "openweather", "parse_forecast"),
        (weather.parse_mag_data, [{}], "noaa", "parse_magnetic_data"),
    ],
)
def test_weather_parse_error_preserves_traceback(
    parse, data, provider, operation, caplog
):
    assert parse(data) is None

    record, = caplog.records
    assert record.name == "services.weather"
    assert record.levelno == logging.ERROR
    assert record.exc_info[0] is KeyError
    assert record.provider == provider
    assert record.operation == operation


@pytest.mark.parametrize("network_error", [True, False])
async def test_briefing_error_has_task_chat_and_correct_traceback(
    network_error, monkeypatch, caplog
):
    bot = AsyncMock()
    error = (
        TelegramNetworkError(
            method=SendMessage(chat_id=12345, text="Weather"),
            message="Request timeout error",
        )
        if network_error else ValueError("Unexpected formatting error")
    )
    bot.send_message.side_effect = error
    monkeypatch.setattr(tasks, "get_weather", AsyncMock(return_value="Weather"))

    await tasks.send_weather_briefing(bot, 12345)

    bot.send_message.assert_awaited_once()
    record, = caplog.records
    assert record.name == "services.tasks"
    assert record.task == "send_weather_briefing"
    assert record.chat_id == 12345
    assert record.operation == "run_task"
    assert record.funcName == "send_weather_briefing"
    if network_error:
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
        assert "TelegramNetworkError" in record.getMessage()
    else:
        assert record.levelno == logging.ERROR
        assert record.exc_info[1] is error


@pytest.mark.parametrize("network_error", [True, False])
async def test_season_notification_error_has_task_chat_context(
    network_error, monkeypatch, caplog
):
    session_maker = MagicMock()
    bot = AsyncMock()
    error = (
        TelegramNetworkError(
            method=SendMessage(chat_id=12345, text="Season"),
            message="Request timeout error",
        )
        if network_error else ValueError("Unexpected send error")
    )
    bot.send_message.side_effect = error
    monkeypatch.setattr(
        seasons, "create_season_if_needed",
        AsyncMock(return_value=(SimpleNamespace(name="Season"), True)),
    )

    await seasons.check_and_update_seasons_task(session_maker, bot, 12345)

    bot.send_message.assert_awaited_once()
    record, = caplog.records
    assert record.name == "services.seasons"
    assert record.task == "check_and_update_seasons_task"
    assert record.chat_id == 12345
    if network_error:
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
    else:
        assert record.levelno == logging.ERROR
        assert record.exc_info[1] is error
