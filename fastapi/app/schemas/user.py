from app.models.user import FinancialSegment
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Публичные данные пользователя — без пароля."""

    id: int
    email: EmailStr
    phone_number: str
    full_name: str
    financial_segment: FinancialSegment

    model_config = {"from_attributes": True}


class UserListItem(BaseModel):
    """Краткая информация для списка выбора тестового пользователя."""

    id: int
    full_name: str
    email: EmailStr
    financial_segment: FinancialSegment

    model_config = {"from_attributes": True}
