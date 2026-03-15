# healthcheck_script.py — скрипт для Docker HEALTHCHECK (проверка БД и Bot API)
"""Запуск: python healthcheck_script.py. Exit 0 — всё ок, иначе 1."""
from __future__ import annotations

import asyncio
import sys

from aiogram import Bot
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.config import Config
from utils.healthcheck import run_healthcheck


def main() -> None:
    try:
        config = Config.from_env()
    except Exception:
        sys.exit(1)
    if not config.BOT_TOKEN or not config.DATABASE_URL:
        sys.exit(1)

    async def _run() -> int:
        engine = create_async_engine(config.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        bot = Bot(token=config.BOT_TOKEN)
        try:
            result = await run_healthcheck(session_factory, bot, scheduler=None)
        finally:
            await bot.session.close()
            await engine.dispose()
        if result["database"] == "ok" and result["bot"] == "ok":
            return 0
        return 1

    exit_code = asyncio.run(_run())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
