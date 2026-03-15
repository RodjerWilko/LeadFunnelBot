# handlers/admin.py — админ-панель: /admin, управление воронками
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config.config import Config
from keyboards.admin_funnels import (
    admin_menu_keyboard,
    admin_segment_screen_keyboard,
    admin_segments_list_keyboard,
    admin_step_detail_keyboard,
    admin_steps_list_keyboard,
)
from services.admin_service import is_admin
from services.funnel_service import get_funnel_by_segment_id, get_funnel_steps
from services.funnel_admin_service import (
    get_funnel_steps_with_preview,
    get_funnel_step_by_id,
    update_funnel_step_text,
)
from services.segment_admin_service import (
    get_all_segments,
    get_segment_by_id_for_admin,
    toggle_segment_active,
)
from states.admin_funnel import AdminEditStepStates
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()
_config = Config.from_env()

ADMIN_DENIED = "⛔ У вас нет доступа к этому разделу."
ADMIN_MENU_TEXT = "🛠 Админ-панель\n\nВыберите действие 👇"
STEP_EDIT_PROMPT = "✏️ Введите новый текст шага (одним сообщением):"
STEP_SAVED = "✅ Текст шага обновлён."
ERROR_MSG = "⚠️ Произошла ошибка. Попробуйте ещё раз."


def _admin_only(callback: CallbackQuery) -> bool:
    if not callback.from_user:
        return False
    return is_admin(callback.from_user.id, _config.ADMIN_ID)


@router.message(Command("health"))
async def cmd_health(
    message: Message,
    session_factory,
    scheduler,
) -> None:
    """Команда /health: только для ADMIN_ID. Показывает состояние системы."""
    if not message.from_user:
        return
    if not is_admin(message.from_user.id, _config.ADMIN_ID):
        try:
            await message.answer(ADMIN_DENIED)
        except Exception:
            pass
        return
    try:
        from utils.healthcheck import run_healthcheck

        status = await run_healthcheck(session_factory, message.bot, scheduler)
        db = "OK" if status.get("database") == "ok" else "FAIL"
        sched = "OK" if status.get("scheduler") == "ok" else "FAIL"
        bot_api = "OK" if status.get("bot") == "ok" else "FAIL"
        text = (
            "🩺 <b>System health</b>\n\n"
            f"Database: {db}\n"
            f"Scheduler: {sched}\n"
            f"Bot API: {bot_api}"
        )
        await message.answer(text)
    except Exception as e:
        logger.exception("Ошибка /health: %s", e)
        try:
            await message.answer(ERROR_MSG)
        except Exception:
            pass


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Команда /admin: только для ADMIN_ID."""
    if not message.from_user:
        return
    if not is_admin(message.from_user.id, _config.ADMIN_ID):
        try:
            await message.answer(ADMIN_DENIED)
        except Exception as e:
            logger.debug("admin deny answer: %s", e)
        return
    logger.info("Админ вошёл в панель: %s", message.from_user.id)
    try:
        await message.answer(ADMIN_MENU_TEXT, reply_markup=admin_menu_keyboard())
    except Exception as e:
        logger.exception("Ошибка отправки админ-меню: %s", e)
        try:
            await message.answer(ERROR_MSG)
        except Exception:
            pass


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery) -> None:
    """Возврат в главное меню админки."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        await callback.message.edit_text(
            ADMIN_MENU_TEXT,
            reply_markup=admin_menu_keyboard(),
        )
        await callback.answer()
    except Exception as e:
        logger.debug("edit_text admin:back: %s", e)
        try:
            await callback.message.answer(ADMIN_MENU_TEXT, reply_markup=admin_menu_keyboard())
        except Exception:
            pass
        await callback.answer()


@router.callback_query(F.data == "admin:funnels")
async def admin_funnels(callback: CallbackQuery, session) -> None:
    """Список сегментов (воронок)."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        segments = await get_all_segments(session)
        if not segments:
            text = "📋 Воронки\n\nНет сегментов."
            kb = admin_menu_keyboard()
        else:
            data = [(s.id, s.name, s.is_active) for s in segments]
            text = "📋 Воронки\n\nВыберите сегмент:"
            kb = admin_segments_list_keyboard(data)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("admin_funnels: %s", e)
        await callback.answer(ERROR_MSG, show_alert=True)


@router.callback_query(F.data.startswith("admin:seg:"))
async def admin_segment_screen(callback: CallbackQuery, session) -> None:
    """Экран сегмента: название, статус, кнопки."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        segment_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer(ERROR_MSG, show_alert=True)
        return
    try:
        segment = await get_segment_by_id_for_admin(session, segment_id)
        if not segment:
            await callback.answer("Сегмент не найден.", show_alert=True)
            return
        status = "активен" if segment.is_active else "выключен"
        text = (
            f"⚙️ Сегмент: <b>{segment.name}</b>\n\n"
            f"Статус: {status}"
        )
        kb = admin_segment_screen_keyboard(segment_id)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("admin_segment_screen: %s", e)
        await callback.answer(ERROR_MSG, show_alert=True)


@router.callback_query(F.data.startswith("admin:toggle:"))
async def admin_toggle_segment(callback: CallbackQuery, session) -> None:
    """Вкл/Выкл сегмента."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        segment_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer(ERROR_MSG, show_alert=True)
        return
    try:
        new_active = await toggle_segment_active(session, segment_id)
        segment = await get_segment_by_id_for_admin(session, segment_id)
        if not segment:
            await callback.answer(ERROR_MSG, show_alert=True)
            return
        status = "активен" if segment.is_active else "выключен"
        text = (
            f"⚙️ Сегмент: <b>{segment.name}</b>\n\n"
            f"Статус: {status}"
        )
        kb = admin_segment_screen_keyboard(segment_id)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
        await callback.answer("Статус обновлён")
    except Exception as e:
        logger.exception("admin_toggle_segment: %s", e)
        await callback.answer(ERROR_MSG, show_alert=True)


@router.callback_query(F.data.startswith("admin:steps:"))
async def admin_steps_list(callback: CallbackQuery, session) -> None:
    """Список шагов воронки сегмента."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        segment_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer(ERROR_MSG, show_alert=True)
        return
    try:
        segment = await get_segment_by_id_for_admin(session, segment_id)
        if not segment:
            await callback.answer("Сегмент не найден.", show_alert=True)
            return
        funnel = await get_funnel_by_segment_id(session, segment_id)
        if not funnel:
            text = f"📋 Шаги: {segment.name}\n\nВоронка не найдена."
            kb = admin_segment_screen_keyboard(segment_id)
            try:
                await callback.message.edit_text(text, reply_markup=kb)
            except Exception:
                await callback.message.answer(text, reply_markup=kb)
            await callback.answer()
            return
        steps_with_preview = await get_funnel_steps_with_preview(
            session, funnel.id, preview_len=50
        )
        if not steps_with_preview:
            text = f"📋 Шаги: {segment.name}\n\nНет шагов."
            kb = admin_segment_screen_keyboard(segment_id)
        else:
            lines = [f"📋 Шаги воронки: <b>{segment.name}</b>\n"]
            step_ids_for_kb = [
                (step.id, step.step_number, step.delay_hours)
                for step, _ in steps_with_preview
            ]
            for step, preview in steps_with_preview:
                lines.append(
                    f"• Шаг {step.step_number} ({step.delay_hours} ч): {preview}"
                )
            text = "\n".join(lines)[:4000]
            kb = admin_steps_list_keyboard(segment_id, step_ids_for_kb)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("admin_steps_list: %s", e)
        await callback.answer(ERROR_MSG, show_alert=True)


@router.callback_query(F.data.startswith("admin:step:"))
async def admin_step_detail(callback: CallbackQuery, session) -> None:
    """Детали шага: полный текст, кнопка Редактировать."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        step_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer(ERROR_MSG, show_alert=True)
        return
    try:
        step = await get_funnel_step_by_id(session, step_id)
        if not step:
            await callback.answer("Шаг не найден.", show_alert=True)
            return
        funnel = await get_funnel_by_segment_id(session, step.funnel.segment_id)
        segment_id = step.funnel.segment_id if funnel else 0
        text = (
            f"📌 Шаг {step.step_number}\n"
            f"⏱ Через {step.delay_hours} ч\n\n"
            f"{step.message_text}"
        )[:4000]
        kb = admin_step_detail_keyboard(step_id, segment_id)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.exception("admin_step_detail: %s", e)
        await callback.answer(ERROR_MSG, show_alert=True)


@router.callback_query(F.data.startswith("admin:edit:"))
async def admin_step_edit_start(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Начало редактирования шага: FSM ожидания текста."""
    if not _admin_only(callback):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    try:
        step_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer(ERROR_MSG, show_alert=True)
        return
    await state.set_state(AdminEditStepStates.waiting_text)
    await state.update_data(admin_edit_step_id=step_id)
    try:
        await callback.message.edit_text(STEP_EDIT_PROMPT)
    except Exception:
        await callback.message.answer(STEP_EDIT_PROMPT)
    await callback.answer()


@router.message(AdminEditStepStates.waiting_text, F.text)
async def admin_step_edit_save(message: Message, state: FSMContext, session) -> None:
    """Сохранение нового текста шага."""
    if not message.from_user or not is_admin(message.from_user.id, _config.ADMIN_ID):
        await state.clear()
        return
    data = await state.get_data()
    step_id = data.get("admin_edit_step_id")
    if not step_id:
        await state.clear()
        try:
            await message.answer(ERROR_MSG)
        except Exception:
            pass
        return
    text = (message.text or "").strip()
    if not text:
        try:
            await message.answer("Введите непустой текст.")
        except Exception:
            pass
        return
    try:
        ok = await update_funnel_step_text(session, step_id, text)
        await state.clear()
        if ok:
            try:
                await message.answer(STEP_SAVED)
            except Exception:
                pass
        else:
            try:
                await message.answer(ERROR_MSG)
            except Exception:
                pass
    except Exception as e:
        logger.exception("admin_step_edit_save: %s", e)
        await state.clear()
        try:
            await message.answer(ERROR_MSG)
        except Exception:
            pass
