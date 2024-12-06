from typing import List
from pydantic import BaseModel

from app.users.schemas import User, UserPublic


class UserResponse(BaseModel):
    user: User


class UsersResponse(BaseModel):
    users: List[User]
