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
