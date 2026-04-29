from datetime import date

from app.models.loyalty_program import CashbackCurrency
from pydantic import BaseModel


class AccountSummary(BaseModel):
    """Сводка по одному счёту пользователя."""

    account_id: int
    loyalty_program_name: str
    cashback_currency: CashbackCurrency
    current_balance: float  # текущий баланс в валюте программы

    model_config = {"from_attributes": True}


class LoyaltySummary(BaseModel):
    """Совокупная лояльность пользователя по всем счетам и программам."""

    total_rub: float  # рубли (программа Black)
    total_miles: float  # мили (программа All Airlines)
    total_bravo: float  # баллы Браво (программа Platinum)
    accounts: list[AccountSummary]


class HistoryItem(BaseModel):
    """Одна запись истории начислений."""

    transaction_id: int
    account_id: int
    loyalty_program_name: str
    cashback_currency: CashbackCurrency
    cashback_amount: float
    payout_date: date

    model_config = {"from_attributes": True}


class MonthlyHistory(BaseModel):
    """История начислений сгруппированная по месяцам."""

    month: str  # формат: "2025-04"
    total_rub: float
    total_miles: float
    total_bravo: float
