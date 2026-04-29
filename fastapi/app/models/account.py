from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.base import Base
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.loyalty_program import LoyaltyProgram
    from app.models.loyalty_transaction import LoyaltyTransaction
    from app.models.user import User


class Account(Base):
    """
    Банковский счёт пользователя с привязанной программой лояльности.
    Один пользователь может иметь несколько счетов с разными программами.
    Например: дебетовый Black + кредитный All Airlines.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    loyalty_program_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_programs.id"), nullable=False
    )
    current_balance: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,  # текущий баланс кэшбэка в валюте программы
    )

    user: Mapped["User"] = relationship(back_populates="accounts")
    loyalty_program: Mapped["LoyaltyProgram"] = relationship(back_populates="accounts")
    transactions: Mapped[list["LoyaltyTransaction"]] = relationship(
        back_populates="account"
    )
