# middlewares/app_state.py — передача session_factory и scheduler в data
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class AppStateMiddleware(BaseMiddleware):
    """Добавляет session_factory и scheduler в data для хендлеров."""

    def __init__(
        self,
        session_factory: Any,
        scheduler: Any,
    ) -> None:
        self.session_factory = session_factory
        self.scheduler = scheduler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["session_factory"] = self.session_factory
        data["scheduler"] = self.scheduler
        return await handler(event, data)
