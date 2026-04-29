from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.account import Account


class LoyaltyTransaction(Base):
    """
    Запись о начислении кэшбэка по счёту.
    Хранит историю выплат — используется для аналитики и прогнозирования выгоды.
    Сумма указывается в валюте программы лояльности привязанного счёта.
    """

    __tablename__ = "loyalty_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    cashback_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,  # сумма начисления в валюте программы
    )
    payout_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,  # дата выплаты кэшбэка
    )
    account: Mapped["Account"] = relationship(back_populates="transactions")
