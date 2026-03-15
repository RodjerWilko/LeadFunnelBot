# keyboards/back.py — универсальная кнопка «Назад»
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def back_to_segments_keyboard() -> InlineKeyboardMarkup:
    """Кнопка «Назад» к выбору сегментов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:segments")],
    ])
