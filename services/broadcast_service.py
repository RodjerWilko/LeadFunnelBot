# services/broadcast_service.py — безопасная рассылка с задержкой и обработкой ошибок
from __future__ import annotations

import asyncio
from typing import Any

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import Config
from services.user_service import get_all_users_telegram_ids
from utils.logger import get_logger

logger = get_logger(__name__)


async def get_all_users_for_broadcast(session: AsyncSession) -> list[int]:
    """Получить список telegram_id всех пользователей для рассылки."""
    return await get_all_users_telegram_ids(session)


async def send_broadcast(
    bot: Any,
    session_factory: Any,
    text: str,
    delay: float | None = None,
) -> tuple[int, int, int]:
    """
    Разослать текст всем пользователям. Задержка между отправками.
    Обрабатывает TelegramForbiddenError (blocked), TelegramNotFound, TelegramBadRequest — не останавливает цикл.
    Возвращает (total, success_count, error_count).
    """
    config = Config.from_env()
    if delay is None:
        delay = config.BROADCAST_DELAY
    success = 0
    errors = 0
    async with session_factory() as session:
        telegram_ids = await get_all_users_for_broadcast(session)
    total = len(telegram_ids)
    for telegram_id in telegram_ids:
        try:
            await bot.send_message(chat_id=telegram_id, text=text)
            success += 1
        except (TelegramForbiddenError, TelegramNotFound) as e:
            errors += 1
            logger.warning(
                "Broadcast skip user %s: %s",
                telegram_id,
                type(e).__name__,
            )
        except TelegramBadRequest as e:
            errors += 1
            logger.warning(
                "Broadcast TelegramBadRequest user %s: %s",
                telegram_id,
                str(e)[:100],
            )
        except Exception as e:
            errors += 1
            logger.error("Broadcast error user %s: %s", telegram_id, e)
        await asyncio.sleep(delay)
    return total, success, errors
