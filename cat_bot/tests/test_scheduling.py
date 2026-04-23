from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.filters import CommandObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.scheduling import (cmd_start_crypto, cmd_start_currency,
                                 cmd_start_leave_reminder, cmd_start_reminder,
                                 cmd_start_stats, cmd_start_weather,
                                 cmd_stop_crypto, cmd_stop_currency,
                                 cmd_stop_leave_reminder, cmd_stop_reminder,
                                 cmd_stop_scheduler, cmd_stop_stats,
                                 cmd_stop_weather)


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


@pytest.mark.parametrize(
    "cmd_func, args, exp_hour, exp_minute, exp_id, text",
    [
        (cmd_start_reminder, "09:30", 9, 30, "reminder", "<b>09:30</b>"),
        (cmd_start_weather, "07:30", 7, 30, "weather", "<b>07:30</b>"),
        (cmd_start_currency, "12:00", 12, 0, "currency", "<b>12:00</b>"),
        (cmd_start_crypto, "08:51", 8, 51, "crypto", "<b>08:51</b>"),
        (cmd_start_leave_reminder, "21:30", 21, 30, "leave_reminder", "<b>21:30</b>"),  # noqa: E501
    ],
)
@pytest.mark.asyncio
async def test_start_commands_success(
    mock_message,
    mock_scheduler,
    cmd_func,
    args,
    exp_hour,
    exp_minute,
    exp_id,
    text,
):
    """Единый тест для успешного запуска базовых рассылок."""
    command = MagicMock(spec=CommandObject)
    command.args = args
    bot = mock_message.bot

    await cmd_func(mock_message, command, mock_scheduler, bot)

    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args.kwargs
    assert call_kwargs["trigger"] == "cron"
    assert call_kwargs["hour"] == exp_hour
    assert call_kwargs["minute"] == exp_minute
    assert call_kwargs["id"] == f"{exp_id}_{mock_message.chat.id}"

    mock_message.answer.assert_called_once()
    assert text in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_stats_success(mock_message, mock_scheduler):
    """Отдельный тест для статистики (требует сессию БД)."""
    command = MagicMock(spec=CommandObject)
    command.args = "18:00"
    with patch("handlers.scheduling.async_session_maker"):
        await cmd_start_stats(mock_message, command, mock_scheduler)

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        assert call_kwargs["hour"] == 18
        assert call_kwargs["minute"] == 0
        assert call_kwargs["id"] == f"daily_stats_{mock_message.chat.id}"

        mock_message.answer.assert_called_once()
        ans = mock_message.answer.call_args[0][0]
        assert "Сводка по выездам активирована" in ans


@pytest.mark.asyncio
async def test_start_commands_no_args(mock_message, mock_scheduler):
    """Тест ошибки, когда пользователь не передал время."""
    command = MagicMock(spec=CommandObject)
    command.args = None
    bot = mock_message.bot

    await cmd_start_reminder(mock_message, command, mock_scheduler, bot)

    mock_scheduler.add_job.assert_not_called()
    assert "Укажите время" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_commands_invalid_format(mock_message, mock_scheduler):
    """Тест обработки неверного формата времени (например, 25:99)."""
    command = MagicMock(spec=CommandObject)
    command.args = "25:99"
    bot = mock_message.bot

    await cmd_start_reminder(mock_message, command, mock_scheduler, bot)

    mock_scheduler.add_job.assert_not_called()
    assert "Неверный формат" in mock_message.answer.call_args[0][0]


@pytest.mark.parametrize(
    "cmd_func, job_prefix",
    [
        (cmd_stop_reminder, "reminder"),
        (cmd_stop_weather, "weather"),
        (cmd_stop_currency, "currency"),
        (cmd_stop_crypto, "crypto"),
        (cmd_stop_stats, "daily_stats"),
        (cmd_stop_leave_reminder, "leave_reminder"),
    ],
)
@pytest.mark.asyncio
async def test_stop_commands_success(
    mock_message, mock_scheduler, cmd_func, job_prefix
):
    """Единый тест успешного отключения любой настроенной рассылки."""
    mock_scheduler.get_job.return_value = True
    await cmd_func(mock_message, mock_scheduler)
    expected_id = f"{job_prefix}_{mock_message.chat.id}"
    mock_scheduler.remove_job.assert_called_once_with(expected_id)
    assert "отключен" in mock_message.answer.call_args[0][0]


@pytest.mark.parametrize(
    "cmd_func",
    [
        cmd_stop_reminder,
        cmd_stop_weather,
        cmd_stop_currency,
        cmd_stop_crypto,
        cmd_stop_stats,
        cmd_stop_leave_reminder,
    ],
)
@pytest.mark.asyncio
async def test_stop_commands_not_found(
    mock_message, mock_scheduler, cmd_func
):
    """Единый тест отключения рассылки, если она не была настроена."""
    mock_scheduler.get_job.return_value = None
    await cmd_func(mock_message, mock_scheduler)
    mock_scheduler.remove_job.assert_not_called()
    assert "не была настроена" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_stop_scheduler_active_jobs(mock_message, mock_scheduler):
    """Тест: удаление нескольких активных задач в текущем чате."""
    chat_id = mock_message.chat.id
    job_1 = MagicMock(id=f"reminder_{chat_id}")
    job_2 = MagicMock(id=f"weather_{chat_id}")
    mock_scheduler.get_jobs.return_value = [job_1, job_2]

    await cmd_stop_scheduler(mock_message, mock_scheduler)

    assert mock_scheduler.remove_job.call_count == 2
    mock_scheduler.remove_job.assert_any_call(f"reminder_{chat_id}")
    mock_scheduler.remove_job.assert_any_call(f"weather_{chat_id}")
    assert "отключены" in mock_message.answer.call_args[0][0]
    assert "2 шт." in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_stop_scheduler_not_found(mock_message, mock_scheduler):
    """Тест: глобальная остановка, когда задач в чате нет."""
    mock_scheduler.get_jobs.return_value = []
    await cmd_stop_scheduler(mock_message, mock_scheduler)
    mock_scheduler.remove_job.assert_not_called()
    assert "не найдено" in mock_message.answer.call_args[0][0]
