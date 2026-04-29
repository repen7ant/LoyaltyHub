"""
Тесты для эндпоинта offers API.
Покрывают: фильтрацию по сегменту, сортировку, исключение уже имеющихся продуктов экосистемы.
"""

import pytest
import pytest_asyncio
from app.models.account import Account
from app.models.loyalty_program import CashbackCurrency, LoyaltyProgram
from app.models.offer import Offer, OfferType
from app.models.user import FinancialSegment
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Вспомогательные фикстуры
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def offers(db: AsyncSession, test_user) -> list[Offer]:
    """
    Создаёт офферы для разных сегментов.
    test_user имеет сегмент HIGH — должны вернуться только HIGH офферы.
    """
    data = [
        Offer(
            partner_name="Партнёр HIGH 1",
            short_description="Описание 1",
            logo_url="https://example.com/logo1.png",
            brand_color_hex="#FF0000",
            cashback_percent=10.0,
            financial_segment=FinancialSegment.HIGH,
            offer_type=OfferType.PARTNER,
        ),
        Offer(
            partner_name="Партнёр HIGH 2",
            short_description="Описание 2",
            logo_url="https://example.com/logo2.png",
            brand_color_hex="#00FF00",
            cashback_percent=5.0,
            financial_segment=FinancialSegment.HIGH,
            offer_type=OfferType.PARTNER,
        ),
        Offer(
            partner_name="Партнёр LOW",
            short_description="Описание LOW",
            logo_url="https://example.com/logo3.png",
            brand_color_hex="#0000FF",
            cashback_percent=15.0,
            financial_segment=FinancialSegment.LOW,
            offer_type=OfferType.PARTNER,
        ),
    ]
    for o in data:
        db.add(o)
    await db.commit()
    return data


@pytest_asyncio.fixture()
async def ecosystem_offer(db: AsyncSession, test_user) -> Offer:
    """Оффер типа ECOSYSTEM — продукт экосистемы Т-Банка."""
    offer = Offer(
        partner_name="Т-Инвестиции",
        short_description="Инвестируй с Т",
        logo_url="https://example.com/invest.png",
        brand_color_hex="#FFFF00",
        cashback_percent=3.0,
        financial_segment=FinancialSegment.HIGH,
        offer_type=OfferType.ECOSYSTEM,
        target_product_id="1",  # loyalty_program_id=1
    )
    db.add(offer)
    await db.commit()
    return offer


@pytest_asyncio.fixture()
async def loyalty_program(db: AsyncSession) -> LoyaltyProgram:
    program = LoyaltyProgram(id=1, name="Black", cashback_currency=CashbackCurrency.RUB)
    db.add(program)
    await db.commit()
    return program


@pytest_asyncio.fixture()
async def user_account(db: AsyncSession, test_user, loyalty_program) -> Account:
    """Счёт пользователя с программой лояльности id=1."""
    account = Account(
        user_id=test_user.id,
        loyalty_program_id=loyalty_program.id,
        current_balance=1000.0,
    )
    db.add(account)
    await db.commit()
    return account


# ---------------------------------------------------------------------------
# Тесты
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_offers_returns_only_user_segment(client, offers):
    """Должны вернуться только офферы для сегмента пользователя (HIGH)."""
    response = await client.get("/offers/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2  # только два HIGH оффера
    for offer in data:
        assert offer["financial_segment"] == FinancialSegment.HIGH.value


@pytest.mark.asyncio
async def test_offers_sorted_by_cashback_desc(client, offers):
    """Офферы должны быть отсортированы по кэшбэку по убыванию."""
    response = await client.get("/offers/")
    assert response.status_code == 200

    data = response.json()
    percents = [o["cashback_percent"] for o in data]
    assert percents == sorted(percents, reverse=True)


@pytest.mark.asyncio
async def test_offers_empty_without_matching_segment(client, db):
    """Если офферов для сегмента нет — вернуть пустой список."""
    response = await client.get("/offers/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_ecosystem_offer_excluded_if_user_has_product(
    client, ecosystem_offer, user_account
):
    """
    Оффер типа ECOSYSTEM должен быть исключён,
    если пользователь уже имеет этот продукт (счёт с loyalty_program_id=1).
    """
    response = await client.get("/offers/")
    assert response.status_code == 200

    names = [o["partner_name"] for o in response.json()]
    assert "Т-Инвестиции" not in names


@pytest.mark.asyncio
async def test_ecosystem_offer_shown_if_user_lacks_product(client, ecosystem_offer):
    """
    Оффер типа ECOSYSTEM должен показываться,
    если у пользователя нет этого продукта.
    """
    response = await client.get("/offers/")
    assert response.status_code == 200

    names = [o["partner_name"] for o in response.json()]
    assert "Т-Инвестиции" in names


@pytest.mark.asyncio
async def test_offers_requires_auth():
    """Запрос без токена должен вернуть 401."""
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/offers/")
    assert response.status_code == 401
