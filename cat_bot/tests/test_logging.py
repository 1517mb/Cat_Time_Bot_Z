import asyncio
import logging
from datetime import datetime, timezone
from functools import partial
from logging.handlers import RotatingFileHandler
from urllib.parse import quote

import pytest
from apscheduler.executors.base import run_coroutine_job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.logger import (ContextFilter, RedactingFormatter, get_log_context,
                         log_context, setup_logging)


@pytest.fixture
def logging_setup():
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    quiet_loggers = [logging.getLogger(name) for name in ("apscheduler", "aiogram.event")]
    original_levels = [logger.level for logger in quiet_loggers]
    yield
    for handler in root.handlers[:]:
        if handler not in original_handlers:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(original_level)
    for logger, level in zip(quiet_loggers, original_levels):
        logger.setLevel(level)


def test_logging_files_preserve_traceback_and_redact_secrets(tmp_path, monkeypatch, logging_setup):
    secret = "weather-secret-for-logging-test"
    monkeypatch.setenv("OPENWEATHER_API_KEY", secret)
    setup_logging(tmp_path)
    logger = logging.getLogger("cat_bot.logging_test")

    logger.warning("Network temporarily unavailable")
    with log_context(chat_id=123, operation="parse_weather"):
        try:
            raise ValueError(f"Invalid data from https://example.com?appid={secret}")
        except ValueError:
            logger.exception("Weather processing failed")

    general = (tmp_path / "cat_bot.log").read_text(encoding="utf-8")
    errors = (tmp_path / "cat_bot_errors.log").read_text(encoding="utf-8")
    assert "Network temporarily unavailable" in general
    assert "Network temporarily unavailable" not in errors
    for content in (general, errors):
        assert "Traceback (most recent call last)" in content
        assert "ValueError: Invalid data" in content
        assert "chat_id=123" in content
        assert "operation=parse_weather" in content
        assert "cat_bot.logging_test" in content
        assert secret not in content
        assert "[REDACTED]" in content


def test_repeated_setup_closes_own_files_and_preserves_other_handlers(tmp_path, logging_setup):
    root = logging.getLogger()
    foreign_handler = logging.NullHandler()
    root.addHandler(foreign_handler)
    setup_logging(tmp_path)
    old_handlers = [handler for handler in root.handlers if getattr(handler, "_cat_bot_handler", False)]

    setup_logging(tmp_path)

    assert foreign_handler in root.handlers
    assert all(handler not in root.handlers for handler in old_handlers)
    assert all(handler._closed for handler in old_handlers)
    assert all(handler.stream is None for handler in old_handlers if isinstance(handler, RotatingFileHandler))
    own_handlers = [handler for handler in root.handlers if getattr(handler, "_cat_bot_handler", False)]
    assert len(own_handlers) == 3
    logging.getLogger("cat_bot.logging_test").error("Exactly one error record")
    assert (tmp_path / "cat_bot_errors.log").read_text(encoding="utf-8").count("Exactly one error record") == 1


def test_redaction_covers_chained_exceptions_and_url_encoded_values(monkeypatch):
    bot_token = "123456789:" + "A" * 35
    api_key = "encoded/key+with space"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", bot_token)
    monkeypatch.setenv("OPENWEATHER_API_KEY", api_key)
    try:
        try:
            raise ValueError(f"https://example.com?appid={quote(api_key, safe='')}")
        except ValueError as error:
            raise RuntimeError(f"https://api.telegram.org/bot{bot_token}/sendPhoto") from error
    except RuntimeError:
        import sys
        record = logging.LogRecord("test", logging.ERROR, __file__, 1, "Request failed", (), sys.exc_info())

    formatted = RedactingFormatter("%(message)s").format(record)

    assert "ValueError" in formatted and "RuntimeError" in formatted
    assert "direct cause" in formatted
    assert bot_token not in formatted
    assert quote(api_key, safe="") not in formatted
    assert "[REDACTED]" in formatted


def test_redaction_masks_unknown_tokens_and_query_keys(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    unknown_token = "987654321:" + "B" * 35
    message = f"https://api.telegram.org/bot{unknown_token}/sendPhoto?api_key=hidden-key&access_token=hidden-access"
    record = logging.LogRecord("test", logging.WARNING, __file__, 1, message, (), None)

    formatted = RedactingFormatter("%(message)s").format(record)

    assert unknown_token not in formatted
    assert "hidden-key" not in formatted
    assert "hidden-access" not in formatted
    assert "sendPhoto" in formatted


@pytest.mark.asyncio
async def test_completed_context_is_not_reused_by_delayed_task():
    release = asyncio.Event()

    async def delayed_operation():
        await release.wait()
        return get_log_context()

    with log_context(update_id=12, chat_id=34):
        task = asyncio.create_task(delayed_operation())
    release.set()

    assert await task == {}
    assert get_log_context() == {}


@pytest.mark.parametrize("use_partial", [False, True])
@pytest.mark.asyncio
async def test_scheduler_failure_has_context_and_one_traceback(caplog, use_partial):
    async def failing_job(chat_id):
        raise ValueError("Scheduled job failed")

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    function = partial(failing_job, chat_id=42) if use_partial else failing_job
    job = scheduler.add_job(
        function, "interval", seconds=60, id="logging_test_42",
        kwargs={} if use_partial else {"chat_id": 42}, misfire_grace_time=None,
    )
    context_filter = ContextFilter()
    caplog.handler.addFilter(context_filter)
    try:
        with caplog.at_level(logging.ERROR, logger="apscheduler.executors.default"):
            events = await run_coroutine_job(
                job, "default", [datetime.now(timezone.utc)], "apscheduler.executors.default"
            )
    finally:
        caplog.handler.removeFilter(context_filter)

    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert errors[0].job_id == "logging_test_42"
    assert errors[0].chat_id == 42
    assert errors[0].exc_info[0] is ValueError
    assert events[0].job_id == "logging_test_42"
