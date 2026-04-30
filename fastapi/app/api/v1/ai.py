from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import AIRecommendation
from app.schemas.offer import OfferResponse
from app.services.ai_service import AIService
from app.services.loyalty_service import LoyaltyService
from app.services.offer_service import OfferService
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/recommend", response_model=AIRecommendation)
async def get_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Персонализированная ИИ-рекомендация на основе данных пользователя.
    Анализирует накопления, прогноз и доступные акции через Anthropic API.
    Возвращает короткий совет как получить максимум выгоды.
    """
    loyalty_service = LoyaltyService(db)
    offer_service = OfferService(db)
    ai_service = AIService()

    # Собираем все данные пользователя
    summary = await loyalty_service.get_summary(current_user.id)
    forecast = await loyalty_service.get_forecast(current_user.id)
    offer_models = await offer_service.get_user_offers(current_user)
    offers = [OfferResponse.model_validate(o) for o in offer_models]

    recommendation = await ai_service.get_recommendation(
        user=current_user,
        summary=summary,
        forecast=forecast,
        offers=offers,
    )

    return AIRecommendation(recommendation=recommendation)
