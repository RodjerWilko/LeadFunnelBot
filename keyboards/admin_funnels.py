# keyboards/admin_funnels.py — клавиатуры админки воронок
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админки: Воронки, Назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Воронки", callback_data="admin:funnels")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")],
    ])


def admin_segments_list_keyboard(
    segments: list[tuple[int, str, bool]]
) -> InlineKeyboardMarkup:
    """Список сегментов для админки. segments: (id, name, is_active)."""
    rows = []
    for seg_id, name, is_active in segments:
        status = "✅" if is_active else "❌"
        rows.append([
            InlineKeyboardButton(
                text=f"{status} {name}",
                callback_data=f"admin:seg:{seg_id}",
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_segment_screen_keyboard(segment_id: int) -> InlineKeyboardMarkup:
    """Экран сегмента: Шаги, Вкл/Выкл, Назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Шаги", callback_data=f"admin:steps:{segment_id}")],
        [InlineKeyboardButton(text="🔁 Вкл/Выкл", callback_data=f"admin:toggle:{segment_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:funnels")],
    ])


def admin_steps_list_keyboard(
    segment_id: int,
    steps: list[tuple[int, int, int]],
) -> InlineKeyboardMarkup:
    """Список шагов. steps: (step_id, step_number, delay_hours)."""
    rows = []
    for step_id, step_number, delay_hours in steps:
        rows.append([
            InlineKeyboardButton(
                text=f"Шаг {step_number} (через {delay_hours} ч)",
                callback_data=f"admin:step:{step_id}",
            )
        ])
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:seg:{segment_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_step_detail_keyboard(step_id: int, segment_id: int) -> InlineKeyboardMarkup:
    """Детали шага: Редактировать, Назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin:edit:{step_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:steps:{segment_id}")],
    ])
