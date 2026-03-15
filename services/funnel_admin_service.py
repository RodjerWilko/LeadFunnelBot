# services/funnel_admin_service.py — админское управление воронками и шагами
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.funnel import Funnel
from models.funnel_step import FunnelStep


async def get_funnel_steps_with_preview(
    session: AsyncSession, funnel_id: int, preview_len: int = 60
) -> list[tuple[FunnelStep, str]]:
    """
    Получить шаги воронки с обрезанным текстом для списка.
    Возвращает список (step, preview_text).
    """
    result = await session.execute(
        select(FunnelStep)
        .where(FunnelStep.funnel_id == funnel_id)
        .order_by(FunnelStep.step_number)
    )
    steps = list(result.scalars().all())
    out = []
    for step in steps:
        text = step.message_text or ""
        if len(text) > preview_len:
            preview = text[:preview_len].rstrip() + "…"
        else:
            preview = text or "—"
        out.append((step, preview))
    return out


async def get_funnel_step_by_id(
    session: AsyncSession, step_id: int
) -> FunnelStep | None:
    """Получить шаг воронки по id (с загрузкой funnel для segment_id)."""
    result = await session.execute(
        select(FunnelStep)
        .options(selectinload(FunnelStep.funnel))
        .where(FunnelStep.id == step_id)
    )
    return result.scalar_one_or_none()


async def update_funnel_step_text(
    session: AsyncSession, step_id: int, new_text: str
) -> bool:
    """Обновить текст шага воронки в БД."""
    step = await get_funnel_step_by_id(session, step_id)
    if step is None:
        return False
    step.message_text = new_text.strip()
    await session.commit()
    return True
