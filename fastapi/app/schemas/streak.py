from datetime import date

from pydantic import BaseModel


class StreakMilestone(BaseModel):
    """Порог стрика с наградой."""

    days: int
    bonus_rub: float
    achievement: str | None  # название ачивки если есть


class StreakResponse(BaseModel):
    """Текущий стрик пользователя с прогрессом до следующей награды."""

    streak_count: int  # текущий стрик в днях
    max_streak: int  # рекорд
    last_visit_date: date | None
    next_milestone: StreakMilestone | None  # следующий порог
    days_until_next: int | None  # дней до следующей награды
    visited_today: bool  # уже зашёл сегодня


class TrackVisitResponse(BaseModel):
    """Ответ на трекинг визита."""

    streak_count: int
    visited_today: bool  # True если уже был сегодня
    milestone_reached: StreakMilestone | None  # достигнутый порог если есть
