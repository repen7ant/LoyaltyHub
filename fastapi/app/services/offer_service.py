from app.models.offer import Offer
from app.models.user import FinancialSegment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class OfferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_offers(self, segment: FinancialSegment) -> list[Offer]:
        """
        Получает список акций и спецпредложений,
        релевантных для финансового сегмента пользователя.
        """
        result = await self.db.execute(
            select(Offer)
            .where(Offer.financial_segment == segment)
            .order_by(Offer.cashback_percent.desc())
            # сортировка по % кэшбэка по убыванию,чтобы самые выгодные были сверху
        )
        return result.scalars().all()
