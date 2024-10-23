from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class CameraCreate(BaseModel):
    name: str
    stream_url: str
    location: str


class CameraPublic(BaseModel):
    id: int
    name: str
    location: str

    class Config:
        orm_mode = True


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    location: Optional[str] = None

    class Config:
        orm_mode = True


class UserCameraBase(BaseModel):
    user_id: UUID
    camera_id: int

    class Config:
        orm_mode = True


class FavoriteCameraBase(BaseModel):
    camera_id: int

    class Config:
        orm_mode = True
