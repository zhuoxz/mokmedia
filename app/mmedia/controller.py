"""
想不通的时候记得先把缓存清了再试试。 Anyway,always clear the cache first when debugging code.
"""
import uuid
import time
from datetime import timedelta

from flask import current_app
from sqlalchemy.orm import load_only, joinedload, selectinload
from sqlalchemy import select
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy.pagination import Pagination

from ..extensions import db, r
from ..common import PAGINATION_CONFIG, MEDIA_PER_PAGE_CONFIG, check_uuid, DeviceType, ProviderType, CLOUD_CDN_NAME
from .model import (Movie, TVShow, MovieSrc, TvSrc, Genre, MovieSubtitle, TVSubtitle,
                    tv_src_subtitle_table, mv_src_subtitle_table)
from .serializers import TVShowSerializer, MovieSerializer, SubtitleSerializer, URLSigner, get_list_sign, get_list


def validate_typ_mid(typ: str | None, mid: str) -> (bool, uuid.UUID | None):
    if not typ or typ not in ['mv', 'tv']:
        return False, None

    if not mid.strip():
        return False, None
    try:
        return True, uuid.UUID(mid)
    except ValueError:
        return False, None


def validate_sign_url_param(params: list) -> bool:
    if len(params) == 0 or len(params) > 25:
        return False
    for i, item in enumerate(params):
        if not isinstance(item, dict):
            return False
        if 'uuid' not in item or 'quality' not in item:
            return False
        uuid_str = item['uuid']
        # if not isinstance(uuid_str, str) or not uuid_str.strip() or len(uuid_str) != 32:
        #     return False
        if not isinstance(uuid_str, str) or not check_uuid(uuid_str):
            return False
        q = item['quality']
        if not (isinstance(q, int) or (isinstance(q, str) and q.isdigit())):
            # if not isinstance(q, (int, str)) or (isinstance(q, str) and not q.isdigit()):
            return False
    return True


def validate_play_url_param(typ: str | None, mid: str, sid: str, sign: str | None, t: str | None):
    if not all([typ, sign, t]):
        return False, None, None

    if typ not in ['mv', 'tv']:
        return False, None, None

    if not mid.strip() or not sid.strip() or not t.strip():
        return False, None, None

    try:
        uuid.UUID(mid)
        uuid_sid = uuid.UUID(sid)
    except ValueError:
        return False, None, None

    try:
        int_t = int(t, 16)
    except ValueError:
        return False, None, None
    return True, uuid_sid, int_t


def validate_play_url(sid: uuid.UUID | str, sign: str, t: str) -> bool:
    """ t: 16进制时间戳字符串 | Hexadecimal string of the timestamp """
    return URLSigner.validate_sign(sid, sign, t)


class MediaHome:

    @staticmethod
    def get_data(nav_for: str, page: int, per_page: int, device_type: DeviceType) -> dict | None:
        if nav_for == 'hot':
            return MediaHome.hot_info()
        elif nav_for == 'dy':
            return MediaHome.media_info('mv', device_type, page=page, per_page=per_page)
        elif nav_for == 'ds':
            return MediaHome.media_info('tv', device_type, page=page, per_page=per_page)
        elif nav_for == 'dj':
            return MediaHome.dj_info(device_type, page=page, per_page=per_page)
        else:
            return None

    @staticmethod
    def hot_info() -> dict:
        """
        todo: add pagination ?
        """
        try:
            mv_stmt = (
                select(Movie.uuid, Movie.title, Movie.description)
                .where(Movie.id.in_(current_app.config['MOVIE_IDS']))
                .order_by(Movie.update_at.desc())
            )
            movie_results = db.session.execute(mv_stmt).all()
            movies = [{'uuid': u.hex, 'title': t, 'description': d, 'typ': 'mv'} for u, t, d in movie_results]

            tv_stmt = (
                select(TVShow.uuid, TVShow.title, TVShow.description)
                .where(TVShow.id.in_(current_app.config['TV_IDS']))
                .order_by(TVShow.update_at.desc())
            )
            tv_results = db.session.execute(tv_stmt).all()
            tvs = [{'uuid': u.hex, 'title': t, 'description': d, 'typ': 'tv'} for u, t, d in tv_results]

            return {
                "success": True,
                "error": '',
                "data": movies + tvs,
                "pagination": None
            }
        except SQLAlchemyError:
            return MediaHome._error_res('查询错误')
        except (ValueError, KeyError, Exception):
            return MediaHome._error_res('系统错误')

    @staticmethod
    def media_info(typ: str, device_type: DeviceType, page: int = None, *, per_page: int = None,
                   only_src: bool = True) -> dict:
        """
        only_src 是查询至少含有一个播放源的视频，device_type是根据不同的设备生成智能分页列表(前端去分或者jinja2迭代iter_pages也行)
        """
        try:
            if typ == 'mv':
                stmt = (
                    select(Movie).options(
                        load_only(Movie.uuid, Movie.title, Movie.description)
                    )
                    .order_by(Movie.update_at.desc())
                )
                if only_src:
                    stmt = stmt.where(Movie.movie_src.any(MovieSrc.is_active))
            elif typ == 'tv':
                stmt = (
                    select(TVShow).options(
                        load_only(TVShow.uuid, TVShow.title, TVShow.description)
                    )
                    .where(~TVShow.genres.any(name='短剧'))
                    .order_by(TVShow.update_at.desc())
                )
                if only_src:
                    stmt = stmt.where(TVShow.tv_src.any(TvSrc.is_active))
            else:
                return MediaHome._error_res('参数错误')

            if per_page is None:
                per_page = MEDIA_PER_PAGE_CONFIG.get(device_type)

            pagination = db.paginate(stmt, page=page, per_page=per_page, max_per_page=100, error_out=False)
            if typ == 'mv':
                data = [MovieSerializer(items).to_brief_dict for items in pagination.items]
            else:
                data = [TVShowSerializer(items).to_brief_dict for items in pagination.items]

            return MediaHome._get_res(data, device_type, pagination)
        except SQLAlchemyError:
            return MediaHome._error_res(err='查询错误')
        except NotImplementedError:
            return MediaHome._error_res(err='model错误')
        except (ValueError, KeyError, NotImplementedError, Exception):
            return MediaHome._error_res(err='系统错误')

    @staticmethod
    def dj_info(device_type: DeviceType, page: int = None, *, per_page: int = None, only_src: bool = True) -> dict:
        try:
            stmt = (
                select(TVShow).options(
                    load_only(TVShow.uuid, TVShow.title, TVShow.description))
                .where(TVShow.genres.any(Genre.name == '短剧'))
                .order_by(TVShow.update_at.desc())
            )

            if only_src:
                stmt = stmt.where(TVShow.tv_src.any(TvSrc.is_active))

            if per_page is None:
                per_page = MEDIA_PER_PAGE_CONFIG.get(device_type)

            pagination = db.paginate(stmt, page=page, per_page=per_page, max_per_page=100, error_out=False)
            data = [TVShowSerializer(items).to_brief_dict for items in pagination.items]

            return MediaHome._get_res(data, device_type, pagination)
        except (ValueError, KeyError, SQLAlchemyError):
            return MediaHome._error_res('查询错误')
        except Exception:
            return MediaHome._error_res('系统错误')

    @staticmethod
    def _get_res(data: list, device_type: DeviceType, pagination: Pagination = None, *,
                 has_iter_pages: bool = True) -> dict:
        if data:
            res = {
                "success": True,
                "error": '',
                "data": data,
            }
            if pagination is not None:
                try:
                    pagination_info = {
                        "total": pagination.total,
                        "page": pagination.page,
                        "size": pagination.per_page,
                        "pages": pagination.pages,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                        "prev_num": pagination.prev_num,
                        "next_num": pagination.next_num,
                    }
                    res['pagination'] = pagination_info

                    if has_iter_pages:
                        iter_pages = list(pagination.iter_pages(left_edge=PAGINATION_CONFIG[device_type]['left_edge'],
                                                                left_current=PAGINATION_CONFIG[device_type][
                                                                    'left_current'],
                                                                right_edge=PAGINATION_CONFIG[device_type]['right_edge'],
                                                                right_current=PAGINATION_CONFIG[device_type][
                                                                    'right_current']))
                        res['pagination']['iter_pages'] = iter_pages
                except (AttributeError, KeyError, ValueError):
                    res['error'] = '分页有错误'
                except (SQLAlchemyError, Exception):
                    res['error'] = '分页有错误'
            return res
        return MediaHome._error_res(f"毛都没有")

    @staticmethod
    def _error_res(err: str) -> dict:
        return {
            "success": False,
            "error": err,
            "data": None,
            "pagination": None,
        }


def media_detail(mid: uuid.UUID, typ: str, with_play_list: bool = False) -> dict | None:
    """
    with_play_list  弃用 ！！  |  Deprecated ！！
    with_play_list: 为真时返回的数据包含播放列表data['src']，不含播放链接 | True -> return data include play-list: data['src'], but no urls
    """
    try:
        if typ == 'mv':
            stmt = (
                select(Movie).options(
                    joinedload(Movie.genres),
                    joinedload(Movie.tags),
                    joinedload(Movie.actors),
                    joinedload(Movie.directors),
                )
                .where(Movie.uuid == mid))
            if with_play_list:
                stmt = stmt.options(joinedload(Movie.movie_src))
            result = db.session.execute(stmt).scalars().first()
            if not result:
                return None
            return MovieSerializer(result).to_detail_dict(with_play_list)
        elif typ == 'tv':
            stmt = (
                select(TVShow).options(
                    joinedload(TVShow.genres),
                    joinedload(TVShow.tags),
                    joinedload(TVShow.actors),
                    joinedload(TVShow.directors),
                )
                .where(TVShow.uuid == mid)
            )
            if with_play_list:
                stmt = stmt.options(joinedload(TVShow.tv_src))
            result = db.session.execute(stmt).scalars().first()
            if not result:
                return None
            return TVShowSerializer(result).to_detail_dict(with_play_list)
        else:
            return None

    except (ValueError, KeyError, SQLAlchemyError, NotImplementedError):
        return None
    except Exception:
        return None


def get_play_list(mid: uuid.UUID, typ: str, with_sign: bool, open_cloud_sign: bool = False) -> dict | None:
    try:
        if typ == 'mv':
            stmt = (select(MovieSrc)
                    .join(Movie, MovieSrc.movie_id == Movie.id)
                    .where(Movie.uuid == mid, MovieSrc.is_valid_url)
                    )
            if not with_sign:
                stmt = stmt.options(selectinload(MovieSrc.subtitles))
            if not open_cloud_sign:
                stmt = stmt.where(MovieSrc.provider.not_in(CLOUD_CDN_NAME))

        else:
            stmt = (select(TvSrc)
                    .join(TVShow, TvSrc.tv_id == TVShow.id)
                    .where(TVShow.uuid == mid, TvSrc.is_valid_url, TvSrc.is_active)
                    )
            if not with_sign:
                stmt = stmt.options(selectinload(TvSrc.subtitles))
            if not open_cloud_sign:
                stmt = stmt.where(TvSrc.provider.not_in(CLOUD_CDN_NAME))

        res = db.session.execute(stmt).scalars().all()
        if with_sign:
            return get_list_sign(res)
        return get_list(mid.hex, res)

    except (ValueError, KeyError, TypeError, AttributeError, SQLAlchemyError):
        return None
    except Exception:
        return None


def sign_url(typ: str, sources: list, expires: int) -> dict | None:
    try:
        urls = []
        sids = []
        t = int(time.time()) + expires
        for item in sources:
            sid = item['uuid']
            sids.append(uuid.UUID(sid))
            q = item['quality']
            sign = URLSigner.url_sign(sid, t)
            urls.append({
                # "url": f'/media/{mid}/{sid}?t={t}&sign={sign}',
                "uuid": sid,
                "sign": sign,
                "quality": q if isinstance(q, int) else int(q),
                "suffix": item.get('suffix', 'mp4')
            })
        if not urls or len(sids) == 0:
            return None
    except (ValueError, KeyError, AttributeError, TypeError):
        return None
    except Exception:
        return None

    sub = get_subtitles(typ, sids)

    return {
        "pre_url": "/media/play/",
        "t": t,
        "sources": urls,
        "sub": sub
    }


def get_subtitles(typ: str, sids: list) -> list:
    try:
        sub = []
        if typ == 'mv':
            sub_stmt = (select(MovieSubtitle)
                        .join(mv_src_subtitle_table, MovieSubtitle.id == mv_src_subtitle_table.c.subtitle_id)
                        .join(MovieSrc, MovieSrc.id == mv_src_subtitle_table.c.mv_src_id)
                        .where(MovieSrc.uuid.in_(sids))
                        )
        elif typ == 'tv':
            sub_stmt = (select(TVSubtitle)
                        .join(tv_src_subtitle_table, TVSubtitle.id == tv_src_subtitle_table.c.subtitle_id)
                        .join(TvSrc, TvSrc.id == tv_src_subtitle_table.c.tv_src_id)
                        .where(TvSrc.uuid.in_(sids))
                        )
        else:
            return sub
        sub_res = db.session.execute(sub_stmt).scalars().all()
        if sub_res:
            sub = [res for s in sub_res if (res := SubtitleSerializer(s).to_dict)]
        return sub
    except Exception:
        return []


def real_url(typ: str, mid: str, sid: uuid.UUID) -> (str | None, int | None, str | None):
    try:
        if typ == 'mv':
            stmt = (select(MovieSrc.provider, MovieSrc.url, MovieSrc.media_format)
                    .where(MovieSrc.uuid == sid,  MovieSrc.is_valid_url, MovieSrc.is_active))
        else:
            stmt = (select(TvSrc.provider, TvSrc.url, TvSrc.media_format)
                    .where(TvSrc.uuid == sid, TvSrc.is_valid_url, TvSrc.is_active))
        res = db.session.execute(stmt).first()
        if not res:
            return None, None, None

        suffix = res.media_format or 'mp4'

        url_typ = ProviderType.get_type(res.provider)

        if url_typ == ProviderType.SIGNED:
            try:
                value = r.get(f's:{mid}:{sid.hex}')
                url = value.decode('utf-8') if isinstance(value, bytes) else value
                if not url:
                    _url = URLSigner.get_cloud_url(res.provider, res.url)
                    if _url:
                        r.setex(f's:{mid}:{sid.hex}', timedelta(hours=4, minutes=57), _url)
                        return _url, url_typ, suffix
                    else:
                        return None, None, None
                return url, url_typ, suffix
            except RedisError:
                # return URLSigner.get_cloud_url(res.provider, res.url), url_typ, suffix
                return None, None, None

        else:
            return res.url, url_typ, suffix

    except Exception:
        return None, None, None
