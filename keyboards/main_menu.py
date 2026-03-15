# keyboards/main_menu.py — стартовый экран (если нужен отдельно)
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.segments import segments_keyboard


def start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура стартового экрана: выбор сегмента (делегируем segments)."""
    return segments_keyboard()
