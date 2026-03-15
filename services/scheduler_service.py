# services/scheduler_service.py — планирование шагов воронки
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None
_bot: Any = None
_session_factory: Any = None
_loop: asyncio.AbstractEventLoop | None = None


def create_scheduler(
    bot: Any,
    config: Config,
    session_factory: Any,
    loop: asyncio.AbstractEventLoop,
) -> AsyncIOScheduler:
    """Создать и вернуть scheduler. Сохранить ссылки для job'ов."""
    global _scheduler, _bot, _session_factory, _loop
    _scheduler = AsyncIOScheduler()
    _bot = bot
    _session_factory = session_factory
    _loop = loop
    return _scheduler


def schedule_funnel_steps(
    telegram_id: int,
    user_id: int,
    funnel_id: int,
    steps_to_schedule: list[tuple[int, int]],  # (step_id, delay_hours)
) -> None:
    """
    Запланировать отправку шагов воронки.
    steps_to_schedule: список (step_id, delay_hours).
    Job id: funnel_step_{user_id}_{step_id}.
    """
    if _scheduler is None or _bot is None or _session_factory is None or _loop is None:
        logger.warning("Scheduler или зависимости не инициализированы")
        return

    for step_id, delay_hours in steps_to_schedule:
        job_id = f"funnel_step_{user_id}_{step_id}"
        try:
            existing = _scheduler.get_job(job_id)
            if existing is not None:
                logger.info("Scheduler: job уже существует, пропуск: %s", job_id)
                continue
            run_date = datetime.utcnow() + timedelta(hours=delay_hours)
            _scheduler.add_job(
                _run_send_step,
                trigger="date",
                run_date=run_date,
                id=job_id,
                kwargs={
                    "telegram_id": telegram_id,
                    "step_id": step_id,
                },
                replace_existing=True,
            )
            logger.info("Scheduled job: %s", job_id)
        except Exception as e:
            logger.error("Scheduler job failed: %s, error: %s", job_id, e)


def cancel_user_funnel_jobs(user_id: int) -> None:
    """
    Отменить все запланированные шаги воронки для пользователя.
    Job id вида: funnel_step_{user_id}_{step_id}.
    """
    if _scheduler is None:
        return
    try:
        jobs = _scheduler.get_jobs()
        for job in jobs:
            if job.id and job.id.startswith(f"funnel_step_{user_id}_"):
                job.remove()
                logger.info("Удалён job воронки: %s", job.id)
    except Exception as e:
        logger.exception("Ошибка отмены job'ов пользователя %s: %s", user_id, e)


async def send_scheduled_funnel_step(
    telegram_id: int, step_id: int, session_factory: Any, bot: Any
) -> None:
    """
    Отправить один запланированный шаг воронки пользователю.
    Вызывается из job'а через run_coroutine_threadsafe.
    """
    from sqlalchemy import select
    from models.funnel_step import FunnelStep
    from keyboards.funnel import funnel_step_keyboard

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(FunnelStep).where(FunnelStep.id == step_id)
            )
            step = result.scalar_one_or_none()
            if step is None:
                logger.warning("Шаг воронки %s не найден", step_id)
                return
            text = step.message_text
            kb = funnel_step_keyboard()
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    reply_markup=kb,
                )
            except Exception as e:
                logger.error(
                    "Отправка шага %s пользователю %s: %s",
                    step_id,
                    telegram_id,
                    e,
                )
    except Exception as e:
        logger.error("send_scheduled_funnel_step: %s", e)


def _run_send_step(telegram_id: int, step_id: int) -> None:
    """Синхронная обёртка для вызова async send из job'а (другой поток)."""
    if _bot is None or _session_factory is None or _loop is None:
        return
    try:
        coro = send_scheduled_funnel_step(
            telegram_id, step_id, _session_factory, _bot
        )
        asyncio.run_coroutine_threadsafe(coro, _loop)
    except Exception as e:
        logger.exception("_run_send_step: %s", e)
