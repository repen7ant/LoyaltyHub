from collections import defaultdict
from datetime import date

from app.models.account import Account
from app.models.loyalty_program import CashbackCurrency
from app.models.loyalty_transaction import LoyaltyTransaction
from app.schemas.loyalty import (
    AccountSummary,
    ForecastItem,
    HistoryItem,
    LoyaltyForecast,
    LoyaltySummary,
    MonthlyHistory,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Коэффициенты конвертации валют лояльности в рубли
BRAVO_TO_RUB = 0.5  # 1 балл Браво ≈ 0.5 ₽
MILE_TO_RUB = 2.0  # 1 миля ≈ 2 ₽

# Коэффициент роста активности после внедрения раздела лояльности
FORECAST_GROWTH = 1.2


def to_rub_equivalent(rub: float, miles: float, bravo: float) -> float:
    """Приводит все валюты кэшбэка к рублёвому эквиваленту."""
    return round(rub + miles * MILE_TO_RUB + bravo * BRAVO_TO_RUB, 2)


class LoyaltyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_accounts(self, user_id: int) -> list[Account]:
        """Возвращает все счета пользователя с загруженными программами лояльности."""
        result = await self.db.execute(
            select(Account)
            .where(Account.user_id == user_id)
            .options(selectinload(Account.loyalty_program))
        )
        return list(result.scalars().all())

    async def _get_transactions(
        self, account_ids: list[int]
    ) -> list[LoyaltyTransaction]:
        """Возвращает все транзакции по списку счетов."""
        result = await self.db.execute(
            select(LoyaltyTransaction)
            .where(LoyaltyTransaction.account_id.in_(account_ids))
            .order_by(LoyaltyTransaction.payout_date.desc())
        )
        return list(result.scalars().all())

    async def get_summary(self, user_id: int) -> LoyaltySummary:
        """
        Возвращает совокупную лояльность пользователя.
        Суммирует текущие балансы по каждой валюте и приводит к рублям.
        """
        accounts = await self._get_user_accounts(user_id)

        total_rub = 0.0
        total_miles = 0.0
        total_bravo = 0.0
        account_summaries = []

        for account in accounts:
            program = account.loyalty_program
            balance = float(account.current_balance)

            if program.cashback_currency == CashbackCurrency.RUB:
                total_rub += balance
            elif program.cashback_currency == CashbackCurrency.MILES:
                total_miles += balance
            elif program.cashback_currency == CashbackCurrency.BRAVO:
                total_bravo += balance

            account_summaries.append(
                AccountSummary(
                    account_id=account.id,
                    loyalty_program_name=program.name,
                    cashback_currency=program.cashback_currency,
                    current_balance=balance,
                )
            )

        return LoyaltySummary(
            total_rub=round(total_rub, 2),
            total_miles=round(total_miles, 2),
            total_bravo=round(total_bravo, 2),
            total_equivalent_rub=to_rub_equivalent(total_rub, total_miles, total_bravo),
            accounts=account_summaries,
        )

    async def get_history(self, user_id: int) -> list[HistoryItem]:
        """
        Возвращает историю начислений пользователя.
        Каждая запись содержит название программы и валюту кэшбэка.
        """
        accounts = await self._get_user_accounts(user_id)
        account_map = {a.id: a for a in accounts}
        account_ids = list(account_map.keys())

        transactions = await self._get_transactions(account_ids)

        result = []
        for tx in transactions:
            account = account_map[tx.account_id]
            program = account.loyalty_program
            result.append(
                HistoryItem(
                    transaction_id=tx.id,
                    account_id=tx.account_id,
                    loyalty_program_name=program.name,
                    cashback_currency=program.cashback_currency,
                    cashback_amount=float(tx.cashback_amount),
                    payout_date=tx.payout_date,
                )
            )

        return result

    async def get_monthly_history(self, user_id: int) -> list[MonthlyHistory]:
        """
        История начислений сгруппированная по месяцам.
        Используется для графика динамики кэшбэка.
        """
        items = await self.get_history(user_id)

        monthly: dict[str, dict[str, float]] = defaultdict(
            lambda: {"rub": 0.0, "miles": 0.0, "bravo-points": 0.0}
        )

        for item in items:
            month_key = item.payout_date.strftime("%Y-%m")
            monthly[month_key][item.cashback_currency.value] += item.cashback_amount

        return [
            MonthlyHistory(
                month=month,
                total_rub=round(data["rub"], 2),
                total_miles=round(data["miles"], 2),
                total_bravo=round(data["bravo-points"], 2),
                total_equivalent_rub=to_rub_equivalent(
                    data["rub"], data["miles"], data["bravo-points"]
                ),
            )
            for month, data in sorted(monthly.items())
        ]

    async def get_forecast(self, user_id: int) -> LoyaltyForecast:
        """
        Прогноз выгоды на следующий месяц.
        Среднее за последние 3 месяца × FORECAST_GROWTH (1.2).
        """
        accounts = await self._get_user_accounts(user_id)
        account_map = {a.id: a for a in accounts}
        account_ids = list(account_map.keys())

        transactions = await self._get_transactions(account_ids)

        today = date.today()

        # Суммируем начисления и уникальные месяцы по каждой программе за последние 3 месяца
        program_totals: dict[int, float] = defaultdict(float)
        program_months: dict[int, set] = defaultdict(set)
        program_currency: dict[int, CashbackCurrency] = {}
        program_name: dict[int, str] = {}

        for tx in transactions:
            months_diff = (today.year - tx.payout_date.year) * 12 + (
                today.month - tx.payout_date.month
            )
            if months_diff <= 3:
                account = account_map[tx.account_id]
                program = account.loyalty_program
                pid = program.id
                program_totals[pid] += float(tx.cashback_amount)
                program_months[pid].add(tx.payout_date.strftime("%Y-%m"))
                program_currency[pid] = program.cashback_currency
                program_name[pid] = program.name

        # Формируем прогноз — среднее × коэффициент роста
        forecasts = []
        seen_programs = set()

        for account in accounts:
            program = account.loyalty_program
            pid = program.id

            if pid in seen_programs:
                continue
            seen_programs.add(pid)

            months_count = len(program_months.get(pid, set())) or 1
            avg = program_totals.get(pid, 0.0) / months_count
            predicted = round(avg * FORECAST_GROWTH, 2)

            currency = program_currency.get(pid, program.cashback_currency)

            # Считаем рублёвый эквивалент прогноза
            if currency == CashbackCurrency.RUB:
                predicted_rub = predicted
            elif currency == CashbackCurrency.MILES:
                predicted_rub = round(predicted * MILE_TO_RUB, 2)
            else:  # BRAVO
                predicted_rub = round(predicted * BRAVO_TO_RUB, 2)

            forecasts.append(
                ForecastItem(
                    loyalty_program_name=program.name,
                    cashback_currency=currency,
                    predicted_amount=predicted,
                    predicted_equivalent_rub=predicted_rub,
                )
            )

        total_predicted_rub = round(
            sum(f.predicted_equivalent_rub for f in forecasts), 2
        )

        return LoyaltyForecast(
            forecasts=forecasts,
            total_predicted_equivalent_rub=total_predicted_rub,
        )
