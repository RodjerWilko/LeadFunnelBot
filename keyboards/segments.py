# keyboards/segments.py — выбор сегмента
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def segments_keyboard(segments: list[tuple[int, str]] | None = None) -> InlineKeyboardMarkup:
    """
    Inline-клавиатура выбора сегмента.
    segments: список (id, name). Если None — кнопки по умолчанию (Маркетинг, Telegram-боты, AI).
    """
    if segments is None:
        segments = [
            (1, "Маркетинг"),
            (2, "Telegram-боты"),
            (3, "AI"),
        ]
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"segment:{seg_id}")]
        for seg_id, name in segments
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
