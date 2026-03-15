# utils/exceptions.py — собственные исключения при необходимости
from __future__ import annotations


class LeadFunnelError(Exception):
    """Базовое исключение приложения."""

    pass


class SendMessageError(LeadFunnelError):
    """Ошибка отправки сообщения в Telegram."""

    pass
