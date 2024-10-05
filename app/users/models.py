from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserRole:
    USER = 'USER'
    ADMIN = 'ADMIN'
    ROOT = 'ROOT'

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    paternal_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, default='000-000-0000')
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ban = Column(Boolean, default=False)

    cameras = relationship("UserCamera", back_populates="user")
    favorite_cameras = relationship("FavoriteCamera", back_populates="user")

    def __str__(self):
        return f"User {self.email}"


class Camera(Base):
    __tablename__ = 'cameras'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    stream_url = Column(String, nullable=False)
    location = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("UserCamera", back_populates="camera")
    favorites = relationship("FavoriteCamera", back_populates="camera")

    def __str__(self):
        return f"Camera {self.name}"

class UserCamera(Base):
    __tablename__ = 'user_cameras'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), primary_key=True)

    user = relationship("User", back_populates="cameras")
    camera = relationship("Camera", back_populates="users")

    UniqueConstraint(user_id, camera_id)

    def __str__(self):
        return f"UserCamera: User {self.user_id} - Camera {self.camera_id}"

class FavoriteCamera(Base):
    __tablename__ = 'favorite_cameras'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'), primary_key=True)

    user = relationship("User", back_populates="favorite_cameras")
    camera = relationship("Camera", back_populates="favorites")

    UniqueConstraint(user_id, camera_id)

    def __str__(self):
        return f"FavoriteCamera: User {self.user_id} - Camera {self.camera_id}"
