# config/config.py — настройки из .env
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Конфигурация приложения. Загрузка из переменных окружения."""

    BOT_TOKEN: str
    DATABASE_URL: str
    ADMIN_ID: int
    RATE_LIMIT_MESSAGES: int = 5
    RATE_LIMIT_PERIOD: int = 2
    BROADCAST_DELAY: float = 0.05

    @classmethod
    def from_env(cls) -> Config:
        token = os.getenv("BOT_TOKEN", "")
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:password@localhost:5432/leadfunnel",
        )
        admin_id = int(os.getenv("ADMIN_ID", "0"))
        rate_messages = int(os.getenv("RATE_LIMIT_MESSAGES", "5"))
        rate_period = int(os.getenv("RATE_LIMIT_PERIOD", "2"))
        broadcast_delay = float(os.getenv("BROADCAST_DELAY", "0.05"))
        return cls(
            BOT_TOKEN=token,
            DATABASE_URL=db_url,
            ADMIN_ID=admin_id,
            RATE_LIMIT_MESSAGES=rate_messages,
            RATE_LIMIT_PERIOD=rate_period,
            BROADCAST_DELAY=broadcast_delay,
        )
