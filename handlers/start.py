# handlers/start.py — /start и стартовый экран (Single-Message UI)
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.segments import segments_keyboard
from services.user_service import get_or_create_user
from services.funnel_service import get_active_segments
from services.ui_service import save_user_ui_message
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()
start_router = router

START_TEXT = (
    "👋 Добро пожаловать!\n\n"
    "Этот бот показывает, как работает автоворонка продаж в Telegram.\n\n"
    "Выберите интересующее направление 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session) -> None:
    """Обработка /start: один экран — одно сообщение, сохраняем как главное UI."""
    if not message.from_user:
        return
    logger.info("Received /start from user_id=%s", message.from_user.id)
    try:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        segments = await get_active_segments(session)
        if not segments:
            await message.answer(
                "⚠️ Сегменты не настроены. Обратитесь к администратору."
            )
            return
        kb = segments_keyboard([(s.id, s.name) for s in segments])
        sent = await message.answer(START_TEXT, reply_markup=kb)
        await save_user_ui_message(
            session, user.id, sent.chat.id, sent.message_id
        )
        logger.info("UI message created: user_id=%s message_id=%s", user.id, sent.message_id)
    except Exception as e:
        logger.exception("Ошибка в /start: %s", e)
        try:
            await message.answer(
                "⚠️ Произошла ошибка. Попробуйте ещё раз."
            )
        except Exception:
            pass
