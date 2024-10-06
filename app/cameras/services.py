from app.models import Camera, UserCamera, FavoriteCamera
from app.services import BaseRequests
from app.database import async_session_maker

from sqlalchemy import delete, update

class CameraService(BaseRequests):
    model = Camera

    @classmethod
    async def update(cls, id, **data):
        """Обновление объектов"""
        async with async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == id).values(**data)
            await session.execute(query)
            await session.commit()


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
