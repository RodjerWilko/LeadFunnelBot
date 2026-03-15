# keyboards/funnel.py — кнопки шага воронки
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def funnel_step_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура под сообщением воронки: заявка, сменить направление, назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Оставить заявку", callback_data="lead:create")],
        [InlineKeyboardButton(text="🔄 Сменить направление", callback_data="nav:segments")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:segments")],
    ])


def segment_confirm_keyboard() -> InlineKeyboardMarkup:
    """После выбора сегмента: только назад к сегментам (первый шаг показываем отдельно)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:segments")],
    ])
