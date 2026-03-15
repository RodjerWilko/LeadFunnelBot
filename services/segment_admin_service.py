# services/segment_admin_service.py — админское управление сегментами
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.segment import Segment


async def get_all_segments(session: AsyncSession) -> list[Segment]:
    """Получить все сегменты (включая неактивные) для админки."""
    result = await session.execute(select(Segment).order_by(Segment.id))
    return list(result.scalars().all())


async def get_segment_by_id_for_admin(
    session: AsyncSession, segment_id: int
) -> Segment | None:
    """Получить сегмент по id (для админки)."""
    result = await session.execute(
        select(Segment).where(Segment.id == segment_id)
    )
    return result.scalar_one_or_none()


async def toggle_segment_active(
    session: AsyncSession, segment_id: int
) -> bool:
    """Переключить is_active сегмента. Возвращает новое значение."""
    segment = await get_segment_by_id_for_admin(session, segment_id)
    if segment is None:
        return False
    segment.is_active = not segment.is_active
    await session.commit()
    await session.refresh(segment)
    return segment.is_active
