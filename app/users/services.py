from sqlalchemy import select, insert, update

from app.models import User
from app.services import BaseRequests


class UserService(BaseRequests):
    model = User
    