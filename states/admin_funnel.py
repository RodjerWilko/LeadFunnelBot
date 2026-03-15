# states/admin_funnel.py — FSM редактирования шага воронки
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminEditStepStates(StatesGroup):
    """Состояния редактирования текста шага воронки."""

    waiting_text = State()
