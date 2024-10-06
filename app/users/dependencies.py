from datetime import datetime
from jose import jwt, JWTError
from fastapi import Request, Depends

from app.config import settings
from app.users.models import User
from app.users.services import UserService
from app.exceptions import TokenAbsentException, IncorrectFormatTokenException, TokenExpiredException, UserIsNotPresentException, NotEnoughAuthorityException


async def get_token(request: Request) -> str:
    """
    Получение токена из cookie запроса.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise TokenAbsentException
    return token


async def get_refresh_token(request: Request) -> str:
    """
    Получение рефреш-токена из cookie запроса.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise TokenAbsentException
    return token


async def get_uuid(email: str) -> str:
    """
    Получение UUID пользователя по email.
    """
    user = await UserService.find_one_or_none(email=email)
    if not user:
        raise UserIsNotPresentException 
    return user.id


async def get_current_user(token: str = Depends(get_token)) -> User:
    """
    Получение текущего пользователя по токену.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHM)
    except JWTError:
        raise IncorrectFormatTokenException

    expire: str = payload.get("exp")
    if not expire or datetime.utcnow().timestamp() > expire:
        raise TokenExpiredException

    user_id: str = payload.get("sub")
    if not user_id:
        raise UserIsNotPresentException 

    user = await UserService.find_by_id(user_id)
    if not user:
        raise UserIsNotPresentException  

    return user


async def check_current_user_and_role(user: User = Depends(get_current_user)):
    """
    Проверка роли текущего пользователя. Возвращает пользователя, если у него достаточно прав.
    """
    if user.role != "USER":
        raise NotEnoughAuthorityException
    return user
