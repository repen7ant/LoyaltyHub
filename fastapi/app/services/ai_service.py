import os

import anthropic
from app.models.user import User
from app.schemas.loyalty import LoyaltyForecast, LoyaltySummary
from app.schemas.offer import OfferResponse

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """
Ты персональный помощник по лояльности Т-Банка.
Твоя задача — дать короткий, конкретный и мотивирующий совет пользователю (2-3 предложения).
Используй данные о его накоплениях, прогнозе и доступных акциях.
Обращайся на "вы". Не упоминай технические детали (сегменты, ID и т.д.).
Пиши живо и по-человечески, как финансовый советник.
""".strip()


def _build_prompt(
    user: User,
    summary: LoyaltySummary,
    forecast: LoyaltyForecast,
    offers: list[OfferResponse],
) -> str:
    """Формирует промпт с данными пользователя для отправки в Claude."""
    top_offers = (
        ", ".join(
            f"{o.partner_name} ({o.cashback_percent}% кэшбэка)" for o in offers[:3]
        )
        or "нет доступных акций"
    )

    return f"""
Данные пользователя:
- Имя: {user.full_name}
- Накоплено рублей: {summary.total_rub} ₽
- Накоплено миль: {summary.total_miles}
- Накоплено баллов Браво: {summary.total_bravo}
- Общая выгода в рублях: {summary.total_equivalent_rub} ₽
- Прогноз на следующий месяц: ~{forecast.total_predicted_equivalent_rub} ₽

Топ акции партнёров доступные пользователю:
{top_offers}

Дай персональный совет как получить максимум выгоды.
""".strip()


class AIService:
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    async def get_recommendation(
        self,
        user: User,
        summary: LoyaltySummary,
        forecast: LoyaltyForecast,
        offers: list[OfferResponse],
    ) -> str:
        """
        Генерирует персонализированную рекомендацию через Claude API.
        Принимает данные о лояльности и офферах, возвращает текст совета.
        """
        prompt = _build_prompt(user, summary, forecast, offers)

        try:
            message = await self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude API error: {e}")
            return "Не удалось получить рекомендацию. Попробуйте позже."
