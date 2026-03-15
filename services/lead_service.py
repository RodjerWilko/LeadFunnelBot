# services/lead_service.py — работа с заявками
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models.lead import Lead


async def create_lead(
    session: AsyncSession, user_id: int, message: str
) -> Lead:
    """Создать заявку (лид)."""
    lead = Lead(user_id=user_id, message=message.strip())
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead
