from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.filters import CommandObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.scheduling import (cmd_start_crypto, cmd_start_currency,
                                 cmd_start_reminder, cmd_start_stats,
                                 cmd_start_weather, cmd_stop_scheduler,
                                 cmd_stop_stats)


@pytest.fixture
def mock_message():
    """Фикстура для создания мока объекта Message."""
    msg = AsyncMock()
    msg.chat.id = 123456789
    msg.bot = AsyncMock()
    return msg


@pytest.fixture
def mock_scheduler():
    """Фикстура для создания мока планировщика."""
    scheduler = MagicMock(spec=AsyncIOScheduler)
    scheduler.get_job.return_value = None
    return scheduler


@pytest.mark.asyncio
async def test_start_reminder_success(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "09:30"
    bot = mock_message.bot

    await cmd_start_reminder(mock_message, command, mock_scheduler, bot)
    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args.kwargs
    assert call_kwargs['trigger'] == "cron"
    assert call_kwargs['hour'] == 9
    assert call_kwargs['minute'] == 30
    assert call_kwargs['id'] == f"reminder_{mock_message.chat.id}"
    mock_message.answer.assert_called_once()
    assert "включены на <b>09:30</b>" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_reminder_no_args(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = None
    bot = mock_message.bot

    await cmd_start_reminder(mock_message, command, mock_scheduler, bot)

    mock_scheduler.add_job.assert_not_called()
    assert "Укажите время" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_reminder_invalid_format(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "25:99"
    bot = mock_message.bot

    await cmd_start_reminder(mock_message, command, mock_scheduler, bot)

    mock_scheduler.add_job.assert_not_called()
    assert "Неверный формат" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_stop_scheduler_job_exists(mock_message, mock_scheduler):
    mock_job_1 = MagicMock()
    mock_job_1.id = f"reminder_{mock_message.chat.id}"
    mock_job_2 = MagicMock()
    mock_job_2.id = f"weather_{mock_message.chat.id}"
    mock_scheduler.get_jobs.return_value = [mock_job_1, mock_job_2]
    await cmd_stop_scheduler(mock_message, mock_scheduler)
    assert mock_scheduler.remove_job.call_count == 2
    mock_scheduler.remove_job.assert_any_call(
        f"reminder_{mock_message.chat.id}")
    mock_scheduler.remove_job.assert_any_call(
        f"weather_{mock_message.chat.id}")
    assert "отключены" in mock_message.answer.call_args[0][0]
    assert "2 шт." in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_stop_scheduler_job_not_found(mock_message, mock_scheduler):
    mock_scheduler.get_jobs.return_value = []
    await cmd_stop_scheduler(mock_message, mock_scheduler)
    mock_scheduler.remove_job.assert_not_called()
    assert "не найдено" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_stats_success(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "18:00"
    with patch("handlers.scheduling.async_session_maker"):
        await cmd_start_stats(mock_message, command, mock_scheduler)

        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args.kwargs
        assert call_args['hour'] == 18
        assert call_args['minute'] == 00
        mock_message.answer.assert_called_once()
        assert "Сводка по выездам активирована" in mock_message.answer.call_args[0][0]  # noqa: E501


@pytest.mark.asyncio
async def test_start_stats_flexible_time_format(mock_message, mock_scheduler):
    """Тест проверяет, что исправленная регулярка принимает время
       в формате ЧЧ:ММ без лидирующего нуля."""
    command = MagicMock(spec=CommandObject)
    command.args = "7:50"
    with patch("handlers.scheduling.async_session_maker"):
        await cmd_start_stats(mock_message, command, mock_scheduler)
        mock_scheduler.add_job.assert_called_once()
        assert "Сводка по выездам активирована" in mock_message.answer.call_args[0][0]  # noqa: E501


@pytest.mark.asyncio
async def test_stop_stats(mock_message, mock_scheduler):
    mock_scheduler.get_job.return_value = True
    await cmd_stop_stats(mock_message, mock_scheduler)
    mock_scheduler.remove_job.assert_called_once_with(
        f"daily_stats_{mock_message.chat.id}")
    assert "отключена" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_crypto_success(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "08:51"
    bot = mock_message.bot
    await cmd_start_crypto(mock_message, command, mock_scheduler, bot)
    mock_scheduler.add_job.assert_called_once()
    assert "установлена на <b>08:51</b>" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_weather_success(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "07:30"
    bot = mock_message.bot

    await cmd_start_weather(mock_message, command, mock_scheduler, bot)
    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args.kwargs
    assert call_kwargs['hour'] == 7
    assert call_kwargs['minute'] == 30
    assert call_kwargs['id'] == f"weather_{mock_message.chat.id}"
    mock_message.answer.assert_called_once()
    assert "включена на <b>07:30</b>" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_currency_success(mock_message, mock_scheduler):
    command = MagicMock(spec=CommandObject)
    command.args = "12:00"
    bot = mock_message.bot

    await cmd_start_currency(mock_message, command, mock_scheduler, bot)
    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args.kwargs
    assert call_kwargs['hour'] == 12
    assert call_kwargs['minute'] == 0
    assert call_kwargs['id'] == f"currency_{mock_message.chat.id}"
    mock_message.answer.assert_called_once()
    assert "установлена на <b>12:00</b>" in mock_message.answer.call_args[0][0]
