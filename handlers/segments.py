# handlers/segments.py — выбор сегмента, первый шаг воронки, планирование
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
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("segment:"))
async def on_segment_chosen(callback: CallbackQuery, session) -> None:
    """
    Выбор сегмента: сохранить segment_id, показать подтверждение,
    отправить первый шаг воронки, запланировать остальные.
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

        # Отменить старые запланированные шаги воронки при смене направления
        cancel_user_funnel_jobs(user.id)

        funnel = await get_funnel_by_segment_id(session, segment_id)
        if not funnel:
            await callback.answer("Воронка не найдена.", show_alert=True)
            return

        steps = await get_funnel_steps(session, funnel.id)
        if not steps:
            await callback.answer("Нет шагов воронки.", show_alert=True)
            return

        # Подтверждение выбора — редактируем сообщение
        confirm_text = (
            f"✅ Вы выбрали: <b>{segment.name}</b>\n\n"
            "Ниже — первое сообщение воронки. Следующие придут по расписанию."
        )
        try:
            await callback.message.edit_text(
                confirm_text,
                reply_markup=funnel_step_keyboard(),
            )
        except Exception as e:
            logger.debug("edit_text в segments: %s", e)
            try:
                await callback.message.answer(
                    confirm_text,
                    reply_markup=funnel_step_keyboard(),
                )
            except Exception:
                pass

        # Первый шаг (delay_hours = 0) — отправляем сразу новым сообщением
        step1 = steps[0]
        first_text = step1.message_text
        try:
            await callback.message.answer(
                first_text,
                reply_markup=funnel_step_keyboard(),
            )
        except Exception as e:
            logger.exception("Отправка первого шага: %s", e)

        # Шаги 2 и 3 — планируем
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
