import os
from pathlib import Path
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent


class Config(object):
    # Custom:

    # 清理页清除缓存的密码 | password for clean page cache , http://loaclhost/clean-cache
    CLEAN_CACHE_PASSWORD = '123'

    # 用户登录密码(播放密码) | this is login password
    PLAY_PASSWORD = '123'

    # 给数据库中的播放地址设置key防盗链。
    # Signing all video URLs stored in the database. model.py -> MovieSrc|TvSrc -> url
    SIGN_FOR_VIDEO = False

    # 防盗链的key  |  sign key
    LOCAL_SIGN_KEY = '123'

    # 第三方云服务商的URL签名，开启后必须有相关的sign校验函数
    # When URL signing for third-party cloud services
    # is enabled,the corresponding signature verification functions must be implemented.
    # step1,app/common.py : Edit -> CLOUD_CDN_NAME, _PROVIDER_TYPE_MAP
    # step2,app/mmedia/serializers.py    URLSigner -> add fun()
    CLOUD_CDN_SIGN = False

    # 腾讯云点播key  |  tencent
    TENCENT_VIDEO_KEY = '123'
    # 阿里云点播key  |  alibaba
    ALI_VIDEO_KEY = '123'

    # (1,2) 选择jwt的token的验证方式：| the way to validate jwt-token: 1-> cookie , 2-> header
    # **NOTE**: 返回模式必须和前端(app/static/src/js/base.js)的配置AppConfig.JwtMode保持一致
    # **NOTE**: This item must be same value with app/static/src/js/base.js -> AppConfig.JwtMode = ?
    JWT_RETURN_MODE = 2

    # 首页热门类目需要显示的内容，选择的是Movie和TVShow表的id。 class MediaHome: MediaHome.hot_info()
    # the content for index hot_page , this id from the tables : Movie.id and TVShow.id.
    # 允许空值，但必须存在。 allow [] ,
    MOVIE_IDS = [1, 2, 3, 4, 5]
    TV_IDS = [1, 2, 3, 4, 5]

    # Others:

    JSONIFY_MIMETYPE = "application/json;charset=utf-8"

    # jwt
    JWT_TOKEN_LOCATION = ['cookies', 'headers']  # 接收token的方式，'headers' 'cookies' 'query_string' 'json'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=6)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ACCESS_COOKIE_NAME = 'l_tk'
    JWT_ACCESS_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    JWT_ACCESS_CSRF_COOKIE_NAME = 'csrf_access_token'
    JWT_REFRESH_COOKIE_NAME = 're_tk'

    JWT_COOKIE_CSRF_PROTECT = True  # JWT的cookieCSRF保护
    JWT_CSRF_IN_COOKIES = True  # 是否将 CSRF-Token 存储在Cookie中

    JWT_CSRF_CHECK_FORM = False
    JWT_SESSION_COOKIE = True  # 设置为会话Cookie，浏览器关闭删除
    JWT_COOKIE_SECURE = False  # 仅https下发送cookie
    JWT_CSRF_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']
    JWT_COOKIE_SAMESITE = 'Strict'

    # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_RECORD_QUERIES = False

    # todo-mok : 连接数据库，mariadb或者mysql | set database： mariadb or mysql
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(BASE_DIR / 'mokmedia.db')
    # mysql+pymysql://  mysql+mysqlconnector://
    # SQLALCHEMY_DATABASE_URI = "mariadb+mariadbconnector://user:password@localhost/mokmedia"

    # flask-limiter
    RATELIMIT_ENABLED = True  # 总开关 | limiter on/off
    RATELIMIT_DEFAULT = '16/seconds;300/hour'
    RATELIMIT_SWALLOW_ERRORS = True  # 发生错误不会抛出，比如redis断连了，就没限制了。 | ignore limiter error


class DevelopmentConfig(Config):
    """开发模式配置"""
    DEBUG = True
    SECRET_KEY = "abc"  # Flask key
    JWT_SECRET_KEY = 'abc'  # jwt key

    # SQLALCHEMY_TRACK_MODIFICATIONS = True  # DEBUG
    # SQLALCHEMY_ECHO = True  # DEBUG
    # SQLALCHEMY_RECORD_QUERIES = True  # DEBUG


class ProductionConfig(Config):
    """生产环境配置"""

    SECRET_KEY = os.getenv('SECRET_KEY', '')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    CLEAN_CACHE_PASSWORD = os.getenv('CLEAN_CACHE_PASSWORD', '')
    PLAY_PASSWORD = os.getenv('PLAY_PASSWORD', '')
    LOCAL_SIGN_KEY = os.getenv('LOCAL_SIGN_KEY', '')
    TENCENT_VIDEO_KEY = os.getenv('TENCENT_VIDEO_KEY', '')
    ALI_VIDEO_KEY = os.getenv('ALI_VIDEO_KEY', '')


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}


def validate_config(config_obj):
    err = []

    play_password = getattr(config_obj, 'PLAY_PASSWORD', None)
    if not play_password or not str(play_password).strip():
        err.append("PLAY_PASSWORD (str) 未设置。 | no set.")

    clean_cache_password = getattr(config_obj, 'CLEAN_CACHE_PASSWORD', None)
    if not clean_cache_password or not str(clean_cache_password).strip():
        err.append("CLEAN_CACHE_PASSWORD (str) 未设置。 | no set.")

    jwt_return_mode = getattr(config_obj, 'JWT_RETURN_MODE', None)
    if not jwt_return_mode or not isinstance(jwt_return_mode, int):
        err.append("JWT_RETURN_MODE (int) 未设置。 | no set.")
    elif jwt_return_mode not in (1, 2):
        err.append("JWT_RETURN_MODE (int) 只能是1(cookie)或者2(header) | must be 1 (cookie) or 2 (header)")

    jwt_key = getattr(config_obj, 'JWT_SECRET_KEY', None)
    if not jwt_key or not str(jwt_key).strip():
        err.append("JWT_SECRET_KEY (str) 未设置。 | no set.")

    secret_key = getattr(config_obj, 'SECRET_KEY', None)
    if not secret_key or not str(secret_key).strip():
        err.append("SECRET_KEY (str) 未设置。 | no set.")

    movie_ids = getattr(config_obj, 'MOVIE_IDS', None)
    tv_ids = getattr(config_obj, 'TV_IDS', None)
    if not movie_ids or not tv_ids:
        err.append("movie_ids (list) and (list)  | must be set,allow []")
    elif not isinstance(movie_ids, list) or not isinstance(tv_ids, list):
        err.append("movie_ids (list) and tv_ids (list) 类型错误,允许空列表[]。 | type error, allow []")

    sign_for_video = getattr(config_obj, 'SIGN_FOR_VIDEO', None)
    if not isinstance(sign_for_video, bool):
        err.append("SIGN_FOR_VIDEO (bool) 未设置。 | no set.")
    elif sign_for_video:
        local_sign_key = getattr(config_obj, 'LOCAL_SIGN_KEY', None)
        if not local_sign_key or not str(local_sign_key).strip():
            err.append("LOCAL_SIGN_KEY (bool) 当key防盗链开启，必须设置防盗链的key |  "
                       "when SIGN_FOR_VIDEO=True, LOCAL_SIGN_KEY is required")

    cloud_cdn_sign = getattr(config_obj, 'CLOUD_CDN_SIGN', None)
    if not isinstance(cloud_cdn_sign, bool):
        err.append("CLOUD_CDN_SIGN (bool) 未设置。 | no set.")
    if cloud_cdn_sign:
        # 别忘了设置 key  | set cloud key ！
        pass

    return err


if __name__ == '__main__':
    # develop
    errors = validate_config(config_map['develop'])
    if errors:
        print(f" 【develop】 配置检查失败 | Development Config error !")
        for e in errors:
            print(f"   • {e}")
    else:
        print('config 通过 | config passed')

    # # product
    # errors = validate_config(config_map['product'])
    # if errors:
    #     print(f" 【product】 配置检查失败 | Production Config error !")
    #     for e in errors:
    #         print(f"   • {e}")
    # else:
    #     print('config 已经检查 | config passed')

    pass
