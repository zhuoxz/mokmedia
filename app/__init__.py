from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import jwt_required

from config import config_map, validate_config
from app.extensions import db, cache, jwt, limiter, r
from app.common import gen_uuid, get_device_info
from app.mmedia import media_blue
from app.api import api_blue
# from app.extensions import sess


NOT_FOUND_PREFIXES = ('/static/', '/media/api/', '/media/play/')


def create_app(config_name):
    app = Flask(__name__)

    # 检查配置
    errors = validate_config(config_map.get(config_name))
    if errors:
        raise RuntimeError(
            "\n 配置验证失败 | Config Error: app->config.py->config_map->'{}', total: {} \n"
            .format(config_name, len(errors)) + "\n".join(errors)
        )

    # 获取配置
    app.config.from_object(config_map.get(config_name))

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # JSON_AS_ASCII
    app.json.ensure_ascii = False

    # 缓存
    cache.init_app(app)

    # session
    # app.config['SESSION_REDIS'] = r
    # sess.init_app(app)

    # jwt
    jwt.init_app(app)

    # limiter
    limiter.init_app(app)

    # 数据库
    db.init_app(app)

    # todo 创建数据库的表，只需要运行一次。 | create database table， just run it once
    with app.app_context():
        db.create_all()

    # 注册蓝图
    app.register_blueprint(media_blue)
    app.register_blueprint(api_blue)

    @app.route('/', methods=['GET'])
    @limiter.exempt
    def home():
        return redirect(url_for('media.movie_home'))

    @app.route('/download', methods=['GET', 'POST'])
    @limiter.exempt
    @cache.cached(timeout=518400)
    def download():
        return render_template('download.html')

    @app.route('/clean-cache', methods=['GET'])
    @limiter.limit("22/hour")
    @jwt_required()
    def clean_cache():
        return render_template('clean.html')

    @app.errorhandler(404)
    def not_found_error(e):
        if any(request.path.startswith(prefix) for prefix in NOT_FOUND_PREFIXES):
            return jsonify(msg='请求的资源不存在'), 404
        return render_template('404.html'), 404

    @app.errorhandler(400)
    def bad_request_error(e):
        return jsonify(msg=e.description), 400

    @app.errorhandler(401)
    def bad_request_error(e):
        return jsonify(msg=e.description), 401

    @app.errorhandler(429)
    def ratelimit_handler(e):  # e.description
        # return e.get_response() or make_response(
        #     jsonify(error='刷新太频繁，请稍后再试'), 429
        # )
        return jsonify(msg="刷新太频繁，请稍后再试"), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(msg=f"页面出错。"), 500

    @jwt.invalid_token_loader
    def my_invalid_token_loader(e: str):
        return jsonify(code=3300, msg=f"认证失败，重新登录"), 401

    @jwt.user_lookup_error_loader
    def my_user_lookup_error_loader(jwt_header, jwt_payload):
        return jsonify(code=3301, msg="用户不存在"), 401

    @jwt.unauthorized_loader  # 没有收到请求的token
    def my_unauthorized_loader(e: str):
        return jsonify(code=3302, msg='认证失败，重新登录'), 401

    @jwt.token_verification_failed_loader  # token 内容验证不正确
    def my_token_verification_failed_loader(jwt_header, jwt_payload):
        return jsonify(code=3303, msg="未通过验证"), 401

    @jwt.expired_token_loader
    def my_expired_token_callback(jwt_header, jwt_payload):
        return jsonify(code=3304, msg="登录过期，重新登录"), 401

    @jwt.revoked_token_loader
    def my_revoked_token_loader(jwt_header, jwt_payload):
        return jsonify(code=3305, msg="需要重新登录"), 401

    @jwt.needs_fresh_token_loader
    def my_needs_fresh_token_loader(jwt_header, jwt_payload):
        return jsonify(code=3306, msg="需要重新刷新token"), 401

    @app.context_processor
    def inject_device():
        return get_device_info(request)

    # # JWT cookie验证自动刷新token  |  JWT Auto Refresh Cookie Token
    # from datetime import datetime
    # from datetime import timedelta
    # from datetime import timezone
    # from flask_jwt_extended import create_access_token
    # from flask_jwt_extended import get_jwt
    # from flask_jwt_extended import get_jwt_identity
    # from flask_jwt_extended import set_access_cookies
    # from flask import current_app
    # @app.after_request
    # def refresh_expiring_jwts(response):
    #     jwt_mode = current_app.config['JWT_RETURN_MODE']
    #     if jwt_mode == 1:
    #         try:
    #             exp_timestamp = get_jwt()["exp"]
    #             now = datetime.now(timezone.utc)
    #             target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
    #             if target_timestamp > exp_timestamp:
    #                 access_token = create_access_token(identity=get_jwt_identity())
    #                 set_access_cookies(response, access_token)
    #             return response
    #         except (RuntimeError, KeyError):
    #             # Case where there is not a valid JWT. Just return the original response
    #             pass
    #     return response

    #  ------ ↓↓  Debug  ↓↓ --------

    # # 本地连接白名单 | local request whitelist
    # @limiter.request_filter
    # def ip_whitelist():
    #     return request.remote_addr == "127.0.0.1"

    # # nginx
    # @app.after_request
    # def after_request(response):
    #     if request.path.endswith('.woff2'):
    #         response.headers['Content-Type'] = 'font/woff2'
    #     return response

    # # nginx
    # from flask import Response
    # @app.after_request
    # def after(response: Response):
    #     response.headers['X-Content-Type-Options'] = 'nosniff'
    #     response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    #     response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    #     return response

    # @app.before_request
    # def before():
    #     for i in request.headers.items():
    #         print(i)

    return app

