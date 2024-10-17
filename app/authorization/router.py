import jwt

from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, Response, status

from app.config import settings
from app.users.services import UserService
from app.users.schemas import UserCreate, UserLogin, User as UserSchema
from app.authorization.dependencies import get_refresh_token, check_is_current_user_root
from app.authorization.authorization import (
    create_refresh_token,
    get_password_hash,
    authenticate_user,
    create_access_token,
)
from app.exceptions import (
    IncorrectFormatTokenException,
    UserAlreadyExistsException,
    UserIsNotPresentException,
    IncorrectEmailOrPasswordException,
    UniquePhoneNumberException,
)


router = APIRouter(
    prefix="/authorization",
    tags=["Аутентификация"],
)


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, current_user: UserSchema = Depends(check_is_current_user_root)) -> dict:
    """
    Регистрация пользователя
    """
    existing_user = await UserService.find_one_or_none(email=user_data.email)
    if existing_user:
        raise UserAlreadyExistsException

    hashed_password = get_password_hash(user_data.password)
    try:
        await UserService.add(
            email=user_data.email,
            password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            paternal_name=user_data.paternal_name,
            phone_number=user_data.phone_number,
        )
    except IntegrityError:
        raise UniquePhoneNumberException
    
    return {"message": f"Пользователь '{user_data.first_name} {user_data.last_name}' успешно создан"}


@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login_user(response: Response, user_data: UserLogin) -> dict:
    """
    Авторизация пользователя
    """
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise IncorrectEmailOrPasswordException

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # response.set_cookie(
    #     key="access_token",
    #     value=access_token,
    #     httponly=True
    # )
    # response.set_cookie(
    #     key="refresh_token",
    #     value=refresh_token,
    #     httponly=True
    # )

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh_token", response_model=dict, status_code=status.HTTP_200_OK)
async def refresh_token(response: Response, refresh_token: str = Depends(get_refresh_token)) -> dict:
    """
    Обновление access токена
    """
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.JWTError:
        raise IncorrectFormatTokenException

    user_id: str = payload.get("sub")
    if not user_id:
        raise UserIsNotPresentException

    user = await UserService.find_by_id(user_id)
    if not user:
        raise UserIsNotPresentException

    access_token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True
    )
    return {"message": "Access токен успешно обновлен."}


@router.post("/logout", response_model=dict, status_code=status.HTTP_200_OK)
async def logout_user(response: Response) -> dict:
    """
    Выход пользователя
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "До свидания!"}
