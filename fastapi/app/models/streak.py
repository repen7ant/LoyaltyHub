from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.user import User


class UserStreak(Base):
    """
    Стрик пользователя — серия ежедневных заходов в раздел лояльности.
    Хранит текущий стрик, рекорд и историю заходов для календаря.
    Сбрасывается если пользователь пропустил день.
    """

    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True
    )
    streak_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,  # текущая длина стрика в днях
    )
    max_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,  # рекорд пользователя
    )
    last_visit_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,  # дата последнего захода
    )

    user: Mapped["User"] = relationship(back_populates="streak")
