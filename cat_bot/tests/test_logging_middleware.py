import asyncio
import logging
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, Update, User
from core.logger import ContextFilter, get_log_context
from middlewares.logging import UpdateLoggingMiddleware, log_update_error

handler_logger = logging.getLogger("tests.update_handler")


@pytest_asyncio.fixture
async def bot():
    bot = Bot(token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
    yield bot
    await bot.session.close()


@pytest.fixture
def dispatcher():
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(UpdateLoggingMiddleware())
    dispatcher.errors.register(log_update_error)
    return dispatcher


def make_update(update_id=101, chat_id=202, user_id=303):
    return Update(
        update_id=update_id,
        message=Message(
            message_id=404,
            date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            chat=Chat(id=chat_id, type="private"),
            from_user=User(id=user_id, is_bot=False, first_name="Example"),
            text="Private message contents",
        ),
    )


@pytest.mark.asyncio
async def test_update_error_is_logged_once_with_traceback_and_context(
    dispatcher, bot, caplog
):
    async def failing_handler(message):
        raise RuntimeError("Unexpected handler failure")

    dispatcher.message.register(failing_handler)

    result = await dispatcher.feed_update(bot, make_update())

    assert result is True
    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(errors) == 1
    record = errors[0]
    assert record.name == "middlewares.logging"
    assert record.exc_info[0] is RuntimeError
    assert record.exc_info[2] is not None
    assert record.update_id == 101
    assert record.event_type == "message"
    assert record.chat_id == 202
    assert record.user_id == 303
    assert "Unexpected handler failure" in caplog.text
    assert "Private message contents" not in caplog.text
    assert get_log_context() == {}


@pytest.mark.asyncio
async def test_handler_logs_receive_context_without_leaking_to_next_update(
    dispatcher, bot, caplog
):
    async def successful_handler(message):
        handler_logger.info("Handled update")

    dispatcher.message.register(successful_handler)
    context_filter = ContextFilter()
    caplog.handler.addFilter(context_filter)
    caplog.set_level(logging.INFO)
    try:
        await dispatcher.feed_update(bot, make_update())
        assert get_log_context() == {}
        await dispatcher.feed_update(bot, make_update(111, 222, 333))
        handler_logger.info("Outside update")
    finally:
        caplog.handler.removeFilter(context_filter)

    records = [record for record in caplog.records if record.name == handler_logger.name]
    assert len(records) == 3
    assert (records[0].update_id, records[0].chat_id, records[0].user_id) == (
        101, 202, 303
    )
    assert (records[1].update_id, records[1].chat_id, records[1].user_id) == (
        111, 222, 333
    )
    assert records[0].event_type == records[1].event_type == "message"
    assert getattr(records[2], "update_id", None) not in {101, 111}
    assert get_log_context() == {}


@pytest.mark.asyncio
async def test_cancellation_propagates_and_resets_context(dispatcher, bot, caplog):
    async def cancelled_handler(message):
        assert get_log_context()["update_id"] == 101
        raise asyncio.CancelledError()

    dispatcher.message.register(cancelled_handler)

    with pytest.raises(asyncio.CancelledError):
        await dispatcher.feed_update(bot, make_update())

    assert get_log_context() == {}
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.asyncio
async def test_concurrent_updates_keep_independent_context(dispatcher, bot):
    contexts = {}
    resumed_contexts = {}
    both_handlers_started = asyncio.Event()

    async def concurrent_handler(message):
        contexts[message.chat.id] = get_log_context()
        if len(contexts) == 2:
            both_handlers_started.set()
        await asyncio.wait_for(both_handlers_started.wait(), timeout=1)
        resumed_contexts[message.chat.id] = get_log_context()

    dispatcher.message.register(concurrent_handler)

    await asyncio.gather(
        dispatcher.feed_update(bot, make_update()),
        dispatcher.feed_update(bot, make_update(111, 222, 333)),
    )

    assert contexts[202]["update_id"] == 101
    assert contexts[222]["update_id"] == 111
    assert resumed_contexts == contexts
    assert get_log_context() == {}
