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
    Показать запланированный шаг воронки в основном UI-сообщении пользователя.
    Редактирует сохранённое сообщение; при неудаче — отправляет новое и обновляет user.
    """
    from sqlalchemy import select
    from models.funnel_step import FunnelStep
    from models.user import User
    from keyboards.funnel import funnel_step_keyboard
    from services.ui_service import safe_edit_or_resend, save_user_ui_message

    try:
        async with session_factory() as session:
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                logger.warning("Scheduled step: user telegram_id=%s not found", telegram_id)
                return

            result = await session.execute(
                select(FunnelStep).where(FunnelStep.id == step_id)
            )
            step = result.scalar_one_or_none()
            if step is None:
                logger.warning("Шаг воронки %s не найден", step_id)
                return
            text = step.message_text
            kb = funnel_step_keyboard()

            chat_id = user.chat_id
            message_id = user.ui_message_id

            if chat_id is not None and message_id is not None:
                success, new_id = await safe_edit_or_resend(
                    bot, chat_id, message_id, text, kb
                )
                if success:
                    if new_id is not None:
                        await save_user_ui_message(
                            session, user.id, chat_id, new_id
                        )
                        logger.info(
                            "Scheduled funnel step fallback resend, ui_message_id updated: "
                            "user_id=%s step_id=%s",
                            user.id,
                            step_id,
                        )
                    else:
                        logger.info(
                            "Scheduled funnel step edit success: user_id=%s step_id=%s",
                            user.id,
                            step_id,
                        )
                    return
                logger.warning(
                    "Scheduled step edit failed, will try send: user_id=%s step_id=%s",
                    user.id,
                    step_id,
                )

            try:
                sent = await bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                    reply_markup=kb,
                )
                await save_user_ui_message(
                    session, user.id, sent.chat.id, sent.message_id
                )
                logger.info(
                    "Scheduled funnel step rendered (new message): user_id=%s step_id=%s",
                    user.id,
                    step_id,
                )
            except Exception as e:
                logger.error(
                    "Scheduler step failed: user_id=%s step_id=%s: %s",
                    user.id,
                    step_id,
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
