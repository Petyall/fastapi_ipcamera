import jwt

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.users.services import UserService
from app.users.schemas import UserCreate, UserLogin, User as UserSchema
from app.users.dependencies import get_current_user, get_refresh_token, check_is_current_user_root
from app.users.authorization import (
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
    UniquePhoneNumberException
)


router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация и пользователи"],
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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True
    )

    return {"message": f"Пользователь {user_data.email} успешно авторизован"}


@router.post("/refresh_token", response_model=dict, status_code=status.HTTP_200_OK)
async def refresh_token(response: Response, refresh_token: str = Depends(get_refresh_token)) -> dict:
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


@router.get("/me", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def read_users_me(current_user: UserSchema = Depends(get_current_user)):
    """
    Получение информации о пользователе
    """
    return current_user


@router.get("/all", response_model=list[UserSchema], status_code=status.HTTP_200_OK)
async def read_users_all(current_user: UserSchema = Depends(check_is_current_user_root)):
    """
    Получение информации обо всех пользователях
    """
    return await UserService.find_all()
