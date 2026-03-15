# services/admin_service.py — проверка прав админа
from __future__ import annotations


def is_admin(telegram_id: int, admin_id: int) -> bool:
    """Проверка: пользователь с telegram_id является админом."""
    return admin_id != 0 and telegram_id == admin_id
