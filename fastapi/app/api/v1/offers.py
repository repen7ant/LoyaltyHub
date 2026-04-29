from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.offer import OfferResponse
from app.services.offer_service import OfferService
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/offers", tags=["Offers"])


async def get_offer_service(db: AsyncSession = Depends(get_db)) -> OfferService:
    return OfferService(db)


@router.get("/", response_model=list[OfferResponse])
async def get_personal_offers(
    current_user: User = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    """
    Персональные предложения и акции партнёров.
    Выдача строго фильтруется на основе финансового сегмента текущего пользователя (LOW, MEDIUM, HIGH).
    Сначала продукты экосистемы, далее предложения партнеров, фильтрующиеся по убывания % кэшбека.
    """
    # Передаем текущего юзера в сервис целиком, чтобы проверить открытые счета
    offers = await service.get_user_offers(current_user)
    return offers
