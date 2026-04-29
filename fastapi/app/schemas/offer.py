from app.models.user import FinancialSegment
from pydantic import BaseModel, ConfigDict


class OfferResponse(BaseModel):
    id: int
    partner_name: str
    short_description: str
    logo_url: str
    brand_color_hex: str
    cashback_percent: float
    financial_segment: FinancialSegment

    # Разрешаем Pydantic читать данные напрямую из SQLAlchemy моделей
    model_config = ConfigDict(from_attributes=True)
