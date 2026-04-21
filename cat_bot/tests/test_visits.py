from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from handlers.visits import JoinProcess, cmd_cancel, cmd_join


@pytest.fixture
def mock_message():
    """Фикстура сообщения, чтобы не писать id и username каждый раз."""
    msg = AsyncMock()
    msg.from_user.id = 12345
    msg.from_user.username = "testuser"
    return msg


@pytest.fixture
def mock_state():
    return AsyncMock(spec=FSMContext)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_cmd_cancel(mock_message, mock_state):
    """Проверяем базовую команду отмены."""
    await cmd_cancel(mock_message, mock_state)
    mock_state.clear.assert_called_once()
    mock_message.answer.assert_called_once()
    assert "Действие отменено" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("handlers.visits.crud")
async def test_cmd_join_active_exists(
    mock_crud, mock_message, mock_state, mock_session
):
    """Сценарий: сотрудник пытается начать выезд, не закрыв предыдущий."""
    command = MagicMock(spec=CommandObject)
    mock_crud.get_active_activity = AsyncMock(return_value=True)
    await cmd_join(mock_message, command, mock_session, mock_state)
    assert "Вы ещё не покинули" in mock_message.answer.call_args[0][0]
    mock_crud.create_activity.assert_not_called()


@pytest.mark.asyncio
@patch("handlers.visits.crud")
async def test_cmd_join_no_args(
    mock_crud, mock_message, mock_state, mock_session
):
    """Сценарий: вызов /join без аргументов."""
    command = MagicMock(spec=CommandObject)
    command.args = None
    mock_crud.get_active_activity = AsyncMock(return_value=None)
    await cmd_join(mock_message, command, mock_session, mock_state)
    assert "Укажите название" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("handlers.visits.crud")
async def test_cmd_join_existing_company_first_blood(
    mock_crud, mock_message, mock_state, mock_session
):
    """Сценарий: успешный выезд + получение ачивки 'Первая кровь'."""
    command = MagicMock(spec=CommandObject)
    command.args = "Рога и Копыта"
    mock_crud.get_active_activity = AsyncMock(return_value=None)
    mock_company = MagicMock()
    mock_company.id = 99
    mock_company.name = "Рога и Копыта"
    mock_crud.get_company_by_name = AsyncMock(return_value=mock_company)
    mock_crud.get_global_today_trips_count = AsyncMock(return_value=1)
    mock_crud.create_activity = AsyncMock()
    await cmd_join(mock_message, command, mock_session, mock_state)
    mock_crud.create_activity.assert_called_once_with(
        mock_session, 12345, "testuser", 99
    )
    mock_session.add.assert_called_once()
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.achievement_name == "Первая кровь"
    assert mock_message.answer.call_count == 2
    assert "Первая кровь" in mock_message.answer.call_args_list[0][0][0]
    assert "Прибыли в" in mock_message.answer.call_args_list[1][0][0]


@pytest.mark.asyncio
@patch("handlers.visits.crud")
async def test_cmd_join_similar_companies(
    mock_crud, mock_message, mock_state, mock_session
):
    """Сценарий: организация не найдена, предлагаются похожие варианты."""
    command = MagicMock(spec=CommandObject)
    command.args = "Сбер"
    mock_crud.get_active_activity = AsyncMock(return_value=None)
    mock_crud.get_company_by_name = AsyncMock(return_value=None)
    mock_crud.get_similar_companies = AsyncMock(
        return_value=["Сбербанк", "Сбер-А"])
    await cmd_join(mock_message, command, mock_session, mock_state)
    mock_message.answer.assert_called_once()
    assert "не найдена" in mock_message.answer.call_args[0][0]
    mock_state.set_state.assert_called_once_with(JoinProcess.select_company)
