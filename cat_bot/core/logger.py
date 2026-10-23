import inspect
import logging
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import quote, quote_plus

from apscheduler.job import Job

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


@dataclass
class _Context:
    values: dict
    active: bool = True


_context: ContextVar[_Context | None] = ContextVar("log_context", default=None)
_CONTEXT_FIELDS = (
    "update_id", "event_type", "chat_id", "user_id", "job_id", "task",
    "operation", "provider", "error_type",
)
_TOKEN_PATTERN = re.compile(r"(?:bot)?\d{5,}(?::|%3[Aa])[A-Za-z0-9_-]{20,}")
_QUERY_SECRET_PATTERN = re.compile(
    r"(?i)(\b(?:appid|api[_-]?key|access[_-]?token|token)\s*=\s*)([^&\s\"'<>]+)"
)


def get_log_context() -> dict:
    """Возвращает контекст текущей асинхронной операции."""
    context = _context.get()
    return context.values.copy() if context is not None and context.active else {}


@contextmanager
def log_context(**values):
    """Добавляет поля только в текущую операцию, включая вложенные вызовы."""
    context = _Context({**get_log_context(), **values})
    token = _context.set(context)
    try:
        yield
    finally:
        # Отложенные фоновые задачи не должны наследовать уже завершённый update.
        context.active = False
        _context.reset(token)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for field, value in get_log_context().items():
            if not hasattr(record, field):
                setattr(record, field, value)

        # APScheduler уже пишет traceback: дополняем его запись без второго лога.
        if record.name.startswith("apscheduler.executors.") and isinstance(record.args, tuple):
            job = next((arg for arg in record.args if isinstance(arg, Job)), None)
            if job is not None:
                record.job_id = job.id
                record.task = getattr(job.func, "__name__", type(job.func).__name__)
                try:
                    arguments = inspect.signature(job.func).bind_partial(*job.args, **job.kwargs)
                    arguments.apply_defaults()
                    record.chat_id = arguments.arguments.get("chat_id")
                except (TypeError, ValueError):
                    pass

        if record.exc_info and record.exc_info[0] is not None:
            record.error_type = record.exc_info[0].__name__
        record.context = " ".join(
            f"{field}={getattr(record, field)}"
            for field in _CONTEXT_FIELDS
            if getattr(record, field, None) is not None
        ) or "-"
        return True


class RedactingFormatter(logging.Formatter):
    """Маскирует секреты во всей записи, включая traceback и цепочку исключений."""

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        for name in ("TELEGRAM_BOT_TOKEN", "OPENWEATHER_API_KEY"):
            secret = os.getenv(name)
            if secret:
                for value in {secret, quote(secret, safe=""), quote_plus(secret, safe="")}:
                    text = text.replace(value, "[REDACTED]")
        text = _TOKEN_PATTERN.sub("[REDACTED]", text)
        return _QUERY_SECRET_PATTERN.sub(r"\1[REDACTED]", text)


def setup_logging(log_dir: str | Path | None = None, level: int = logging.INFO) -> None:
    """Настраивает консоль, общий журнал и отдельный журнал ERROR/CRITICAL."""
    directory = Path(log_dir) if log_dir is not None else LOG_DIR
    directory.mkdir(parents=True, exist_ok=True)
    formatter = RedactingFormatter(
        "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d | "
        "%(context)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers[:]:
        if getattr(handler, "_cat_bot_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    handlers = [logging.StreamHandler()]
    for filename in ("cat_bot.log", "cat_bot_errors.log"):
        handlers.append(RotatingFileHandler(
            directory / filename, maxBytes=5 * 1024 * 1024,
            backupCount=5, encoding="utf-8",
        ))
    for index, handler in enumerate(handlers):
        handler._cat_bot_handler = True
        handler.setLevel(logging.ERROR if index == 2 else level)
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())
        root_logger.addHandler(handler)

    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger(__name__).info("Система логирования успешно инициализирована.")
