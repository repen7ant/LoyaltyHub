from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.account import Account


class FinancialSegment(str, enum.Enum):
    """
    Финансовый сегмент пользователя на основе объёма финансов в экосистеме Т-Банка.
    Влияет на отображение акций партнёров и кросс-селл предложений.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class User(Base):
    """Пользователь системы лояльности."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    financial_segment: Mapped[FinancialSegment] = mapped_column(
        Enum(FinancialSegment),
        nullable=False,  # сегмент определяет доступные офферы
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")
