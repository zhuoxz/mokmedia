from hashlib import md5
from typing import Any

from redis.exceptions import TimeoutError, ConnectionError, RedisError
from flask import current_app

from ..extensions import r


def auth_users(password: Any) -> bool:
    if not password or not isinstance(password, str) or len(password) != 32:
        return False
    if md5(current_app.config.get('PLAY_PASSWORD').encode(encoding='utf-8')).hexdigest() == password:
        return True
    return False


def auth_captcha(c_id: str, captcha: str) -> (bool, str):
    """  1 captcha, 3 submit try"""
    if c_id is None:
        return False, '浏览器不允许cookie或者非法请求。'
    if not c_id.strip():
        return False, '参数错误。'

    if captcha is None:
        return False, '参数错误。'
    if not isinstance(captcha, str):
        return False, '参数类型错误。'
    cap_clean = captcha.replace(" ", "")
    if cap_clean == '':
        return False, '验证码不能为空。'
    if not 0 < len(cap_clean) <= 6:
        return False, '验证码不合规。'

    try:
        captcha_key = f"cc:{c_id}"
        attempts_key = f"caat:{c_id}"

        # if not r.exists(captcha_key):
        #     return False, '验证码已失效'
        redis_code = r.get(captcha_key)
        if not redis_code:
            return False, '验证码已失效。'

        _attempts = r.get(attempts_key)
        if _attempts is None:
            return False, '失效'

        attempts = int(_attempts)
        if attempts > 2:
            r.delete(captcha_key, attempts_key)
            return False, '验证码失效，请刷新验证码。'
        # when redis config set decode_responses=False/True,
        code = redis_code.decode('utf-8') if isinstance(redis_code, bytes) else redis_code
        if cap_clean.lower() == code.lower():
            r.set(attempts_key, attempts + 1, keepttl=True)
            return True, '验证成功。'
        else:
            r.set(attempts_key, attempts + 1, keepttl=True)
            return False, '验证码错误。'
    except (ValueError, UnicodeDecodeError):
        return False, '验证码数据损坏。'
    except RedisError as e:
        return False, f'系统出错。{e}'
    except (TimeoutError, ConnectionError, ):
        return False, '系统临时故障，请稍后再试。'
    except Exception:
        return False, '系统出错。'
