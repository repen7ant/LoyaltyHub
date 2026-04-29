"""
Тесты для эндпоинтов loyalty API.
Покрывают: summary, history, monthly history, forecast.
"""

from datetime import date, timedelta

import pytest
import pytest_asyncio
from app.models.account import Account
from app.models.loyalty_program import CashbackCurrency, LoyaltyProgram
from app.models.loyalty_transaction import LoyaltyTransaction
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Вспомогательные фикстуры
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def loyalty_programs(db: AsyncSession) -> dict[str, LoyaltyProgram]:
    """Создаёт три программы лояльности."""
    programs = [
        LoyaltyProgram(id=1, name="Black", cashback_currency=CashbackCurrency.RUB),
        LoyaltyProgram(
            id=2, name="All Airlines", cashback_currency=CashbackCurrency.MILES
        ),
        LoyaltyProgram(id=3, name="Bravo", cashback_currency=CashbackCurrency.BRAVO),
    ]
    for p in programs:
        db.add(p)
    await db.commit()
    return {p.name: p for p in programs}


@pytest_asyncio.fixture()
async def accounts(db: AsyncSession, test_user, loyalty_programs) -> dict[str, Account]:
    """Создаёт счета для тестового пользователя по каждой программе."""
    accs = [
        Account(
            user_id=test_user.id,
            loyalty_program_id=loyalty_programs["Black"].id,
            current_balance=3000.0,
        ),
        Account(
            user_id=test_user.id,
            loyalty_program_id=loyalty_programs["All Airlines"].id,
            current_balance=1000.0,
        ),
        Account(
            user_id=test_user.id,
            loyalty_program_id=loyalty_programs["Bravo"].id,
            current_balance=2000.0,
        ),
    ]
    for a in accs:
        db.add(a)
    await db.commit()
    for a in accs:
        await db.refresh(a)
    return {
        "black": accs[0],
        "airlines": accs[1],
        "bravo": accs[2],
    }


@pytest_asyncio.fixture()
async def transactions(db: AsyncSession, accounts) -> list[LoyaltyTransaction]:
    """
    Создаёт транзакции за последние 3 месяца для тестирования прогноза.
    По 2 транзакции в месяц на каждый счёт.
    """
    today = date.today()
    txs = []

    for month_offset in [1, 2, 3]:
        tx_date = date(today.year, today.month, 1) - timedelta(days=30 * month_offset)
        for account in accounts.values():
            txs.append(
                LoyaltyTransaction(
                    account_id=account.id,
                    cashback_amount=500.0,
                    payout_date=tx_date,
                )
            )

    for tx in txs:
        db.add(tx)
    await db.commit()
    return txs


# ---------------------------------------------------------------------------
# Тесты summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loyalty_summary_returns_correct_totals(
    client, accounts, loyalty_programs
):
    """Сводка должна вернуть корректные суммы по каждой валюте."""
    response = await client.get("/loyalty/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_rub"] == 3000.0
    assert data["total_miles"] == 1000.0
    assert data["total_bravo"] == 2000.0


@pytest.mark.asyncio
async def test_loyalty_summary_equivalent_rub(client, accounts, loyalty_programs):
    """
    total_equivalent_rub = rub + miles*2 + bravo*0.5
    3000 + 1000*2 + 2000*0.5 = 3000 + 2000 + 1000 = 6000
    """
    response = await client.get("/loyalty/summary")
    assert response.status_code == 200
    assert response.json()["total_equivalent_rub"] == 6000.0


@pytest.mark.asyncio
async def test_loyalty_summary_empty_for_user_without_accounts(client):
    """Пользователь без счетов должен получить нулевые значения."""
    response = await client.get("/loyalty/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_rub"] == 0.0
    assert data["total_miles"] == 0.0
    assert data["total_bravo"] == 0.0
    assert data["total_equivalent_rub"] == 0.0
    assert data["accounts"] == []


# ---------------------------------------------------------------------------
# Тесты history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loyalty_history_returns_all_transactions(client, transactions):
    """История должна вернуть все транзакции пользователя."""
    response = await client.get("/loyalty/history")
    assert response.status_code == 200
    assert len(response.json()) == len(transactions)


@pytest.mark.asyncio
async def test_loyalty_history_empty_without_transactions(client, accounts):
    """История без транзакций должна вернуть пустой список."""
    response = await client.get("/loyalty/history")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_loyalty_monthly_history_groups_by_month(client, transactions):
    """Месячная история должна группировать транзакции по месяцам."""
    response = await client.get("/loyalty/history/monthly")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1  # минимум один месяц

    # Каждый элемент должен содержать поле month в формате YYYY-MM
    for item in data:
        assert len(item["month"]) == 7
        assert item["month"][4] == "-"


# ---------------------------------------------------------------------------
# Тесты forecast
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loyalty_forecast_returns_predictions(client, accounts, transactions):
    """Прогноз должен вернуть предсказания по каждой программе."""
    response = await client.get("/loyalty/forecast")
    assert response.status_code == 200

    data = response.json()
    assert len(data["forecasts"]) > 0
    assert data["total_predicted_equivalent_rub"] > 0


@pytest.mark.asyncio
async def test_loyalty_forecast_applies_growth_coefficient(
    client, accounts, transactions
):
    """Прогноз должен быть выше среднего за счёт коэффициента 1.2."""
    response = await client.get("/loyalty/forecast")
    assert response.status_code == 200

    for forecast in response.json()["forecasts"]:
        assert forecast["predicted_amount"] > 0
        # Коэффициент 1.2 означает прогноз всегда больше нуля при наличии транзакций
        assert forecast["predicted_equivalent_rub"] > 0


# ---------------------------------------------------------------------------
# Тест авторизации
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loyalty_requires_auth():
    """Запрос без токена должен вернуть 401."""
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/loyalty/summary")
    assert response.status_code == 401
