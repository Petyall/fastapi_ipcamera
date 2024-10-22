from typing import List
from pydantic import BaseModel

from app.cameras.schemas import Camera, UserCameraBase, FavoriteCameraBase


class CameraResponse(BaseModel):
    camera: Camera


class CamerasResponse(BaseModel):
    cameras: List[Camera]


class UserCamerasResponse(BaseModel):
    cameras: List[UserCameraBase]


class UserFavoritesCamerasResponse(BaseModel):
    cameras: List[FavoriteCameraBase]