from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.account import Account


class CashbackCurrency(str, enum.Enum):
    """
    Валюта кэшбэка программы лояльности.
    - RUB: рубли (программа Black)
    - MILES: мили (программа All Airlines)
    - BRAVO: баллы Браво (программа Platinum)
    """

    RUB = "rub"
    MILES = "miles"
    BRAVO = "bravo-points"


class LoyaltyProgram(Base):
    """
    Программа лояльности банка.
    Три программы: Black (рубли), All Airlines (мили), Platinum/Bravo (баллы).
    К одному аккаунту привязана одна программа лояльности.
    """

    __tablename__ = "loyalty_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cashback_currency: Mapped[CashbackCurrency] = mapped_column(
        Enum(CashbackCurrency),
        nullable=False,  # определяет единицу начисления кэшбэка
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="loyalty_program")
