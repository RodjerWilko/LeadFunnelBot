# services/user_service.py — работа с пользователями
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    """Получить пользователя по telegram_id."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    """Создать пользователя."""
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    """Получить пользователя или создать, если нет."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is not None:
        return user
    return await create_user(session, telegram_id, username, first_name)


async def update_user_segment(
    session: AsyncSession, user_id: int, segment_id: int | None
) -> bool:
    """Обновить выбранный сегмент пользователя."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return False
    user.segment_id = segment_id
    await session.commit()
    return True


async def get_all_users_telegram_ids(session: AsyncSession) -> list[int]:
    """Список telegram_id всех пользователей (для рассылки)."""
    result = await session.execute(select(User.telegram_id))
    return [row[0] for row in result.all()]
