import os
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.schemas.auth import Token
from jose import jwt
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Хэшер паролей — используем рекомендованные настройки pwdlib (bcrypt)
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа


def get_password_hash(password: str) -> str:
    """Хеширование пароля через pwdlib/bcrypt."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля. Возвращает False при любой ошибке."""
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """Создаёт JWT-токен с временем жизни ACCESS_TOKEN_EXPIRE_MINUTES."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Ищет пользователя по email и проверяет пароль."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_access_token(self, user: User) -> Token:
        """Генерирует токен для авторизованного пользователя."""
        access_token = create_access_token({"sub": user.email})
        return Token(access_token=access_token, token_type="bearer")
