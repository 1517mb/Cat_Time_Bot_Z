from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.tasks import (get_plural_days, send_leave_reminder_task,
                            send_transport_reminder)


@pytest.mark.parametrize(
    "days, expected",
    [
        (1, "день"), (21, "день"), (31, "день"),
        (2, "дня"), (3, "дня"), (4, "дня"), (22, "дня"),
        (0, "дней"), (5, "дней"), (10, "дней"),
        (11, "дней"), (14, "дней"), (25, "дней"),
    ],
)
def test_get_plural_days(days, expected):
    """Проверяем правильность склонения слова 'день'."""
    assert get_plural_days(days) == expected


@pytest.fixture
def mock_bot():
    """Фикстура для создания мока объекта Bot."""
    return AsyncMock()


@pytest.mark.asyncio
@patch("services.tasks.date")
async def test_reminder_last_day_of_month(mock_date, mock_bot):
    """Тест: сегодня последний день месяца."""
    mock_date.today.return_value = date(2026, 4, 30)
    await send_transport_reminder(mock_bot, 12345)
    mock_bot.send_message.assert_called_once()
    sent_text = mock_bot.send_message.call_args[0][1]
    assert "Сегодня последний день месяца" in sent_text


@pytest.mark.asyncio
@patch("services.tasks.date")
@patch("services.tasks.BotRemidersCfg")
async def test_reminder_one_day_left(mock_cfg, mock_date, mock_bot):
    """Тест: до конца месяца остался 1 день."""
    mock_date.today.return_value = date(2026, 4, 29)
    mock_cfg.TRANSPORT_REMINDER_TEMPLATES = ["{verb} {days} {day_word}"]
    await send_transport_reminder(mock_bot, 12345)
    mock_bot.send_message.assert_called_once()
    sent_text = mock_bot.send_message.call_args[0][1]
    assert sent_text == "Остался 1 день"


@pytest.mark.asyncio
@patch("services.tasks.date")
@patch("services.tasks.BotRemidersCfg")
async def test_reminder_few_days_left(mock_cfg, mock_date, mock_bot):
    """Тест: до конца месяца осталось несколько дней (2-4)."""
    mock_date.today.return_value = date(2026, 4, 27)
    mock_cfg.TRANSPORT_REMINDER_TEMPLATES = ["{verb} {days} {day_word}"]
    await send_transport_reminder(mock_bot, 12345)
    mock_bot.send_message.assert_called_once()
    sent_text = mock_bot.send_message.call_args[0][1]
    assert sent_text == "Осталось 3 дня"


@pytest.mark.asyncio
@patch("services.tasks.date")
@patch("services.tasks.BotRemidersCfg")
async def test_reminder_many_days_left(mock_cfg, mock_date, mock_bot):
    """Тест: до конца месяца осталось 11 дней (исключение)."""
    mock_date.today.return_value = date(2026, 4, 19)
    mock_cfg.TRANSPORT_REMINDER_TEMPLATES = ["{verb} {days} {day_word}"]
    await send_transport_reminder(mock_bot, 12345)
    mock_bot.send_message.assert_not_called()


@pytest.fixture
def mock_session_maker():
    """Фикстура для мока асинхронного session_maker."""
    maker = MagicMock()
    session = AsyncMock()
    maker.return_value.__aenter__.return_value = session
    maker.return_value.__aexit__.return_value = None
    return maker


@pytest.mark.asyncio
@patch("services.tasks.get_all_active_activities")
async def test_leave_reminder_no_activities(
    mock_get_all, mock_bot, mock_session_maker
):
    """Тест: нет активных выездов, бот ничего не отправляет."""
    mock_get_all.return_value = []
    await send_leave_reminder_task(mock_bot, 12345, mock_session_maker)
    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
@patch("services.tasks.get_all_active_activities")
async def test_leave_reminder_with_activities(
    mock_get_all, mock_bot, mock_session_maker
):
    """Тест: есть активные выезды, бот отправляет список 'забывашек'."""
    mock_activity = MagicMock()
    mock_activity.username = "test_user_forgot"
    mock_activity.user_id = 999
    mock_activity.company.name = "Рога и Копыта"
    mock_get_all.return_value = [mock_activity]
    await send_leave_reminder_task(mock_bot, 12345, mock_session_maker)
    mock_bot.send_message.assert_called_once()
    sent_text = mock_bot.send_message.call_args.kwargs['text']
    assert "@test_user_forgot" in sent_text
    assert "Рога и Копыта" in sent_text
    assert "на объектах" in sent_text
