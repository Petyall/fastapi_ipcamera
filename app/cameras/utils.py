import re


def parse_rtsp_url(rtsp_url: str) -> dict:
    """
    Парсинг RTSP URL в словарь с компонентами (тип, пользователь, пароль, адрес, порт, аргументы).
    """
    pattern = r"(?P<stream_type>[^://]+)://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<url>[^:/]+):(?P<port>\d+)(?P<args>/.*)"
    match = re.match(pattern, rtsp_url)
    if match:
        return match.groupdict()
    else:
        return False
