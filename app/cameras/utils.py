import re

from app.cameras.schemas import CameraAdmin, URLStreamDetails
from app.stream.url_encryption import decrypt_stream_url, encrypt_stream_url


def parse_rtsp_url(rtsp_url: str) -> dict:
    """
    Парсинг RTSP URL в словарь с компонентами (тип, пользователь, пароль, адрес, порт, аргументы)
    """
    pattern = r"(?P<stream_type>[^://]+)://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<url>[^:/]+):(?P<port>\d+)(?P<args>/.*)"
    match = re.match(pattern, rtsp_url)
    if match:
        return match.groupdict()
    else:
        return False
    

def build_rtsp_url(rtsp_dict: dict) -> str:
    """
    Создание RTSP URL из отдельных компонентов (тип, пользователь, пароль, адрес, порт, аргументы)
    """
    new_url = f"{rtsp_dict['stream_type']}://{rtsp_dict['user']}:{rtsp_dict['password']}@{rtsp_dict['url']}:{rtsp_dict['port']}{rtsp_dict['args']}"
    return new_url


async def handle_stream_url(new_stream_url, old_stream_url):
    """
    Обработка stream_url: шифрование строк или обновление параметров.
    """
    if isinstance(new_stream_url, str):
        return encrypt_stream_url(new_stream_url)
    elif isinstance(new_stream_url, list) and all(isinstance(item, dict) for item in new_stream_url):
        decrypted_url = decrypt_stream_url(old_stream_url)
        old_url = parse_rtsp_url(decrypted_url)

        for item in new_stream_url:
            filtered_item = {key: value for key, value in item.items() if value}
            for key, value in filtered_item.items():
                if key in old_url:
                    old_url[key] = value

        new_url = build_rtsp_url(old_url)
        return encrypt_stream_url(new_url)

    raise ValueError("Некорректный формат stream_url")


def format_camera(camera) -> CameraAdmin:
    """
    Форматирование одного объекта камеры
    """
    decrypted_url = decrypt_stream_url(camera.stream_url)
    parsed_url = parse_rtsp_url(decrypted_url)

    if parsed_url:
        stream_details = URLStreamDetails(
            stream_type=parsed_url["stream_type"],
            user=parsed_url["user"],
            password="*" * len(parsed_url["password"]),
            url=parsed_url["url"],
            port=int(parsed_url["port"]),
            args=parsed_url["args"],
        )
        stream_url = [stream_details]
    else:
        stream_url = decrypted_url

    return CameraAdmin(
        id=camera.id,
        name=camera.name,
        stream_url=stream_url,
        location=camera.location
    )


def cameras_list_formatter(cameras: list) -> list:
    """
    Форматирование списка камер
    """
    cameras_list = []
    for camera in cameras:
        cameras_list.append(format_camera(camera))
    return cameras_list
