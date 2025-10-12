import uuid
from datetime import datetime, timedelta, timezone
from user_agents import parse
from enum import IntEnum


class MokError(Exception):
    pass


def gen_uuid() -> str:
    return uuid.uuid4().hex


def check_uuid(uid: str, version: int = 4):
    try:
        return uuid.UUID(uid).version == version
    except ValueError:
        return False


def get_device_info(request) -> dict:
    user_agent = parse(request.user_agent.string)
    return {
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'os': user_agent.os.family,
        'browser': user_agent.browser.family,
        'device_family': user_agent.device.family,
    }


class DeviceType(IntEnum):
    MOBILE = 1
    TABLET = 2
    DESKTOP = 3
    UNKNOWN = 4

    @classmethod
    def get_type(cls, request):
        device = get_device_info(request)
        if device['is_mobile']:
            return cls.MOBILE
        elif device['is_tablet']:
            return cls.TABLET
        elif device['is_pc']:
            return cls.DESKTOP
        else:
            return cls.UNKNOWN


MEDIA_PER_PAGE_CONFIG = {
    DeviceType.MOBILE: 15,
    DeviceType.TABLET: 25,
    DeviceType.DESKTOP: 30,
    DeviceType.UNKNOWN: 20
}

# pagination
PAGINATION_CONFIG = {
    DeviceType.MOBILE: {'left_edge': 1, 'left_current': 1, 'right_current': 2, 'right_edge': 2},
    DeviceType.TABLET: {'left_edge': 1, 'left_current': 1, 'right_current': 4, 'right_edge': 4},
    DeviceType.DESKTOP: {'left_edge': 3, 'left_current': 3, 'right_current': 6, 'right_edge': 6},
    DeviceType.UNKNOWN: {'left_edge': 1, 'left_current': 1, 'right_current': 4, 'right_edge': 4},
}


class ProviderType(IntEnum):
    LOCAL = 1
    SIGNED = 2
    DIRECT = 3

    @classmethod
    def get_type(cls, name):
        return _PROVIDER_TYPE_MAP.get(name, cls.DIRECT)


# 注意：云服务商的名字要和_PROVIDER_TYPE_MAP给出的SIGNED类型名字保持一致
# Note: These names must match the keys in _PROVIDER_TYPE_MAP
CLOUD_CDN_NAME = ['腾讯云', '阿里云']

_PROVIDER_TYPE_MAP = {
    '本站': ProviderType.LOCAL,
    'loc': ProviderType.LOCAL,
    'local': ProviderType.LOCAL,
    '腾讯云': ProviderType.SIGNED,
    '阿里云': ProviderType.SIGNED,
}


# # 需要安装tzdata库
# from zoneinfo import ZoneInfo
# datetime.now(ZoneInfo('Asia/Shanghai'))


def bj_time():
    beijing_offset = timedelta(hours=8)
    return datetime.now(timezone(beijing_offset))


def utc_time():
    return datetime.now(timezone.utc)


# # url = "https://example.com/path?query=hello
# import urllib.parse
# import zlib
# def url_compressed(url):
#     # encoded_url = urllib.parse.quote(url, safe='')
#     encoded_url = urllib.parse.quote(url, encoding='utf-8')
#     return zlib.compress(encoded_url.encode('utf-8'))
#
#
# def url_decompressed(url):
#     if not url:
#         return ''
#     try:
#         decompressed_url = zlib.decompress(url).decode('utf-8')
#         return urllib.parse.unquote(decompressed_url)
#     except:
#         return ''




