from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    paternal_name: str
    phone_number: str = Field(default='000-000-0000')  # Значение по умолчанию


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: UUID  # Изменено на UUID
    role: str
    ban: bool
    created_at: datetime  # Если нужно время создания в формате строки
    updated_at: datetime  # Если нужно время обновления в формате строки

    class Config:
        orm_mode = True


class CameraBase(BaseModel):
    name: str
    stream_url: str
    location: str


class CameraCreate(CameraBase):
    pass


class Camera(CameraBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True


class UserCameraBase(BaseModel):
    user_id: UUID
    camera_id: int


class UserCamera(UserCameraBase):
    pass


class FavoriteCameraBase(BaseModel):
    user_id: UUID
    camera_id: int


class FavoriteCamera(FavoriteCameraBase):
    pass
