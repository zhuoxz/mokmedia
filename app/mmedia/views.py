import time

from flask import request, render_template, jsonify, abort, redirect, current_app
from flask_jwt_extended import jwt_required
# from flask import make_response
# from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, unset_jwt_cookies
# from jwt.exceptions import PyJWTError

from . import media_blue
from ..extensions import cache, limiter
from ..common import DeviceType, ProviderType
from .controller import (media_detail, MediaHome, get_play_list, sign_url, validate_sign_url_param, real_url,
                         validate_typ_mid, validate_play_url_param, validate_play_url)


VIDEO_EXPIRES = 18060  # 5小时，允许1分钟延迟 | 5 hours，allow 1min delay


@media_blue.route('/media', methods=['GET'])
@limiter.exempt
@cache.cached(timeout=518400, query_string=True)
def movie_home():
    nav_for = request.args.get('tp', type=str, default='hot')
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    device_type = DeviceType.get_type(request)

    res = MediaHome.get_data(nav_for, page, per_page, device_type)
    if res is None:
        abort(404)
    return render_template('media.html', res=res, nav_for=nav_for)


@media_blue.route('/media/<string:mid>', methods=['GET'])
@limiter.exempt
@cache.cached(timeout=518400, query_string=True)
def detail_page(mid: str):

    typ = request.args.get('typ', type=str)

    is_valid, uuid_mid = validate_typ_mid(typ, mid)
    if not is_valid:
        abort(404)

    data = media_detail(uuid_mid, typ)

    if not data:
        abort(404)
    return render_template('play.html', data=data, typ=typ, mid=mid)


# @media_blue.route('/media/<string:mid>', methods=['GET'])
# @limiter.exempt
# # @cache.cached(timeout=518400, query_string=True)
# def play_page(mid: str):
#     """ 有坑啊，cookie提交模式，当token过期了以后带不上刷新token,需要后端自动刷新token。"""
#     typ = request.args.get('typ', type=str)
#     is_valid, uuid_mid = validate_typ_mid(typ, mid)
#     if not is_valid:
#         abort(404)
#
#     jwt_mode = current_app.config['JWT_RETURN_MODE']
#     if jwt_mode == 2:
#         data = media_detail(uuid_mid, typ)
#         if not data:
#             abort(404)
#         return render_template('play.html', data=data, typ=typ, mid=mid)
#
#     try:
#         verify_jwt_in_request(optional=True)
#         current_user = get_jwt_identity()
#     # except :
#     except PyJWTError:
#         current_user = None
#         # data = media_detail(mid, typ)
#         # if not data:
#         #     abort(404)
#         # resp = make_response(render_template('play.html', data=data, typ=typ, mid=mid))
#         # unset_jwt_cookies(resp)
#         # return resp
#     if current_user:
#         data = media_detail(uuid_mid, typ, with_play_list=True)
#     else:
#         data = media_detail(uuid_mid, typ)
#     if not data:
#         abort(404)
#     return render_template('play.html', data=data, typ=typ, mid=mid)


@media_blue.route('/media/api/playlist/<string:mid>', methods=['GET', 'POST'])
@limiter.limit("46/minute")
@jwt_required()
def play_list(mid: str):

    typ = request.args.get('typ', type=str)
    is_valid, uuid_mid = validate_typ_mid(typ, mid)
    if not is_valid:
        return jsonify(msg='参数错误'), 400

    data = get_play_list(uuid_mid,
                         typ,
                         with_sign=current_app.config.get('SIGN_FOR_VIDEO'),
                         open_cloud_sign=current_app.config.get('CLOUD_CDN_SIGN'))

    if not data or data['playList'] is None:
        return jsonify(msg='内部错误。'), 500
    return jsonify(data), 200


@media_blue.route('/media/api/geturl', methods=['POST'])
@limiter.limit("20/minute")
@jwt_required()
def get_url():
    params = request.get_json()

    typ = request.args.get('typ', type=str)

    if params is None or not isinstance(params, list):
        return jsonify(msg='参数错误'), 400
    if not validate_sign_url_param(params):
        return jsonify(msg='参数错误'), 400

    data = sign_url(typ, params, VIDEO_EXPIRES)
    # data = sign_url(params, request.args)
    if data:
        return jsonify(data), 200

    return jsonify(msg='签名失败'), 400


@media_blue.route('/media/play/<string:mid>/<string:sid>', methods=['GET'])
def play(mid: str, sid: str):

    typ = request.args.get('typ', type=str)
    sign = request.args.get('sign', type=str)
    t = request.args.get('t', type=str)

    is_valid, uuid_sid, int_t = validate_play_url_param(typ, mid, sid, sign, t)
    if not is_valid:
        return jsonify(msg='参数错误'), 400

    if int(time.time()) >= int_t:
        return jsonify(code=4412, msg='播放签名过期'), 403

    if not validate_play_url(sid, sign, t):
        return jsonify(code=4413, msg='签名错误'), 403

    url, url_type, suffix = real_url(typ, mid, uuid_sid)

    if not url.strip():
        return jsonify(msg='视频已删除'), 404

    if url_type == ProviderType.DIRECT or url_type == ProviderType.SIGNED:
        return redirect(url, code=302)
    else:


        # # 仅开发，调试使用 | only for Development
        # from flask import send_file
        # return send_file(f'/static/media/video/{url}', mimetype=f'video/{suffix}', as_attachment=False)
        # # 或者 | or :
        return redirect(f'/static/media/video/{url}', code=302)


        # # 部署 | Production
        # response = make_response()
        # response.headers['X-Accel-Redirect'] = '/protected/videos/' + url
        # # # # response.headers['Content-Type'] = f'video/{suffix}'
        # return response


#  ------ ↓↓  Debug  ↓↓ --------

# @media_blue.after_request
# def log_queries(response):
#     """数据库调试 SQLALCHEMY_RECORD_QUERIES = True"""
#     from flask_sqlalchemy.record_queries import get_recorded_queries
#     for query in get_recorded_queries():
#         print(query)
#     return response
#
# @media_blue.before_request
# def test():
#     print(request.cookies)
