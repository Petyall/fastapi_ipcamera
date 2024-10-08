from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    paternal_name: str
    phone_number: str = Field(default='000-000-0000')


class UserCreate(UserBase):
    role: str = Field(default='USER')
    password: str


class UserUpdate(UserBase):
    role: str
    password: str
    ban: str
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: UUID
    role: str
    ban: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
