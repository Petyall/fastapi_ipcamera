from sqlalchemy import delete

from app.services import BaseRequests
from app.database import async_session_maker
from app.models import Camera, UserCamera, FavoriteCamera


class CameraService(BaseRequests):
    model = Camera


class UserCameraService(BaseRequests):
    model = UserCamera

    @classmethod
    async def delete(cls, user_id, camera_id):
        """Удаление объектов"""
        async with async_session_maker() as session:
            async with session.begin():
                query = delete(cls.model).where(cls.model.user_id == user_id, cls.model.camera_id == camera_id)
                await session.execute(query)
                await session.commit()


    @classmethod
    async def delete_all(cls, camera_id: int):
        """Удаление всех объектов, связанных с данной камерой"""
        async with async_session_maker() as session:
            async with session.begin():
                query = delete(cls.model).where(cls.model.camera_id == camera_id)
                await session.execute(query)
                await session.commit()


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


    @classmethod
    async def delete_all(cls, camera_id: int):
        """Удаление всех объектов, связанных с данной камерой"""
        async with async_session_maker() as session:
            async with session.begin():
                query = delete(cls.model).where(cls.model.camera_id == camera_id)
                await session.execute(query)
                await session.commit()
