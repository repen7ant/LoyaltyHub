from datetime import date

from app.models.streak import UserStreak
from app.models.user import User
from app.schemas.streak import StreakMilestone, StreakResponse, TrackVisitResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Пороги стрика с наградами
MILESTONES = [
    StreakMilestone(days=3, bonus_rub=20, achievement=None),
    StreakMilestone(days=7, bonus_rub=100, achievement="Первая неделя"),
    StreakMilestone(days=14, bonus_rub=200, achievement="Бустер x1.2 на 3 дня"),
    StreakMilestone(days=30, bonus_rub=500, achievement="Марафонец"),
    StreakMilestone(days=60, bonus_rub=1000, achievement="Эксклюзивная акция 20%"),
    StreakMilestone(days=100, bonus_rub=3000, achievement="Легенда"),
]


def _get_next_milestone(streak_count: int) -> tuple[StreakMilestone | None, int | None]:
    """Возвращает следующий порог и сколько дней до него."""
    for milestone in MILESTONES:
        if streak_count < milestone.days:
            return milestone, milestone.days - streak_count
    return None, None  # все пороги пройдены


def _check_milestone_reached(old_count: int, new_count: int) -> StreakMilestone | None:
    """Проверяет достигнут ли новый порог после обновления стрика."""
    for milestone in MILESTONES:
        if old_count < milestone.days <= new_count:
            return milestone
    return None


class StreakService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_streak(self, user_id: int) -> UserStreak:
        """Возвращает стрик пользователя или создаёт новый."""
        result = await self.db.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        if streak is None:
            streak = UserStreak(user_id=user_id)
            self.db.add(streak)
            await self.db.flush()
        return streak

    async def get_streak(self, user: User) -> StreakResponse:
        """Возвращает текущий стрик пользователя."""
        streak = await self._get_or_create_streak(user.id)
        today = date.today()

        visited_today = streak.last_visit_date == today
        next_milestone, days_until_next = _get_next_milestone(streak.streak_count)

        return StreakResponse(
            streak_count=streak.streak_count,
            max_streak=streak.max_streak,
            last_visit_date=streak.last_visit_date,
            next_milestone=next_milestone,
            days_until_next=days_until_next,
            visited_today=visited_today,
        )

    async def track_visit(self, user: User) -> TrackVisitResponse:
        """
        Трекинг ежедневного визита пользователя.
        Увеличивает стрик если прошёл ровно 1 день с последнего визита.
        Сбрасывает стрик если пропустил день.
        Игнорирует повторный визит в тот же день.
        """
        streak = await self._get_or_create_streak(user.id)
        today = date.today()

        # Уже заходил сегодня — ничего не меняем
        if streak.last_visit_date == today:
            return TrackVisitResponse(
                streak_count=streak.streak_count,
                visited_today=True,
                milestone_reached=None,
            )

        old_count = streak.streak_count

        if streak.last_visit_date is None:
            # Первый визит
            streak.streak_count = 1
        else:
            days_diff = (today - streak.last_visit_date).days
            if days_diff == 1:
                # Пришёл на следующий день — продолжаем стрик
                streak.streak_count += 1
            else:
                # Пропустил день — сбрасываем
                streak.streak_count = 1

        streak.last_visit_date = today
        streak.max_streak = max(streak.max_streak, streak.streak_count)

        await self.db.commit()

        milestone_reached = _check_milestone_reached(old_count, streak.streak_count)

        return TrackVisitResponse(
            streak_count=streak.streak_count,
            visited_today=False,
            milestone_reached=milestone_reached,
        )
