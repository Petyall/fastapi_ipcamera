from typing import List
from pydantic import BaseModel

from app.cameras.schemas import CameraPublic, UserCameraBase, FavoriteCameraBase, CameraAdmin


class CameraResponse(BaseModel):
    camera: CameraPublic


class CamerasResponse(BaseModel):
    cameras: List[CameraPublic]


class AdminCameraResponse(BaseModel):
    cameras: CameraAdmin


class AdminCamerasResponse(BaseModel):
    cameras: List[CameraAdmin]


class UserCamerasResponse(BaseModel):
    cameras: List[UserCameraBase]


class UserFavoritesCamerasResponse(BaseModel):
    cameras: List[FavoriteCameraBase]
    