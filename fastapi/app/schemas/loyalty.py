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
    """
    Совокупная лояльность пользователя по всем счетам и программам.
    Все валюты приводятся к рублям для наглядного отображения общей выгоды.
    """

    total_rub: float  # рубли (программа Black)
    total_miles: float  # мили (программа All Airlines)
    total_bravo: float  # баллы Браво (программа Platinum)
    total_equivalent_rub: float  # совокупная выгода в рублях: rub + miles*2 + bravo*0.5
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
    total_equivalent_rub: float  # совокупная выгода месяца в рублях


class ForecastItem(BaseModel):
    """Прогноз выгоды по одной программе лояльности."""

    loyalty_program_name: str
    cashback_currency: CashbackCurrency
    predicted_amount: float  # прогноз в валюте программы
    predicted_equivalent_rub: float  # прогноз в рублях


class LoyaltyForecast(BaseModel):
    """
    Прогноз выгоды на следующий месяц.
    Считается как среднее за 3 месяца × коэффициент роста 1.2.
    Коэффициент 1.2 отражает предполагаемый рост активности
    после внедрения единого раздела лояльности.
    """

    forecasts: list[ForecastItem]
    total_predicted_equivalent_rub: (
        float  # суммарный прогноз в рублях по всем программам
    )
