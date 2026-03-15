# models/funnel.py — модель воронки
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.funnel_step import FunnelStep
    from models.segment import Segment


class Funnel(Base):
    """Воронка для сегмента (серия шагов)."""

    __tablename__ = "funnels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("segments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    segment: Mapped["Segment"] = relationship("Segment", back_populates="funnels")
    steps: Mapped[list["FunnelStep"]] = relationship(
        "FunnelStep", back_populates="funnel", cascade="all, delete-orphan"
    )
