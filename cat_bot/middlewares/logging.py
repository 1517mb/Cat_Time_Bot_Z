import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.types import ErrorEvent, Update
from aiogram.types.update import UpdateTypeLookupError
from core.logger import log_context

logger = logging.getLogger(__name__)


def _update_context(update: Update) -> dict[str, Any]:
    context = UserContextMiddleware.resolve_event_context(update)
    try:
        event_type = update.event_type
    except UpdateTypeLookupError:
        event_type = "unknown"
    return {
        "update_id": update.update_id,
        "event_type": event_type,
        "chat_id": context.chat_id,
        "user_id": context.user_id,
    }


class UpdateLoggingMiddleware(BaseMiddleware):
    """Attach update identifiers to logs for the duration of a handler."""

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        with log_context(**_update_context(event)):
            return await handler(event, data)


async def log_update_error(event: ErrorEvent) -> bool:
    """Log once and mark the error handled by aiogram's error pipeline."""
    error = event.exception
    context = _update_context(event.update)
    with log_context(**context):
        logger.error(
            "Unhandled Telegram update error: %s",
            type(error).__name__,
            exc_info=(type(error), error, error.__traceback__),
            extra=context,
        )
    return True
