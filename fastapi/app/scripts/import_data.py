"""
Скрипт импорта CSV-данных в базу данных.
Запускается автоматически через docker compose (сервис import-data).
Для ручного запуска: docker exec loyaltyhub-fastapi uv run python -m app.scripts.import_data
"""

import asyncio
import csv
from datetime import date
from pathlib import Path

from app.db.session import AsyncSessionLocal
from app.models import (
    Account,
    CashbackCurrency,
    FinancialSegment,
    LoyaltyProgram,
    LoyaltyTransaction,
    Offer,
    User,
)
from app.services.auth_service import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession

# Путь к папке с CSV-файлами
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def open_csv(filename: str) -> list[dict]:
    """Открывает CSV с учётом BOM и windows-переносов строк."""
    path = DATA_DIR / filename
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


async def import_loyalty_programs(session: AsyncSession) -> None:
    rows = open_csv("LoyaltyPrograms.csv")
    for row in rows:
        program = LoyaltyProgram(
            id=int(row["loyalty_program_id"]),
            name=row["loyalty_program_name"],
            cashback_currency=CashbackCurrency(row["cashback_currency"]),
        )
        session.add(program)
    print(f"  LoyaltyPrograms: {len(rows)} записей")


async def import_users(session: AsyncSession) -> None:
    rows = open_csv("Users.csv")
    for row in rows:
        user = User(
            id=int(row["id"]),
            email=row["email"],
            hashed_password=get_password_hash(f"user_{row['id']}"),
            phone_number=row["phone_number"],
            full_name=row["full_name"],
            financial_segment=FinancialSegment(row["financial_segment"]),
        )
        session.add(user)
    print(f"  Users: {len(rows)} записей")


async def import_accounts(session: AsyncSession) -> None:
    rows = open_csv("Accounts.csv")
    for row in rows:
        account = Account(
            id=int(row["account_id"]),
            user_id=int(row["user_id"]),
            loyalty_program_id=int(row["loyalty_program_id"]),
            current_balance=float(row["current_balance"]),
        )
        session.add(account)
    print(f"  Accounts: {len(rows)} записей")


async def import_loyalty_history(session: AsyncSession) -> None:
    rows = open_csv("LoyaltyHistory.csv")
    for row in rows:
        transaction = LoyaltyTransaction(
            id=int(row["transaction_id"]),
            account_id=int(row["account_id"]),
            cashback_amount=float(row["cashback_amount"]),
            payout_date=date.fromisoformat(row["payout_date"]),
        )
        session.add(transaction)
    print(f"  LoyaltyHistory: {len(rows)} записей")


async def import_offers(session: AsyncSession) -> None:
    rows = open_csv("Offers.csv")
    for row in rows:
        offer = Offer(
            id=int(row["partner_id"]),
            partner_name=row["partner_name"],
            short_description=row["short_description"],
            logo_url=row["logo_url"],
            brand_color_hex=row["brand_color_hex"],
            cashback_percent=float(row["cashback_percent"]),
            financial_segment=FinancialSegment(row["financial_segment"]),
        )
        session.add(offer)
    print(f"  Offers: {len(rows)} записей")


async def main() -> None:
    print("Начинаем импорт данных...")
    async with AsyncSessionLocal() as session:
        # Порядок важен — сначала то, на что есть FK
        await import_loyalty_programs(session)
        await import_users(session)
        await import_accounts(session)
        await import_loyalty_history(session)
        await import_offers(session)
        await session.commit()
    print("Импорт завершён успешно.")


if __name__ == "__main__":
    asyncio.run(main())
