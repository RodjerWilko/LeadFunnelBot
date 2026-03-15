# services/funnel_service.py — воронки и сегменты
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.funnel import Funnel
from models.funnel_step import FunnelStep
from models.segment import Segment


# Тексты шагов воронок по умолчанию (сегмент -> список текстов для step 1, 2, 3)
DEFAULT_FUNNEL_TEXTS: dict[str, list[str]] = {
    "Маркетинг": [
        "📢 Маркетинг в Telegram — это охват целевой аудитории без лишнего шума.\n\n"
        "В этом демо вы увидите, как работает простая автоворонка для лидов.",
        "📈 Второй шаг воронки: полезный контент, кейсы, призыв к действию.\n\n"
        "Так мы прогреваем подписчика и подводим к заявке.",
        "🚀 Готовы обсудить маркетинг для вашего проекта? Оставьте заявку — мы свяжемся с вами.",
    ],
    "Telegram-боты": [
        "🤖 Telegram-бот может автоматизировать продажи, запись клиентов и поддержку.\n\n"
        "В этом демо-боте показан базовый сценарий автоворонки.",
        "📈 Второй шаг воронки обычно прогревает пользователя: кейсы, выгоды, "
        "примеры автоматизации, точки роста бизнеса.",
        "🚀 Если хотите такого бота для своего проекта — оставьте заявку, и мы обсудим задачу.",
    ],
    "AI": [
        "🧠 AI в бизнесе: чат-боты, аналитика, автоматизация рутины.\n\n"
        "В этом демо показана простая воронка с отложенными сообщениями.",
        "📈 Следующий шаг — углубление в пользу: где AI уже даёт результат, "
        "какие задачи решает, как начать пробовать.",
        "🚀 Хотите обсудить внедрение AI в ваш процесс? Оставьте заявку.",
    ],
}


async def get_segments(session: AsyncSession) -> list[Segment]:
    """Получить все сегменты."""
    result = await session.execute(select(Segment).order_by(Segment.id))
    return list(result.scalars().all())


async def get_active_segments(session: AsyncSession) -> list[Segment]:
    """Получить только активные сегменты (для выбора пользователем)."""
    result = await session.execute(
        select(Segment).where(Segment.is_active == True).order_by(Segment.id)
    )
    return list(result.scalars().all())


async def get_segment_by_id(
    session: AsyncSession, segment_id: int
) -> Segment | None:
    """Получить сегмент по id."""
    result = await session.execute(
        select(Segment).where(Segment.id == segment_id)
    )
    return result.scalar_one_or_none()


async def get_segment_by_name(
    session: AsyncSession, name: str
) -> Segment | None:
    """Получить сегмент по имени."""
    result = await session.execute(
        select(Segment).where(Segment.name == name)
    )
    return result.scalar_one_or_none()


async def get_funnel_by_segment_id(
    session: AsyncSession, segment_id: int
) -> Funnel | None:
    """Получить воронку для сегмента (первую, если несколько)."""
    result = await session.execute(
        select(Funnel)
        .where(Funnel.segment_id == segment_id)
        .order_by(Funnel.id)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_funnel_steps(
    session: AsyncSession, funnel_id: int
) -> list[FunnelStep]:
    """Получить шаги воронки по порядку step_number."""
    result = await session.execute(
        select(FunnelStep)
        .where(FunnelStep.funnel_id == funnel_id)
        .order_by(FunnelStep.step_number)
    )
    return list(result.scalars().all())


async def bootstrap_default_funnels(session: AsyncSession) -> None:
    """
    Создать сегменты и воронки по умолчанию, если их ещё нет.
    Для каждого сегмента — одна воронка из 3 шагов (0, 24, 72 ч).
    """
    existing = await get_segments(session)
    if existing:
        return

    for name, texts in DEFAULT_FUNNEL_TEXTS.items():
        segment = Segment(name=name)
        session.add(segment)
        await session.flush()

        funnel = Funnel(segment_id=segment.id, name=f"Воронка: {name}")
        session.add(funnel)
        await session.flush()

        delays = [0, 24, 72]
        for step_number, (delay_hours, message_text) in enumerate(
            zip(delays, texts), start=1
        ):
            step = FunnelStep(
                funnel_id=funnel.id,
                step_number=step_number,
                delay_hours=delay_hours,
                message_text=message_text,
            )
            session.add(step)

    await session.commit()
