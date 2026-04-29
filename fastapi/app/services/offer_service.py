from app.models.account import Account
from app.models.offer import Offer, OfferType
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class OfferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_offers(self, user: User) -> list[Offer]:
        """
        Получает список акций и спецпредложений,
        релевантных для финансового сегмента пользователя.
        """
        # 1. Получаем все офферы для сегмента
        result = await self.db.execute(
            select(Offer).where(Offer.financial_segment == user.financial_segment)
        )
        all_offers = result.scalars().all()

        # 2. Получаем ID программ лояльности (карт), которые уже есть у юзера
        acc_result = await self.db.execute(
            select(Account.loyalty_program_id).where(Account.user_id == user.id)
        )
        owned_ids = set(acc_result.scalars().all())

        # 3. Фильтруем: исключаем продукты экосистемы, которые уже есть у юзера
        final_offers = []
        for offer in all_offers:
            if offer.offer_type == OfferType.ECOSYSTEM and offer.target_product_id:
                if (
                    offer.target_product_id.isdigit()
                    and int(offer.target_product_id) in owned_ids
                ):
                    continue  # Пропускаем продукт, так как счет уже открыт
            final_offers.append(offer)

        # Сортируем: сначала продукты экосистемы, затем
        # сортировка по % кэшбэка по убыванию,чтобы самые выгодные были сверху
        final_offers.sort(
            key=lambda x: (
                x.offer_type != OfferType.ECOSYSTEM,
                -float(x.cashback_percent),
            )
        )

        return final_offers
