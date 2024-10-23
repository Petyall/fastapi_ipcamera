import cv2

from starlette.responses import StreamingResponse
from fastapi import APIRouter, Depends, status

from app.users.schemas import User as UserSchema
from app.stream.url_encryption import decrypt_stream_url
from app.authorization.dependencies import get_current_user
from app.cameras.services import CameraService, UserCameraService
from app.exceptions import CameraNotFoundException, UserCameraNotFoundException, UnexpectedErrorException


router = APIRouter(
    prefix="/stream",
    tags=["Работа с потоком"],
)


def generate_frames(camera_url: str):
    """
    Генерирация кадров для передачи видеопотока
    """
    cap = cv2.VideoCapture(camera_url)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            

@router.get("/{camera_id}", status_code=status.HTTP_200_OK)
async def stream_camera(camera_id: int, current_user: UserSchema = Depends(get_current_user)):
    """
    Потоковое воспроизведение камеры, к которой у пользователя есть доступ
    """
    user_camera = await UserCameraService.find_one_or_none(user_id=current_user.id, camera_id=camera_id)
    if not user_camera:
        raise UserCameraNotFoundException

    camera = await CameraService.find_one_or_none(id=camera_id)
    if not camera:
        raise CameraNotFoundException
    
    try:
        decrypted_stream_url = decrypt_stream_url(camera.stream_url)
    except:
        raise UnexpectedErrorException

    return StreamingResponse(generate_frames(decrypted_stream_url), media_type='multipart/x-mixed-replace; boundary=frame')
