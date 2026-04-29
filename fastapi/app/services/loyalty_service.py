from app.models.account import Account
from app.models.loyalty_program import CashbackCurrency
from app.models.loyalty_transaction import LoyaltyTransaction
from app.schemas.loyalty import (
    AccountSummary,
    LoyaltySummary,
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
