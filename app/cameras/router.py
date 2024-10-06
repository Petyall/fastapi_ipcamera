from fastapi import APIRouter, Depends, Response, status
from app.cameras.schemas import UserCameraBase, FavoriteCameraBase, CameraCreate, CameraBase, CameraUpdate, Camera
from app.users.schemas import User as UserSchema
from app.users.dependencies import get_current_user, check_is_current_user_admin
from app.cameras.services import CameraService, UserCameraService, UserFavoriteCameraService
from app.exceptions import UserCamerasNotFoundException, UserCameraNotFoundException, UserFavoriteCamerasNotFoundException, UserAlreadyHasThisFavoriteCameraException

from datetime import datetime
from uuid import UUID

router = APIRouter(
    prefix="/cameras",
    tags=["Работа с камерами"],
)


@router.get("/user/all", response_model=list[UserCameraBase], status_code=status.HTTP_200_OK)
async def get_all_user_cameras(current_user: UserSchema = Depends(get_current_user)):
    cameras = await UserCameraService.find_all(user_id=current_user.id)
    if not cameras:
        raise UserCamerasNotFoundException
    return cameras


@router.get("/user/{camera_id}", response_model=UserCameraBase, status_code=status.HTTP_200_OK)
async def get_user_camera_by_id(camera_id: int, current_user: UserSchema = Depends(get_current_user)):
    camera = await UserCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    return camera


@router.get("/favorite/all", response_model=list[FavoriteCameraBase], status_code=status.HTTP_200_OK)
async def get_all_favorite_user_cameras(current_user: UserSchema = Depends(get_current_user)):
    cameras = await UserFavoriteCameraService.find_all(user_id=current_user.id)
    if not cameras:
        raise UserFavoriteCamerasNotFoundException
    return cameras


@router.get("/favorite/{camera_id}", response_model=FavoriteCameraBase, status_code=status.HTTP_200_OK)
async def get_favorite_user_camera_by_id(camera_id: int, current_user: UserSchema = Depends(get_current_user)):
    camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    return camera


@router.post("/favorite", response_model= dict, status_code=status.HTTP_201_CREATED)
async def add_camera_to_favorite(camera_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    camera = await UserCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    favorite_camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if favorite_camera:
        raise UserAlreadyHasThisFavoriteCameraException

    await UserFavoriteCameraService.add(user_id=current_user.id, camera_id=camera_id)
    return {"message": f"Пользователь '{current_user.email}' успешно добавил в избранное камеру {camera_id}"}


@router.delete("/favorite", response_model= dict, status_code=status.HTTP_200_OK)
async def delete_camera_from_favorite(camera_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    favorite_camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not favorite_camera:
        raise UserCameraNotFoundException

    await UserFavoriteCameraService.delete(user_id=current_user.id, camera_id=camera_id)
    return {"message": f"Пользователь '{current_user.email}' успешно удалил из избранного камеру {camera_id}"}


@router.post("/", response_model = dict, status_code=status.HTTP_201_CREATED)
async def add_camera(camera_data: CameraCreate, current_user: UserSchema = Depends(check_is_current_user_admin)):
    camera = await CameraService.add(
        name=camera_data.name,
        stream_url=camera_data.stream_url,
        location=camera_data.location,
    )
    return {"message": f"Камера успешно создана"}

@router.delete("/{camera_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_camera(camera_id: int, current_user: UserSchema = Depends(check_is_current_user_admin)) -> dict:
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    await CameraService.delete(id=camera_id)
    return {"message": f"Камера с ID {camera_id} успешно удалена пользователем {current_user.email}"}

@router.patch("/{camera_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def edit_camera(camera_id: int, camera_data: CameraUpdate, current_user: UserSchema = Depends(check_is_current_user_admin)):
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    update_data = {k: v for k, v in camera_data.dict(exclude_unset=True).items() if v != ""}
    
    if not update_data:
        return {"message": "Нет данных для обновления"}
    
    update_data['updated_at'] = datetime.utcnow()

    updated_camera = await CameraService.update(id=camera_id, **update_data)

    return {"message": f"Камера с ID {camera_id} успешно отредактирована пользователем {current_user.email}"}

@router.get("/all", response_model=list[Camera], status_code=status.HTTP_200_OK)
async def get_all_cameras(current_user: UserSchema = Depends(check_is_current_user_admin)):
    cameras = await CameraService.find_all()
    return cameras


@router.get("/{camera_id}", response_model=Camera, status_code=status.HTTP_200_OK)
async def get_camera_by_id(camera_id: int, current_user: UserSchema = Depends(check_is_current_user_admin)):
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    return camera


@router.get("/users/{user_id}", response_model=list[UserCameraBase], status_code=status.HTTP_200_OK)
async def get_cameras_by_user(user_id: UUID, current_user: UserSchema = Depends(check_is_current_user_admin)):   
    cameras = await UserCameraService.find_all(user_id=user_id)
    if not cameras:
        raise UserCamerasNotFoundException
    return cameras
