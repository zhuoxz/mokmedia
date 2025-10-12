import os
import time
import uuid
from urllib.parse import urlparse
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, Any
from hashlib import md5
from datetime import timedelta

from flask import current_app
from sqlalchemy.orm import InstrumentedAttribute
from redis.exceptions import RedisError

from .model import TVShow, Movie, MovieSrc, TvSrc, TVSubtitle, MovieSubtitle
from ..extensions import r
from ..common import ProviderType


pre_static_sub_path = '/static/media/sub/'


class URLSigner:

    @staticmethod
    def url_sign(sid: uuid.UUID | str, t: int) -> str:
        if isinstance(sid, uuid.UUID):
            sid = sid.hex
        sign_str = f'{sid}{current_app.config['LOCAL_SIGN_KEY']}{format(t, 'x')}'.encode('utf-8')
        sign = md5(sign_str).hexdigest()
        return sign

    # @staticmethod
    # def url_sign2(sid: uuid.UUID | str) -> (str, str):
    #     if isinstance(sid, uuid.UUID):
    #         sid = sid.hex
    #     t = int(time.time())
    #     sign_str = f'{sid}{current_app.config['LOCAL_SIGN_KEY']}{format(t, 'x')}'.encode('utf-8')
    #     sign = md5(sign_str).hexdigest()
    #     return sign, t

    @staticmethod
    def validate_sign(sid: uuid.UUID | str, sign: str, t: str) -> bool:
        if isinstance(sid, uuid.UUID):
            sid = sid.hex
        try:
            sign_str = f'{sid}{current_app.config['LOCAL_SIGN_KEY']}{t}'.encode('utf-8')
            token = md5(sign_str).hexdigest()
            if token == sign:
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def url_sign_tencent(url: str | InstrumentedAttribute) -> str | None:
        """
        腾讯云点播
        https://cloud.tencent.com/document/product/266/14047
        """
        try:
            parse_url = urlparse(url)
            path = parse_url.path
            directory = os.path.dirname(path) + '/'
            expire_at = format(int(time.time()) + 18060, 'x')  # 5 hours
            rlimit = 5
            sign_str = f'{current_app.config['TENCENT_VIDEO_KEY']}{directory}{expire_at}{rlimit}'.encode('utf-8')
            sign = md5(sign_str).hexdigest()
            return f'{url}?t={expire_at}&rlimit={rlimit}&sign={sign}'
        except:
            return None

    @staticmethod
    def url_sign_ali(url: str | InstrumentedAttribute) -> str | None:
        """
        阿里云 类型A签名 | Aliyun sign Type A
        https://help.aliyun.com/zh/vod/user-guide/type-a-signing?spm=a2c4g.11186623.0.0.270e13ef689Gfp#main-2321301
        """
        try:
            parse_url = urlparse(url)
            t = str(int(time.time()))
            sign_str = f'{parse_url.path}-{t}-0-0-{current_app.config['ALI_VIDEO_KEY']}'.encode('utf-8')
            sign = md5(sign_str).hexdigest()
            return f'{url}?auth_key={t}-0-0-{sign}'
        except:
            return None

    @staticmethod
    def get_cloud_url(provider, url):
        if provider == '腾讯云':
            return URLSigner.url_sign_tencent(url)
        if provider == '阿里云':
            return URLSigner.url_sign_ali(url)
        return None


def get_list(mid: str, items: list[TvSrc] | list[MovieSrc]) -> dict:

    def _add_to_result(src, url):
        provider = src.provider
        ep_str = str(src.ep)
        quality_str = str(src.quality)

        if provider not in result:
            result[provider] = {}
        if ep_str not in result[provider]:
            result[provider][ep_str] = {}

        result[provider][ep_str][quality_str] = {
            "url": url,
            "suffix": src.media_format or 'mp4',
            "sub": [res for s in src.subtitles if (res := SubtitleSerializer(s).to_dict)]
        }

    result = {}

    sign_items = []

    for item in items:
        _url = None
        provider_type = ProviderType.get_type(item.provider)
        if provider_type == ProviderType.SIGNED:
            sign_items.append(item)
        elif provider_type == ProviderType.LOCAL:
            if item.url.startswith(('http://', 'https://', '/')):
                _url = item.url
            else:
                _url = f"/static/media/video/{item.url}"
        elif provider_type == ProviderType.DIRECT:
            _url = item.url
        else:
            pass

        if _url:
            _add_to_result(item, _url)

    if sign_items:
        pipeline = r.pipeline()
        need_cache = False
        cache_keys = [f's:{mid}:{item.uuid.hex}' for item in sign_items]
        try:
            cached_urls = r.mget(cache_keys)
        except RedisError:
            cached_urls = [None] * len(sign_items)

        for i, item in enumerate(sign_items):
            cache_key = cache_keys[i]
            cached_url = cached_urls[i]

            if cached_url:
                # when redis config set decode_responses=False/True,
                _url = cached_url.decode('utf-8') if isinstance(cached_url, bytes) else cached_url
                _add_to_result(item, _url)
            else:
                signed_url = URLSigner.get_cloud_url(item.provider, item.url)
                if signed_url:
                    _add_to_result(item, signed_url)
                    pipeline.setex(cache_key, timedelta(hours=4, minutes=57), signed_url)
                    if not need_cache:
                        need_cache = True

        if need_cache:
            try:
                pipeline.execute()
            except RedisError as e:
                current_app.logger.warning(f'Redis缓存签名URL失败: {e}')

    return {
        'signVideo': False,
        'playList': result
    }


def get_list_sign(items: list[TvSrc] | list[MovieSrc]) -> dict:
    result = {}
    for item in items:
        if item.url and item.url.strip():
            provider = item.provider
            ep_str = str(item.ep)
            quality_str = str(item.quality)
            if provider not in result:
                result[provider] = {}
            if ep_str not in result[provider]:
                result[provider][ep_str] = {}
            result[provider][ep_str][quality_str] = {
                # "is_active": item.is_active,
                "uuid": item.uuid.hex,
                "suffix": item.media_format,
            }
    return {
        'signVideo': True,
        'playList': result
    }


@dataclass
class BaseMediaSerializer(ABC):
    model: Any

    @property
    @abstractmethod
    def media_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def source_field(self):
        raise NotImplementedError

    # @property
    # @abstractmethod
    # def subtitle_field(self):
    #     raise NotImplementedError

    @property
    def to_brief_dict(self) -> Dict[str, Any]:
        return {
            'uuid': self.model.uuid.hex,
            'title': self.model.title,
            'description': self.model.description,
            'typ': self.media_type
        }

    def to_detail_dict(self, with_play_list: bool = False) -> Dict[str, Any]:
        data = {
            'uuid': self.model.uuid.hex,
            'title': self.model.title,
            'name': f"{self.model.title}{' / ' + self.model.e_title if self.model.e_title else ''}",
            'a_name': self.model.a_title,
            'release_date': self.model.release_date.strftime(
                "%Y-%m-%d") if self.model.release_date is not None else None,
            'end_date': None,
            'duration': None,
            'season': None,
            'network': None,
            'description': self.model.description,
            'storyline': self.model.storyline,
            'language': self.model.language,
            'country': self.model.country,
            'star': self.model.star,
            'rating': self.model.rating,
            'imdb': self.model.imdb,
            'genres': [genre.name for genre in self.model.genres],
            'tags': [tag.name for tag in self.model.tags],
            'actors': ' / '.join([actor.name for actor in self.model.actors]),
            'directors': ' / '.join([director.name for director in self.model.directors]),
            'update': self.model.update_at.strftime("%Y-%m-%d %H:%M"),
        }
        if hasattr(self.model, 'end_date') and self.model.end_date:
            data['end_date'] = self.model.end_date.strftime("%Y-%m-%d")

        if hasattr(self.model, 'season'):
            data['season'] = self.model.season

        if hasattr(self.model, 'network'):
            data['network'] = self.model.network

        if hasattr(self.model, 'duration'):
            data['duration'] = self.model.duration

        # if with_play_list:
        #     if current_app.config['SIGN_FOR_VIDEO']:
        #         data['src'] = get_list_sign(self.source_field)
        #     else:
        #         data['src'] = get_list(self.model.uuid.hex, self.source_field)
        #     pass

        return data


@dataclass
class MovieSerializer(BaseMediaSerializer):
    model: Movie

    @property
    def media_type(self) -> str:
        return 'mv'

    @property
    def source_field(self):
        return self.model.movie_src

    # @property
    # def subtitle_field(self):
    #     return self.model.subtitles


@dataclass
class TVShowSerializer(BaseMediaSerializer):
    model: TVShow

    @property
    def media_type(self) -> str:
        return 'tv'

    @property
    def source_field(self):
        return self.model.tv_src

    # @property
    # def subtitle_field(self):
    #     return self.model.subtitles


class SubtitleSerializer:
    def __init__(self, model: TVSubtitle | MovieSubtitle):
        if model is None:
            raise ValueError("SubtitleSerializer: no model")
        if not isinstance(model, (TVSubtitle, MovieSubtitle)):
            raise TypeError("SubtitleSerializer: wrong type")
        self.model = model

    def _handle_url(self):
        if self.model.url is None or not self.model.url.strip():
            return None
        if '/' not in self.model.url:
            return f'{pre_static_sub_path}{self.model.url}'
        return self.model.url

    @property
    def to_dict(self):
        url = self._handle_url()
        if not url:
            return None
        return {
            'language': self.model.language,
            'format': self.model.format,
            'url': url,
            'is_default': self.model.is_default,
            'fps': self.model.fps,
            'version': self.model.version,
        }
