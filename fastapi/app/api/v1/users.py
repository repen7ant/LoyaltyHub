from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserListItem, UserResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserListItem])
async def list_users(db: AsyncSession = Depends(get_db)):
    """
    Список всех тестовых пользователей.
    Используется как стартовая точка — выбор пользователя перед входом.
    """
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Возвращает данные текущего авторизованного пользователя."""
    return current_user
