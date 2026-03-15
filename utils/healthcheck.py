# utils/healthcheck.py — проверка состояния системы
from __future__ import annotations

from typing import Any

from sqlalchemy import text


async def check_database(session_factory: Any) -> str:
    """Проверка БД: простой SELECT 1."""
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "fail"


def check_scheduler(scheduler: Any) -> str:
    """Проверка scheduler: running и количество job'ов."""
    if scheduler is None:
        return "fail"
    try:
        if not scheduler.running:
            return "fail"
        jobs = scheduler.get_jobs()
        return "ok"
    except Exception:
        return "fail"


async def check_bot(bot: Any) -> str:
    """Проверка Bot API: get_me()."""
    try:
        await bot.get_me()
        return "ok"
    except Exception:
        return "fail"


async def run_healthcheck(
    session_factory: Any,
    bot: Any,
    scheduler: Any = None,
) -> dict[str, str]:
    """
    Запуск всех проверок. Возвращает dict:
    { "database": "ok"|"fail", "scheduler": "ok"|"fail", "bot": "ok"|"fail" }
    """
    db_status = await check_database(session_factory)
    sched_status = check_scheduler(scheduler)
    bot_status = await check_bot(bot)
    return {
        "database": db_status,
        "scheduler": sched_status,
        "bot": bot_status,
    }
