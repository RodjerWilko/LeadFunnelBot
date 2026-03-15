# handlers/segments.py — выбор сегмента → тот же экран превращается в шаг 1 (Single-Message UI)
from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from keyboards.funnel import funnel_step_keyboard
from services.user_service import get_or_create_user, update_user_segment
from services.funnel_service import (
    get_funnel_by_segment_id,
    get_funnel_steps,
    get_segment_by_id,
)
from services.scheduler_service import schedule_funnel_steps, cancel_user_funnel_jobs
from services.ui_service import safe_edit_or_resend, save_user_ui_message
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()
segments_router = router


@router.callback_query(lambda c: c.data and c.data.startswith("segment:"))
async def on_segment_chosen(callback: CallbackQuery, session) -> None:
    """
    Выбор сегмента: сохраняем segment_id, то же сообщение сразу — первый шаг воронки.
    Без промежуточного «Вы выбрали» и без второго нового сообщения.
    """
    if not callback.data or not callback.from_user:
        return
    try:
        segment_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка выбора.")
        return

    try:
        segment = await get_segment_by_id(session, segment_id)
        if not segment:
            await callback.answer("Сегмент не найден.", show_alert=True)
            return
        if not segment.is_active:
            await callback.answer("Это направление временно недоступно.", show_alert=True)
            return

        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        await update_user_segment(session, user.id, segment_id)
        cancel_user_funnel_jobs(user.id)

        funnel = await get_funnel_by_segment_id(session, segment_id)
        if not funnel:
            await callback.answer("Воронка не найдена.", show_alert=True)
            return

        steps = await get_funnel_steps(session, funnel.id)
        if not steps:
            await callback.answer("Нет шагов воронки.", show_alert=True)
            return

        step1 = steps[0]
        first_text = (
            f"✅ Направление: <b>{segment.name}</b>\n\n"
            f"{step1.message_text}"
        )
        kb = funnel_step_keyboard()
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id

        success, new_id = await safe_edit_or_resend(
            callback.bot, chat_id, message_id, first_text, kb
        )
        if success and new_id is not None:
            await save_user_ui_message(session, user.id, chat_id, new_id)
        else:
            await save_user_ui_message(session, user.id, chat_id, message_id)

        logger.info(
            "Segment changed with single-message flow: user_id=%s segment=%s",
            user.id,
            segment.name,
        )

        to_schedule = [
            (s.id, s.delay_hours)
            for s in steps
            if s.delay_hours > 0
        ]
        if to_schedule:
            schedule_funnel_steps(
                telegram_id=callback.from_user.id,
                user_id=user.id,
                funnel_id=funnel.id,
                steps_to_schedule=to_schedule,
            )

        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка в on_segment_chosen: %s", e)
        try:
            await callback.answer(
                "⚠️ Произошла ошибка. Попробуйте ещё раз.",
                show_alert=True,
            )
        except Exception:
            pass
