from app.services import BaseRequests
from app.database import async_session_maker
from app.models import Camera, UserCamera, FavoriteCamera

from sqlalchemy import delete


class CameraService(BaseRequests):
    model = Camera


class UserCameraService(BaseRequests):
    model = UserCamera


class UserFavoriteCameraService(BaseRequests):
    model = FavoriteCamera

    @classmethod
    async def delete(cls, user_id, camera_id):
        """Удаление объектов"""
        async with async_session_maker() as session:
            async with session.begin():
                query = delete(cls.model).where(cls.model.user_id == user_id, cls.model.camera_id == camera_id)
                await session.execute(query)
                await session.commit()
