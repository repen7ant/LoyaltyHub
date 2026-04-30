from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.streak import StreakResponse, TrackVisitResponse
from app.services.streak_service import StreakService
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/gamification", tags=["Gamification"])


async def get_streak_service(db: AsyncSession = Depends(get_db)) -> StreakService:
    return StreakService(db)


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    service: StreakService = Depends(get_streak_service),
):
    """
    Текущий стрик пользователя.
    Возвращает длину стрика, рекорд и прогресс до следующей награды.
    """
    return await service.get_streak(current_user)


@router.post("/streak/visit", response_model=TrackVisitResponse)
async def track_visit(
    current_user: User = Depends(get_current_user),
    service: StreakService = Depends(get_streak_service),
):
    """
    Трекинг ежедневного визита.
    Вызывается фронтендом при каждом заходе в раздел лояльности.
    Увеличивает стрик если прошёл ровно 1 день, сбрасывает если больше.
    Повторный вызов в тот же день ничего не меняет.
    """
    return await service.track_visit(current_user)
