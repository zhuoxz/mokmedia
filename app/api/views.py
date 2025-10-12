from io import BytesIO
from random import sample as rd_sample
from string import ascii_uppercase as str_abc, digits as str_num
from hashlib import md5
from datetime import timedelta
from functools import wraps

from flask import current_app, request, jsonify, Response, make_response, send_from_directory, abort
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from flask_limiter.util import get_remote_address
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, \
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies, get_jwt

from . import api_blue
from .controller import auth_users, auth_captcha
from ..common import gen_uuid
from ..mmedia.model import Wish
from ..extensions import r, cache, limiter, image_captcha, db


MAX_LOGIN_TRY = 20
SHOW_CAPTCHA = 3

DEFAULT_OPTIONS = {
    'httponly': True,
    'samesite': 'Lax',
}

DOWNLOAD_LIST = ['test720p.mp4']


def add_id_cookie(id_name: str, **cookie_options):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            str_id = request.cookies.get(id_name)
            if str_id is None or len(str_id) != 32:
                str_id = gen_uuid()
            kwargs[id_name] = str_id
            response = make_response(f(*args, **kwargs))
            final_options = {**DEFAULT_OPTIONS, **cookie_options}
            response.set_cookie(id_name, str_id, **final_options)
            return response
        return decorated_function
    return decorator


@api_blue.route('/api/captcha', methods=['GET'])
@add_id_cookie('c_id')
@limiter.limit("18/minute")
@limiter.exempt
def generate_captcha(c_id):
    """ 验证码不能用用户uid，当不同设备去发送，验证时会粘在一起。"""
    # code = ''.join(rd_sample(str_num, 4))  # like: 1234
    code = ''.join(rd_sample(str_abc, 4))  # like: ABCD
    try:
        r.setex(f"cc:{c_id}", timedelta(minutes=3, seconds=30), code)
        r.setex(f"caat:{c_id}", timedelta(minutes=3, seconds=38), 0)
        image: BytesIO = image_captcha.generate(code)
        response = make_response(Response(image, mimetype="image/png"))
        return response
    except RedisError:
        #  if redis crashed, instead of session , memory?
        abort(500, 'captcha: redis crash')
    except (ValueError, TypeError, AttributeError, Exception):
        abort(500, 'captcha: error')


@api_blue.route('/api/auth', methods=['POST'])
@jwt_required(optional=True)
@limiter.limit("18/hour")
def auth():
    jwt_mode = current_app.config['JWT_RETURN_MODE']
    current_user = get_jwt_identity()
    if current_user:
        return jsonify(msg='已登录。', jwt_mode=jwt_mode), 200
    return jsonify(msg='未登录。'), 401

# ---------------     Option 1       -------------------
# @api_blue.route('/api/login', methods=['POST'])
# @add_id_cookie('u_id', max_age=2592000)  # 30 day,传u_id, 添加cookie:u_id
# @limiter.limit("22/hour")
# def login(u_id):
#     """
#     Option 1
#     当redis出错，禁止登录 | When redis crashed, disable user login.
#     """
#
#     attempts_key = f"lgat:{u_id}"
#
#     try:
#         attempts = r.get(attempts_key)
#         login_attempts = int(attempts) if attempts is not None else 1
#     except RedisError:
#         return jsonify(msg='当前时段，无法登录。', show_captcha=False), 500
#
#     c_id = request.cookies.get('c_id')
#     if SHOW_CAPTCHA < login_attempts < MAX_LOGIN_TRY:
#         captcha = request.json.get('captcha')
#         validated, msg = auth_captcha(c_id, captcha)
#         if not validated:
#             try:
#                 r.setex(attempts_key, timedelta(hours=5), login_attempts + 1)
#             except RedisError:
#                 pass
#
#             return jsonify(code=1, msg=msg, show_captcha=True), 401
#
#     if login_attempts >= MAX_LOGIN_TRY:
#         return jsonify(msg='刷新太频繁,5个小时后再试.', show_captcha=True), 429
#
#     password = request.json.get('pd')
#     if auth_users(password=password):
#         try:
#             if login_attempts > SHOW_CAPTCHA and c_id:
#                 r.delete(attempts_key, f"cc:{c_id}", f"caat:{c_id}")
#             else:
#                 r.delete(attempts_key)
#         except RedisError:
#             # more: redis残留。logger -> warn
#             pass
#
#         access_token = create_access_token(identity=u_id,
#                                            # additional_claims={'role': 'guest', 'is_anonymous': False}
#                                            )
#         refresh_token = create_refresh_token(identity=u_id)
#         jwt_mode = current_app.config['JWT_RETURN_MODE']
#         if jwt_mode == 2:
#             # config -> JWT_RETURN_MODE= 2 , JWT_TOKEN_LOCATION add 'headers' 前端用请求头验证
#             return jsonify(msg='登录成功', jwt_mode=2, token=access_token, re_token=refresh_token), 200
#         elif jwt_mode == 1:
#             # config -> JWT_RETURN_MODE= 1 , JWT_TOKEN_LOCATION add 'cookies'  前端用cookies验证
#             remember_me = request.json.get('rm', True)
#             resp = jsonify(msg='登录成功', jwt_mode=1)
#             if remember_me:
#                 set_access_cookies(resp,
#                                    access_token,
#                                    int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()))
#                 set_refresh_cookies(resp,
#                                     refresh_token,
#                                     int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()))
#             else:
#                 set_access_cookies(resp, access_token, max_age=None)
#                 set_refresh_cookies(resp, refresh_token, max_age=None)
#             return resp, 200
#
#     else:
#         try:
#             r.setex(attempts_key, timedelta(hours=5), login_attempts + 1)
#         except RedisError:
#             pass
#
#         if login_attempts > SHOW_CAPTCHA:
#             return jsonify(code=2, msg='口令错误。。。', show_captcha=True), 401
#         if login_attempts == SHOW_CAPTCHA:
#             return jsonify(code=2, msg='口令错误。。。', will_show=True, show_captcha=False), 401
#         return jsonify(code=2, msg='口令错误。。。', show_captcha=False), 401


# ---------------     Option 2       -------------------
@api_blue.route('/api/login', methods=['POST'])
@add_id_cookie('u_id', max_age=2592000)  # 30 day,传u_id, 添加cookie:u_id
@limiter.limit("22/hour")
def login(u_id):
    """
    Option 2
    当redis出错，依然允许登录尝试 | even redis crashed，still allow login attempts.

    """
    # current_app.session_interface.regenerate(sess) flask-session
    # u_id = session.setdefault('u_id', gen_uuid())  # 如果把user id放在session里

    redis_status = True
    attempts_key = f"lgat:{u_id}"

    try:
        attempts = r.get(attempts_key)
        login_attempts = int(attempts) if attempts is not None else 1
    except RedisError:
        # 验证码需要redis存储，如果返回，抛出错会阻挡验证。或者出错时不让登录。(此时给个默认值0, 当redis出错的时候跳过验证码检查)
        # return jsonify(msg='系统出错', show_captcha=False), 500
        # more:  redis记录在logger()里
        redis_status = False
        login_attempts = 0

    c_id = request.cookies.get('c_id')
    if SHOW_CAPTCHA < login_attempts < MAX_LOGIN_TRY:
        captcha = request.json.get('captcha')
        validated, msg = auth_captcha(c_id, captcha)
        if not validated:
            if redis_status:
                try:
                    r.setex(attempts_key, timedelta(hours=5), login_attempts + 1)
                except RedisError:
                    pass
            return jsonify(code=1, msg=msg, show_captcha=True), 401

    if login_attempts >= MAX_LOGIN_TRY:
        return jsonify(msg='刷新太频繁,5个小时后再试.', show_captcha=True), 429

    password = request.json.get('pd')
    if auth_users(password=password):
        if redis_status:
            try:
                if login_attempts > SHOW_CAPTCHA and c_id:
                    r.delete(attempts_key, f"cc:{c_id}", f"caat:{c_id}")
                else:
                    r.delete(attempts_key)
            except RedisError:
                # more: redis残留。logger -> warn
                pass

        access_token = create_access_token(identity=u_id,
                                           # additional_claims={'role': 'guest', 'is_anonymous': False}
                                           )
        refresh_token = create_refresh_token(identity=u_id)
        jwt_mode = current_app.config['JWT_RETURN_MODE']
        if jwt_mode == 2:
            # config -> JWT_RETURN_MODE= 2 , JWT_TOKEN_LOCATION add 'headers' 前端用请求头验证
            return jsonify(msg='登录成功', jwt_mode=2, token=access_token, re_token=refresh_token), 200
        elif jwt_mode == 1:
            # config -> JWT_RETURN_MODE= 1 , JWT_TOKEN_LOCATION add 'cookies'  前端用cookies验证
            remember_me = request.json.get('rm', True)
            resp = jsonify(msg='登录成功', jwt_mode=1)
            if remember_me:
                set_access_cookies(resp,
                                   access_token,
                                   int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()))
                set_refresh_cookies(resp,
                                    refresh_token,
                                    int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()))
            else:
                set_access_cookies(resp, access_token, max_age=None)
                set_refresh_cookies(resp, refresh_token, max_age=None)
            return resp, 200

    else:
        if redis_status:
            try:
                r.setex(attempts_key, timedelta(hours=5), login_attempts + 1)
            except RedisError:
                pass
        if login_attempts > SHOW_CAPTCHA:
            return jsonify(code=2, msg='口令错误。。。', show_captcha=True), 401
        if login_attempts == SHOW_CAPTCHA:
            return jsonify(code=2, msg='口令错误。。。', will_show=True, show_captcha=False), 401
        return jsonify(code=2, msg='口令错误。。。', show_captcha=False), 401


@api_blue.route('/api/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()

    jwt_mode = current_app.config['JWT_RETURN_MODE']

    access_token = create_access_token(
        identity=current_user,
        fresh=False,
        # additional_claims={'role': get_jwt().get('role'), 'is_anonymous': get_jwt().get('is_anonymous')}
    )
    if jwt_mode == 2:
        return jsonify(msg='令牌刷新成功', token=access_token), 200
    if jwt_mode == 1:
        resp = jsonify(msg='令牌刷新成功')
        remember_me = request.json.get('rm', False)
        if remember_me:
            set_access_cookies(resp, access_token, int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()))
        else:
            set_access_cookies(resp, access_token)
        return resp, 200
    return jsonify(msg='JWT返回模式错误'), 500


@api_blue.route('/api/logout', methods=['POST', 'GET'])
@limiter.limit("10/minute")
def logout():
    jwt_mode = current_app.config['JWT_RETURN_MODE']
    if jwt_mode == 1:
        resp = jsonify(msg='已退出')
        unset_jwt_cookies(resp)
        return resp, 200
    return jsonify(msg='已退出。'), 200  # only JWT -> cookies, others do nothing


@api_blue.route('/api/wish', methods=['POST'])
# @limiter.limit("4/minute", deduct_when=lambda response: response.status_code != 200)
@limiter.limit("15/hour;4/minute")
@jwt_required()
def wish():
    remote_ip = get_remote_address() or None

    data = request.get_json()
    content = data.get('content')

    if content and isinstance(content, str):
        content_length = len(content)
        if 0 < content_length < 70:
            try:
                db.session.add(Wish(user=get_jwt_identity(), comment=content.strip(), ip=remote_ip))
                db.session.commit()
                return jsonify(code=200, msg='已经提交成功'), 200
            except (SQLAlchemyError, Exception):
                return jsonify(msg='无法提交..'), 500
        elif content_length > 70:
            return jsonify(msg='太啰嗦，提交失败'), 400
        else:
            return jsonify(msg='什么也没说'), 400
    else:
        return jsonify(msg='数据为空或类型不正确'), 400


@api_blue.route('/api/download/<string:name>', methods=['GET'])
@limiter.exempt
def download_file(name: str):

    if not name.strip() or len(name) > 80:
        return jsonify(msg='参数不正确'), 404

    if name in DOWNLOAD_LIST:
        #  'static/download'
        return send_from_directory('static/media/video', name, as_attachment=True)
    else:
        return jsonify(msg='文件已经删除'), 404


@api_blue.route('/api/clean-cache', methods=['POST'])
@limiter.limit("6/minute")
def clean_cache():
    data = request.get_json()
    password = data.get('password')
    if not password:
        return jsonify(msg="缺少密码"), 400
    if password != md5(current_app.config.get('CLEAN_CACHE_PASSWORD').encode('utf-8')).hexdigest():
        return jsonify(msg='密码错误'), 401
    try:
        try:
            r.ping()
            redis_working = True
        except:
            redis_working = False
        cache.clear()
        return jsonify(msg="缓存清理成功", redis=redis_working), 200
    except Exception:
        return jsonify(msg='缓存清理失败'), 500


#  ------ ↓↓  Debug  ↓↓ --------

# @api_blue.after_request
# def after(response: Response):
#     # response.headers['Access-Control-Max-Age']
#     response.headers['X-Content-Type-Options'] = 'nosniff'
#     response.headers['X-Frame-Options'] = 'SAMEORIGIN'
#     response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
#     return response
