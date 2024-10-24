import pandas as pd

from datetime import datetime
from fastapi import APIRouter, status, UploadFile, File, Depends

from app.models import Camera
from app.cameras.services import CameraService
from app.users.schemas import User as UserSchema
from app.stream.url_encryption import encrypt_stream_url
from app.authorization.dependencies import check_is_current_user_admin
from app.exceptions import IncorrectFileTypeException, IncorrectFileDataException, ImportDataException


router = APIRouter(
    prefix="/import",
    tags=["Импортирование данных"],
)


@router.post(path="/cameras", response_model=dict, status_code=status.HTTP_201_CREATED)
async def cameras_importer(file: UploadFile = File(...), current_user: UserSchema = Depends(check_is_current_user_admin)):
    """
    Импортирование камер из excel файла
    """
    if file.content_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        raise IncorrectFileTypeException

    try:
        df = pd.read_excel(file.file, engine='openpyxl')

        required_columns = ['id', 'name', 'stream_url', 'location', 'created_at', 'updated_at']
        if not all(column in df.columns for column in required_columns):
            raise IncorrectFileDataException

        cameras_to_insert = []
        for _, row in df.iterrows():
            camera = Camera(
                id=row['id'],
                name=row['name'],
                stream_url=encrypt_stream_url(row['stream_url']),
                location=row['location'],
                created_at=pd.to_datetime(row['created_at']).to_pydatetime() if not pd.isnull(row['created_at']) else datetime.utcnow(),
                updated_at=pd.to_datetime(row['updated_at']).to_pydatetime() if not pd.isnull(row['updated_at']) else datetime.utcnow()
            )
            cameras_to_insert.append(camera)

        await CameraService.import_cameras(cameras_to_insert)
        
        return {"success": True, "message": f"Импортировано {len(cameras_to_insert)} камер."}

    except Exception as e:
        raise ImportDataException(str(e))
    