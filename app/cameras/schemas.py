from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class CameraBase(BaseModel):
    name: str
    stream_url: str
    location: str


class CameraCreate(CameraBase):
    pass


class Camera(CameraBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    stream_url: Optional[str] = None


class UserCameraBase(BaseModel):
    user_id: UUID
    camera_id: int

    class Config:
        orm_mode = True


class UserCamera(UserCameraBase):
    pass


class FavoriteCameraBase(BaseModel):
    camera_id: int

    class Config:
        orm_mode = True


class FavoriteCameraAdd(FavoriteCameraBase):
    pass


class FavoriteCameraDelete(FavoriteCameraBase):
    pass


class FavoriteCamera(FavoriteCameraBase):
    user_id: UUID
