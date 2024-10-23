from fastapi import HTTPException, status


class ProjectException(HTTPException):
    status_code = 500
    detail = ""
    
    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class UserAlreadyExistsException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="Пользователь уже существует"


class UniquePhoneNumberException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="Пользователь с данным номером телефона уже существует"


class UserNotFoundException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Пользователь не найден"


class UserIsNotPresentException(ProjectException):
    status_code=status.HTTP_401_UNAUTHORIZED


class UserIsBannedException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Пользователь был забанен"


class NotEnoughAuthorityException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="У данного пользователя недостаточно прав"


class TokenExpiredException(ProjectException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Истек срок действия токена"


class TokenAbsentException(ProjectException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Токен отсутствует"


class IncorrectFormatTokenException(ProjectException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверный формат токена"


class IncorrectEmailOrPasswordException(ProjectException):
    status_code=status.HTTP_401_UNAUTHORIZED
    detail="Неверная почта или пароль"


class UserCamerasNotFoundException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="У данного пользователя не найдены камеры"


class UserAlreadyHasAccessToThisCameraException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="У данного пользователя уже есть доступ к этой камере"


class CameraNotFoundException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Камера с таким ID не найдена либо доступ к ней запрещен"


class UserCameraNotFoundException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="Камера с таким ID не найдена"


class UserFavoriteCamerasNotFoundException(ProjectException):
    status_code=status.HTTP_404_NOT_FOUND
    detail="У данного пользователя не найдены избранные камеры"


class UserAlreadyHasThisFavoriteCameraException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="Пользователь уже добавил эту камеру в избранное"


class UnexpectedErrorException(ProjectException):
    status_code=status.HTTP_400_BAD_REQUEST
    detail="Неизвестная ошибка"


class IncorrectUserUpdateDataException(ProjectException):
    status_code=status.HTTP_409_CONFLICT
    detail="Введенные данные не соответствуют необходимому формату"
