from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, status

from app.users.services import UserService
from app.users.schemas import UserUpdate, User as UserSchema
from app.authorization.dependencies import get_current_user, check_is_current_user_root
from app.exceptions import (
    UserNotFoundException,
    IncorrectUserUpdateDataException
)


router = APIRouter(
    prefix="/users",
    tags=["Работа с пользователями"],
)


@router.get("/me", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user(current_user: UserSchema = Depends(get_current_user)):
    """
    Получение информации о пользователе
    """
    return current_user


@router.get("/all", response_model=list[UserSchema], status_code=status.HTTP_200_OK)
async def get_users_all(current_user: UserSchema = Depends(check_is_current_user_root)):
    """
    Получение информации обо всех пользователях
    """
    return await UserService.find_all()


@router.get("/{user_id}", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: UUID, current_user: UserSchema = Depends(check_is_current_user_root)):
    """
    Получение информации о пользователе по UUID
    """
    user = await UserService.find_one_or_none(id=user_id)
    if not user:
        raise UserNotFoundException
    
    return user


@router.patch("/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def edit_user(user_id: UUID, user_data: UserUpdate, current_user: UserSchema = Depends(check_is_current_user_root)):
    """
    Редактирование пользователя
    """
    user = await UserService.find_one_or_none(id=user_id)
    if not user:
        raise UserNotFoundException
    
    update_data = {k: v for k, v in user_data.dict(exclude_unset=True).items() if v != ""}

    if not update_data:
        return {"message": "Нет данных для обновления"}

    def str_to_bool(value: str) -> bool:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            raise IncorrectUserUpdateDataException

    if 'ban' in update_data:
        update_data['ban'] = str_to_bool(update_data['ban'])

    update_data['updated_at'] = datetime.utcnow()

    updated_user = await UserService.update(id=user_id, **update_data)

    return {"message": f"Пользователю с ID {user_id} успешно отредактированы поля {update_data}"}


@router.delete("/{user_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_user(user_id: UUID, current_user: UserSchema = Depends(check_is_current_user_root)):
    """
    Удаление пользователя
    """
    user = await UserService.find_one_or_none(id=user_id)
    if not user:
        raise UserNotFoundException
    
    await UserService.delete(id=user_id)

    return {"message": "Пользователь успешно удален"}
