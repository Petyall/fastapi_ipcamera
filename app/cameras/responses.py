from typing import List
from pydantic import BaseModel

from app.cameras.schemas import CameraPublic, UserCameraBase, FavoriteCameraBase


class CameraResponse(BaseModel):
    camera: CameraPublic


class CamerasResponse(BaseModel):
    cameras: List[CameraPublic]


class UserCamerasResponse(BaseModel):
    cameras: List[UserCameraBase]


class UserFavoritesCamerasResponse(BaseModel):
    cameras: List[FavoriteCameraBase]