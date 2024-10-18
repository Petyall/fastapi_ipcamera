from jose import jwt
from pydantic import EmailStr
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.models import User
from app.config import settings
from app.users.services import UserService


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Возврат хэшированного пароля
    """
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    """
    Проверка пароля на совпадение
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    """
    Создание JWT токена с указанными данными и временем жизни.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)) -> str:
#     """
#     Создание JWT refresh токена с указанными данными и временем жизни.
#     """
#     to_encode = data.copy()
#     expire = datetime.utcnow() + expires_delta
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
#     return encoded_jwt


async def authenticate_user(email: EmailStr, password: str) -> User | None:
    """
    Аутентификация пользователя по email и паролю.
    Возвращает пользователя, если аутентификация успешна, иначе None.
    """
    user = await UserService.find_one_or_none(email=email)
    if user and verify_password(password, user.password):
        return user
    return None
