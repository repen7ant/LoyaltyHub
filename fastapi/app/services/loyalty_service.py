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
        return result.scalars().all()

    async def _get_transactions(
        self, account_ids: list[int]
    ) -> list[LoyaltyTransaction]:
        """Возвращает все транзакции по списку счетов."""
        result = await self.db.execute(
            select(LoyaltyTransaction)
            .where(LoyaltyTransaction.account_id.in_(account_ids))
            .order_by(LoyaltyTransaction.payout_date.desc())
        )
        return result.scalars().all()

    async def get_summary(self, user_id: int) -> LoyaltySummary:
        """
        Возвращает совокупную лояльность пользователя.
        Суммирует текущие балансы по каждой валюте кэшбэка.
        """
        accounts = await self._get_user_accounts(user_id)

        total_rub = 0.0
        total_miles = 0.0
        total_bravo = 0.0
        account_summaries = []

        for account in accounts:
            program = account.loyalty_program
            balance = float(account.current_balance)

            # Суммируем по типу валюты
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
            total_rub=total_rub,
            total_miles=total_miles,
            total_bravo=total_bravo,
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

        # Группируем по месяцу и валюте
        monthly: dict[str, dict[str, float]] = defaultdict(
            lambda: {"rub": 0.0, "miles": 0.0, "bravo-points": 0.0}
        )

        for item in items:
            month_key = item.payout_date.strftime("%Y-%m")
            monthly[month_key][item.cashback_currency.value] += item.cashback_amount

        # Сортируем по дате
        return [
            MonthlyHistory(
                month=month,
                total_rub=data["rub"],
                total_miles=data["miles"],
                total_bravo=data["bravo-points"],
            )
            for month, data in sorted(monthly.items())
        ]

    async def get_forecast(self, user_id: int) -> LoyaltyForecast:
        """
        Прогноз выгоды на следующий месяц.
        Считается как среднее начислений за последние 3 месяца по каждой программе.
        """
        accounts = await self._get_user_accounts(user_id)
        account_map = {a.id: a for a in accounts}
        account_ids = list(account_map.keys())

        transactions = await self._get_transactions(account_ids)

        today = date.today()

        # Берём транзакции за последние 3 месяца
        recent_months = set()
        for tx in transactions:
            months_diff = (today.year - tx.payout_date.year) * 12 + (
                today.month - tx.payout_date.month
            )
            if months_diff <= 3:
                recent_months.add(tx.payout_date.strftime("%Y-%m"))

        # Суммируем по программам за последние 3 месяца
        program_totals: dict[int, float] = defaultdict(float)
        program_months: dict[int, set] = defaultdict(set)

        for tx in transactions:
            months_diff = (today.year - tx.payout_date.year) * 12 + (
                today.month - tx.payout_date.month
            )
            if months_diff <= 3:
                account = account_map[tx.account_id]
                program_id = account.loyalty_program_id
                program_totals[program_id] += float(tx.cashback_amount)
                program_months[program_id].add(tx.payout_date.strftime("%Y-%m"))

        # Считаем среднее и формируем прогноз
        forecasts = []
        for account in accounts:
            program = account.loyalty_program
            pid = program.id
            months_count = len(program_months.get(pid, set())) or 1
            predicted = round(program_totals.get(pid, 0.0) / months_count, 2)

            # Избегаем дублирования программ если у пользователя несколько счетов одной программы
            if not any(f.loyalty_program_name == program.name for f in forecasts):
                forecasts.append(
                    ForecastItem(
                        loyalty_program_name=program.name,
                        cashback_currency=program.cashback_currency,
                        predicted_amount=predicted,
                    )
                )

        return LoyaltyForecast(forecasts=forecasts)
