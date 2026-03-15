# services/ui_service.py — единое UI-сообщение пользователя (Single-Message UI)
from __future__ import annotations

from typing import Any

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
)
from aiogram.types import InlineKeyboardMarkup

from models.user import User
from services.user_service import update_user_ui_context
from utils.logger import get_logger

logger = get_logger(__name__)


def get_user_ui_message(user: User) -> tuple[int | None, int | None]:
    """Вернуть (chat_id, ui_message_id) основного сообщения пользователя."""
    return (user.chat_id, user.ui_message_id)


async def save_user_ui_message(
    session: Any,
    user_id: int,
    chat_id: int,
    ui_message_id: int,
) -> bool:
    """Сохранить chat_id и ui_message_id как основной экран пользователя."""
    ok = await update_user_ui_context(session, user_id, chat_id, ui_message_id)
    if ok:
        logger.info("User UI context updated: user_id=%s chat_id=%s message_id=%s", user_id, chat_id, ui_message_id)
    return ok


async def safe_edit_or_resend(
    bot: Any,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> tuple[bool, int | None]:
    """
    Редактировать сообщение или отправить новое при ошибке.
    Возвращает (успех, new_message_id или None если edit успешен).
    """
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        logger.info("UI message edited: chat_id=%s message_id=%s", chat_id, message_id)
        return (True, None)
    except TelegramBadRequest as e:
        msg = (e.message or str(e)).lower()
        if "message is not modified" in msg or "message to edit not found" in msg:
            logger.debug("Edit not possible (not modified or not found): %s", msg[:80])
        else:
            logger.warning("UI edit TelegramBadRequest: %s", msg[:100])
    except (TelegramForbiddenError, TelegramNotFound) as e:
        logger.warning("UI edit forbidden/not found: %s", type(e).__name__)
    except Exception as e:
        logger.error("UI edit error: %s", e)

    try:
        sent = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )
        logger.info("UI message fallback resend: chat_id=%s new_message_id=%s", chat_id, sent.message_id)
        return (True, sent.message_id)
    except (TelegramForbiddenError, TelegramNotFound) as e:
        logger.warning("UI resend failed (blocked/not found): %s", type(e).__name__)
        return (False, None)
    except Exception as e:
        logger.error("UI resend error: %s", e)
        return (False, None)


async def send_or_update_ui_message(
    bot: Any,
    session: Any,
    user: User,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """
    Показать контент в основном UI-сообщении пользователя.
    Если ui_message_id нет — отправить новое и сохранить.
    Иначе — edit; при неудаче — отправить новое и обновить.
    """
    chat_id = user.chat_id
    message_id = user.ui_message_id

    if chat_id is None or message_id is None:
        try:
            sent = await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=reply_markup,
            )
            chat_id = sent.chat.id
            message_id = sent.message_id
            await save_user_ui_message(session, user.id, chat_id, message_id)
            logger.info("UI message created: user_id=%s message_id=%s", user.id, message_id)
            return True
        except Exception as e:
            logger.error("UI message create failed: %s", e)
            return False

    success, new_id = await safe_edit_or_resend(
        bot, chat_id, message_id, text, reply_markup
    )
    if success and new_id is not None:
        await save_user_ui_message(session, user.id, chat_id, new_id)
        logger.info("UI message fallback resend, user context updated: user_id=%s", user.id)
    return success
