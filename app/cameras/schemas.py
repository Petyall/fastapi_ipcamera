from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    user_id: UUID
    camera_id: int

    class Config:
        orm_mode = True


class FavoriteCamera(FavoriteCameraBase):
    pass
