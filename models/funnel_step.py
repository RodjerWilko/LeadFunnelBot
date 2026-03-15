# models/funnel_step.py — шаг воронки
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.funnel import Funnel


class FunnelStep(Base):
    """Один шаг воронки (сообщение с задержкой в часах)."""

    __tablename__ = "funnel_steps"
    __table_args__ = (UniqueConstraint("funnel_id", "step_number", name="uq_funnel_step"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    funnel_id: Mapped[int] = mapped_column(
        ForeignKey("funnels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    funnel: Mapped["Funnel"] = relationship("Funnel", back_populates="steps")
