# middlewares/rate_limit.py — ограничение частоты запросов пользователя
from __future__ import annotations

import time
from collections import abc
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# user_id -> список timestamp (время последних сообщений)
_user_timestamps: dict[int, list[float]] = {}
RATE_MSG = (
    "⚠️ Слишком много запросов.\nПопробуйте через пару секунд."
)


class RateLimitMiddleware(BaseMiddleware):
    """
    Ограничение: не более RATE_LIMIT_MESSAGES сообщений за RATE_LIMIT_PERIOD секунд.
    Учитываются только сообщения (message), не callback.
    """

    def __init__(self, config: Config) -> None:
        self.max_messages = config.RATE_LIMIT_MESSAGES
        self.period = config.RATE_LIMIT_PERIOD

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        user = event.from_user
        if not user:
            return await handler(event, data)

        now = time.monotonic()
        uid = user.id
        if uid not in _user_timestamps:
            _user_timestamps[uid] = []
        timestamps = _user_timestamps[uid]
        # Удалить старые
        cutoff = now - self.period
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        if len(timestamps) >= self.max_messages:
            try:
                await event.answer(RATE_MSG)
            except Exception as e:
                logger.debug("Rate limit answer: %s", e)
            return
        timestamps.append(now)
        return await handler(event, data)
