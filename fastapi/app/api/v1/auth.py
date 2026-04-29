from app.db.session import get_db
from app.schemas.auth import Token
from app.services.auth_service import AuthService
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    """
    Авторизация по email и паролю.
    Тестовые пользователи: пароль user_{id}, например user_1 для первого пользователя.
    """
    user = await service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return await service.create_access_token(user)
