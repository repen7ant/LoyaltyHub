from app.models.base import Base
from app.models.user import FinancialSegment
from sqlalchemy import Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class Offer(Base):
    """
    Акция партнёра Т-Банка с повышенным кэшбэком.
    Акции фильтруются по финансовому сегменту пользователя —
    каждый пользователь видит только релевантные для него предложения.
    """

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,  # краткое описание партнёра для карточки оффера
    )
    logo_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,  # URL логотипа партнёра
    )
    brand_color_hex: Mapped[str] = mapped_column(
        String(7),
        nullable=False,  # HEX-цвет бренда для оформления карточки, пр. #2E86DE
    )
    cashback_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,  # процент кэшбэка у партнёра
    )
    financial_segment: Mapped[FinancialSegment] = mapped_column(
        Enum(FinancialSegment),
        nullable=False,  # сегмент пользователей которым показывается оффер
    )
