
"""              *****  Option1:     Development  (test, debug) 调试配置  *****              """

import redis
from redis.exceptions import RedisError
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from captcha.image import ImageCaptcha


# 你的redis链接  |  set redis url
# 如果安装了redis，记得修改超时时间 | When Redis is already installed, it's necessary to modify the timeout values.
redis_url = 'redis://@localhost:6379?socket_connect_timeout=0.1&socket_timeout=0.1'

# Redis
r = redis.from_url(redis_url)

# flask_caching
try:
    r.ping()
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': redis_url,
        'CACHE_REDIS_DB': 0,
        'CACHE_IGNORE_ERRORS': True,
        'CACHE_DEFAULT_TIMEOUT': 3600 * 24 * 6,
        'CACHE_KEY_PREFIX': 'cache',
    }
except RedisError as e:
    cache_config = {'CACHE_TYPE': 'NullCache'}

cache = Cache(config=cache_config)

# limiter
limiter = Limiter(key_func=get_remote_address,
                  storage_uri=redis_url)

# jwt
jwt = JWTManager()

# captcha
image_captcha = ImageCaptcha()


# Flask-SQLAlchemy
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


"""              *****  Option2:     Production     (部署)*****              """

# import redis
# from flask_caching import Cache
# from flask_jwt_extended import JWTManager
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
# from captcha.image import ImageCaptcha
# from app.common import MokError
# from redis.exceptions import RedisError
#
# # todo-mok :连接 Redis | set redis url
# redis_url = 'redis://@localhost:6379'
#
# redis_pool = redis.BlockingConnectionPool.from_url(redis_url,
#                                                    max_connections=15,
#                                                    timeout=2,
#                                                    socket_timeout=2,
#                                                    socket_connect_timeout=2,
#                                                    decode_responses=False,  # return bytes.Flask-Caching must set False
#                                                    protocol=3,
#                                                    db=0
#                                                    )
#
# # Redis
# r = redis.Redis(connection_pool=redis_pool)  # type: ignore
#
# try:
#     r.ping()
# except RedisError as e:
#     raise MokError(f' **extensions.py** : redis没连上 | redis not working. \n 详细 | more: {e}')
#
# cache = Cache(config={
#         'CACHE_TYPE': 'RedisCache',
#         # 'CACHE_OPTIONS': {'connection_pool': redis_pool} doesn't work
#         'CACHE_REDIS_URL': redis_url,
#         'CACHE_REDIS_DB': 0,
#         'CACHE_IGNORE_ERRORS': True,
#         'CACHE_DEFAULT_TIMEOUT': 3600 * 24 * 6,
#         'CACHE_KEY_PREFIX': 'cache',
#         'CACHE_OPTIONS': {
#             'socket_connect_timeout': 2,
#             'socket_timeout': 2,
#             'retry_on_timeout': False,
#             'max_connections': 10,
#         }
# })
#
# # Flask-Limiter
# limiter = Limiter(key_func=get_remote_address,
#                   storage_uri='redis://',
#                   storage_options={"connection_pool": redis_pool})  # type: ignore
#
# # Flask-JWT-Extended
# jwt = JWTManager()
#
# # captcha
# image_captcha = ImageCaptcha()
#
#
# # Flask-SQLAlchemy
# class Base(DeclarativeBase):
#     pass
#
#
# db = SQLAlchemy(model_class=Base)
