from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.loyalty import (
    HistoryItem,
    LoyaltySummary,
    MonthlyHistory,
)
from app.services.loyalty_service import LoyaltyService
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


async def get_loyalty_service(db: AsyncSession = Depends(get_db)) -> LoyaltyService:
    return LoyaltyService(db)


@router.get("/summary", response_model=LoyaltySummary)
async def get_summary(
    current_user: User = Depends(get_current_user),
    service: LoyaltyService = Depends(get_loyalty_service),
):
    """
    Совокупная лояльность пользователя.
    Возвращает общий баланс по всем валютам (рубли, мили, баллы Браво)
    и детализацию по каждому счёту.
    """
    return await service.get_summary(current_user.id)


@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    current_user: User = Depends(get_current_user),
    service: LoyaltyService = Depends(get_loyalty_service),
):
    """
    Полная история начислений кэшбэка по всем счетам пользователя.
    Отсортирована по дате — сначала новые.
    """
    return await service.get_history(current_user.id)


@router.get("/history/monthly", response_model=list[MonthlyHistory])
async def get_monthly_history(
    current_user: User = Depends(get_current_user),
    service: LoyaltyService = Depends(get_loyalty_service),
):
    """
    История начислений сгруппированная по месяцам.
    Используется для построения графика динамики кэшбэка.
    """
    return await service.get_monthly_history(current_user.id)
