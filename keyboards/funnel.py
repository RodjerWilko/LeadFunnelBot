# keyboards/funnel.py — кнопки шага воронки
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def funnel_step_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура шага воронки: заявка, сменить направление (без дубля «Назад»)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Оставить заявку", callback_data="lead:create")],
        [InlineKeyboardButton(text="🔄 Сменить направление", callback_data="nav:segments")],
    ])


