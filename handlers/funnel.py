# handlers/funnel.py — навигация: назад к сегментам
from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from keyboards.segments import segments_keyboard
from services.funnel_service import get_active_segments
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()
funnel_router = router

NAV_SEGMENTS_TEXT = (
    "👋 Выберите интересующее направление 👇"
)


@router.callback_query(lambda c: c.data == "nav:segments")
async def nav_to_segments(callback: CallbackQuery, session) -> None:
    """Возврат к выбору сегментов (single-message: edit_text)."""
    try:
        segments = await get_active_segments(session)
        if not segments:
            await callback.answer("Нет доступных сегментов.", show_alert=True)
            return
        kb = segments_keyboard([(s.id, s.name) for s in segments])
        try:
            await callback.message.edit_text(
                NAV_SEGMENTS_TEXT,
                reply_markup=kb,
            )
        except Exception as e:
            logger.debug("edit_text nav:segments: %s", e)
            try:
                await callback.message.answer(
                    NAV_SEGMENTS_TEXT,
                    reply_markup=kb,
                )
            except Exception:
                pass
        await callback.answer()
    except Exception as e:
        logger.exception("nav_to_segments: %s", e)
        try:
            await callback.answer(
                "⚠️ Произошла ошибка. Попробуйте ещё раз.",
                show_alert=True,
            )
        except Exception:
            pass
