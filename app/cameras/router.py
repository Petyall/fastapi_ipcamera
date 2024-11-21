from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, status

from app.users.services import UserService
from app.cameras.utils import parse_rtsp_url
from app.users.schemas import User as UserSchema
from app.stream.url_encryption import encrypt_stream_url, decrypt_stream_url
from app.authorization.dependencies import get_current_user, check_is_current_user_admin
from app.cameras.services import CameraService, UserCameraService, UserFavoriteCameraService
from app.cameras.schemas import CameraCreate, CameraUpdate, CameraPublic, UserCameraBase, URLStreamDetails, CameraAdmin
from app.cameras.responses import CamerasResponse, CameraResponse, UserCamerasResponse, AdminCamerasResponse
from app.exceptions import (
    UserAlreadyHasAccessToThisCameraException,
    UserCamerasNotFoundException, 
    UserCameraNotFoundException, 
    UserFavoriteCamerasNotFoundException, 
    UserAlreadyHasThisFavoriteCameraException,
    UserNotFoundException,
    CameraHasForeignKeysException
    )


router = APIRouter(
    prefix="/cameras",
    tags=["Работа с камерами"],
)


@router.post("/", response_model=CamerasResponse, status_code=status.HTTP_201_CREATED)
async def add_camera(camera_data: CameraCreate, current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Добавление камеры (у пользователя должна быть роль администратора и выше)
    """
    encrypted_stream_url = encrypt_stream_url(camera_data.stream_url)
    
    await CameraService.add(name=camera_data.name, stream_url=encrypted_stream_url, location=camera_data.location)
    cameras = await CameraService.find_all()

    return {"cameras": cameras}


@router.get("/all", response_model=AdminCamerasResponse, status_code=status.HTTP_200_OK)
async def get_all_cameras(current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Получение всех камер (у пользователя должна быть роль администратора и выше)
    """
    cameras = await CameraService.find_all()

    cameras_list = []
    for camera in cameras:
        decrypted_url = decrypt_stream_url(camera.stream_url)
        parsed_url = parse_rtsp_url(decrypted_url)
        if parsed_url:

            stream_details = URLStreamDetails(
                stream_type="rtsp",
                user=parsed_url["user"],
                password="*" * len(parsed_url["password"]),
                url=parsed_url["url"],
                port=int(parsed_url["port"]),
                args=parsed_url["args"],
            )

            cameras_list.append(CameraAdmin(
                id=camera.id,
                name=camera.name,
                stream_url=[stream_details],
                location=camera.location
            ))
        else:
            cameras_list.append(CameraAdmin(
                id=camera.id,
                name=camera.name,
                stream_url=decrypted_url,
                location=camera.location
            ))    

    return {"cameras": cameras_list}


@router.get("/{camera_id}", response_model=CameraResponse, status_code=status.HTTP_200_OK)
async def get_camera_by_id(camera_id: int, current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Получение камеры по её ID (у пользователя должна быть роль администратора и выше)
    """
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    return {"camera": camera}


@router.get("/users/{user_id}", response_model=UserCamerasResponse, status_code=status.HTTP_200_OK)
async def get_all_cameras_by_user(user_id: UUID, current_user: UserSchema = Depends(check_is_current_user_admin)):  
    """
    Получение камер, закрепленных за пользователем (должна быть роль администратора и выше)
    """ 
    cameras = await UserCameraService.find_all(user_id=user_id)
    if not cameras:
        raise UserCamerasNotFoundException
    
    return {"cameras": cameras}


@router.delete("/{camera_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_camera(camera_id: int, confirm: bool = False, current_user: UserSchema = Depends(check_is_current_user_admin)) -> dict:
    """
    Удаление камеры (у пользователя должна быть роль администратора и выше).
    Если камера связана с другими записями, будет предложено подтверждение на удаление всех связанных записей.
    """
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException

    user_cameras = await UserCameraService.find_all(camera_id=camera_id)
    favorite_cameras = await UserFavoriteCameraService.find_all(camera_id=camera_id)

    if user_cameras or favorite_cameras:
        if not confirm:
            raise CameraHasForeignKeysException
        
        await UserCameraService.delete_all(camera_id=camera_id)
        await UserFavoriteCameraService.delete_all(camera_id=camera_id)

    await CameraService.delete(id=camera_id)

    return {"success": True}


@router.patch("/{camera_id}", response_model=dict|CameraPublic, status_code=status.HTTP_200_OK)
async def edit_camera(camera_id: int, camera_data: CameraUpdate, current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Редактирование камеры (у пользователя должна быть роль администратора и выше)
    """
    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    update_data = {k: v for k, v in camera_data.dict(exclude_unset=True).items() if v != ""}
    
    if not update_data:
        return {"detail": "Нет данных для обновления"}
    
    update_data['updated_at'] = datetime.utcnow()

    if update_data['stream_url']:
        update_data['stream_url'] = encrypt_stream_url(update_data['stream_url'])

    updated_camera = await CameraService.update(id=camera_id, **update_data)

    if updated_camera:
        camera = await CameraService.find_by_id(camera_id)
        return camera
    else:
        return {"success": False}


@router.post("/user/add_camera", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_camera_to_user(camera_data: UserCameraBase, current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Открытие доступа к камере пользователю
    """
    user_camera = await UserCameraService.find_one_or_none(camera_id=camera_data.camera_id, user_id=camera_data.user_id)
    if user_camera:
        raise UserAlreadyHasAccessToThisCameraException

    user = await UserService.find_one_or_none(id=camera_data.user_id)
    if not user:
        raise UserNotFoundException
    
    camera = await CameraService.find_one_or_none(id=camera_data.camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    await UserCameraService.add(camera_id=camera_data.camera_id, user_id=camera_data.user_id)
    return {"success": True}


@router.post("/user/delete_camera", response_model=dict, status_code=status.HTTP_201_CREATED)
async def delete_camera_from_user(camera_data: UserCameraBase, current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Открытие доступа к камере пользователю
    """
    user_camera = await UserCameraService.find_one_or_none(camera_id=camera_data.camera_id, user_id=camera_data.user_id)
    if not user_camera:
        raise UserCameraNotFoundException
    
    await UserCameraService.delete(camera_id=camera_data.camera_id, user_id=camera_data.user_id)
    return {"success": True}


@router.get("/user/all", response_model=CamerasResponse, status_code=status.HTTP_200_OK)
async def get_all_user_cameras(current_user: UserSchema = Depends(get_current_user)):
    """
    Все камеры, закрепленные за пользователем
    """
    user_cameras = await UserCameraService.find_all(user_id=current_user.id)
    if not user_cameras:
        raise UserCamerasNotFoundException

    cameras = []
    for camera in user_cameras:
        cameras.append(await CameraService.find_by_id(int(camera.camera_id)))
        
    return {"cameras": cameras}


@router.get("/user/{camera_id}", response_model=CameraResponse, status_code=status.HTTP_200_OK)
async def get_user_camera_by_id(camera_id: int, current_user: UserSchema = Depends(get_current_user)):
    """
    Получение камеры, закрепленной за пользователем по её ID
    """
    user_camera = await UserCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not user_camera:
        raise UserCameraNotFoundException
    
    camera = await CameraService.find_one_or_none(id=user_camera.camera_id)
    return {"camera": camera}


@router.post("/favorite", response_model= dict, status_code=status.HTTP_201_CREATED)
async def add_camera_to_favorite(camera_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    """
    Добавление пользователем камеры в избранное (добавиться могут только те, которые закреплены за пользователем)
    """
    camera = await UserCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not camera:
        raise UserCameraNotFoundException
    
    favorite_camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if favorite_camera:
        raise UserAlreadyHasThisFavoriteCameraException

    await UserFavoriteCameraService.add(user_id=current_user.id, camera_id=camera_id)
    return {"success": True}


@router.get("/favorite/all", response_model=CamerasResponse, status_code=status.HTTP_200_OK)
async def get_all_favorite_user_cameras(current_user: UserSchema = Depends(get_current_user)):
    """
    Все избранные камеры пользователя (выводятся только те, которые закреплены за пользователем и были добавлены им в избранное)
    """
    user_favorite_cameras = await UserFavoriteCameraService.find_all(user_id=current_user.id)
    if not user_favorite_cameras:
        raise UserFavoriteCamerasNotFoundException
    
    cameras = []
    for camera in user_favorite_cameras:
        cameras.append(await CameraService.find_by_id(int(camera.camera_id)))

    return {"cameras": cameras}


@router.get("/favorite/{camera_id}", response_model=CameraResponse, status_code=status.HTTP_200_OK)
async def get_favorite_user_camera_by_id(camera_id: int, current_user: UserSchema = Depends(get_current_user)):
    """
    Получение избранной камеры пользователя по её ID (если пользователь введёт камеру, которая не закреплена за ним, то ничего не выведется в ответ)
    """
    user_favorite_camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not user_favorite_camera:
        raise UserCameraNotFoundException
    
    camera = await CameraService.find_one_or_none(id=user_favorite_camera.camera_id)

    return {"camera": camera}


@router.post("/favorite/delete", response_model= dict, status_code=status.HTTP_200_OK)
async def delete_camera_from_favorite(camera_id: int, current_user: UserSchema = Depends(get_current_user)) -> dict:
    """
    Удаление пользователем камеры из избранного
    """
    favorite_camera = await UserFavoriteCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not favorite_camera:
        raise UserCameraNotFoundException

    await UserFavoriteCameraService.delete(user_id=current_user.id, camera_id=camera_id)
    return {"success": True}
