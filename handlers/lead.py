# handlers/lead.py — заявка: FSM ввод текста, сохранение, уведомление админу
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config.config import Config
from keyboards.funnel import funnel_step_keyboard
from services.user_service import get_user_by_telegram_id
from services.lead_service import create_lead
from services.funnel_service import get_segment_by_id
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router()
lead_router = router


class LeadStates(StatesGroup):
    waiting_message = State()


LEAD_PROMPT = "📩 Напишите текст заявки (одним сообщением):"
LEAD_CONFIRM = "✅ Заявка отправлена. Мы скоро свяжемся с вами."
LEAD_ERROR = "⚠️ Произошла ошибка. Попробуйте ещё раз."


def _format_lead_for_admin(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    segment_name: str | None,
    message: str,
    created_at: str,
) -> str:
    """Форматирование сообщения админу о новом лиде."""
    return (
        "🆕 <b>Новая заявка</b>\n\n"
        f"<b>Telegram ID:</b> {telegram_id}\n"
        f"<b>Username:</b> @{username or '—'}\n"
        f"<b>Имя:</b> {first_name or '—'}\n"
        f"<b>Сегмент:</b> {segment_name or '—'}\n"
        f"<b>Текст заявки:</b>\n{message}\n\n"
        f"<b>Дата:</b> {created_at}"
    )


@router.callback_query(lambda c: c.data == "lead:create")
async def lead_create_start(
    callback: CallbackQuery, state: FSMContext, session
) -> None:
    """Нажатие «Оставить заявку»: переводим в FSM ожидания текста."""
    try:
        await state.set_state(LeadStates.waiting_message)
        try:
            await callback.message.edit_text(LEAD_PROMPT)
        except Exception:
            await callback.message.answer(LEAD_PROMPT)
        await callback.answer()
    except Exception as e:
        logger.exception("lead_create_start: %s", e)
        try:
            await callback.answer(LEAD_ERROR, show_alert=True)
        except Exception:
            pass


@router.message(LeadStates.waiting_message, F.text)
async def lead_receive_message(
    message: Message, state: FSMContext, session
) -> None:
    """Получение текста заявки: сохранить лид, уведомить админа, подтвердить пользователю."""
    if not message.text or not message.from_user:
        return
    text = message.text.strip()
    if not text:
        return

    try:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(LEAD_ERROR)
            await state.clear()
            return

        lead = await create_lead(session, user.id, text)
        created_at = lead.created_at.strftime("%d.%m.%Y %H:%M")
        segment_name = None
        if user.segment_id:
            seg = await get_segment_by_id(session, user.segment_id)
            segment_name = seg.name if seg else None

        # Уведомление админу
        config = Config.from_env()
        if config.ADMIN_ID:
            admin_text = _format_lead_for_admin(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                segment_name=segment_name,
                message=text,
                created_at=created_at,
            )
            try:
                await message.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text=admin_text,
                )
            except Exception as e:
                logger.exception("Отправка заявки админу: %s", e)

        await state.clear()
        await message.answer(LEAD_CONFIRM, reply_markup=funnel_step_keyboard())
    except Exception as e:
        logger.exception("lead_receive_message: %s", e)
        try:
            await message.answer(LEAD_ERROR)
        except Exception:
            pass
        await state.clear()


@router.message(LeadStates.waiting_message)
async def lead_wrong_content(message: Message) -> None:
    """Не текст в состоянии заявки — подсказка."""
    await message.answer("Пожалуйста, отправьте текст сообщением.")
