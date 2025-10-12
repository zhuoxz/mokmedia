"""
SQLAlchemy 1.4和2.0
使用Mapped类型注释以后，默认的成为了 nullable=False
所以想列可以为空，要么手动设置nullable=True：
name: Mapped[str] = mapped_column(String(30), nullable=True)
要么把类型设定为[Optional[str]] ：
from typing import Optional
name: Mapped[Optional[str]] = mapped_column(String(30))
或者不用类型提示：
name = mapped_column(String(30))
官方文档说明：
    # not Optional[], therefore will be NOT NULL
      data: Mapped[str]
    # Optional[], therefore will be NULL
      additional_info: Mapped[Optional[str]]

说明： 为了方便，没有使用Episode表，在字幕TVSubtitle和播放源TvSrc中加了季数和集数冗余字段，这是需要优化的地方。
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing_extensions import Annotated

from sqlalchemy import (func, and_, Integer, SmallInteger, Uuid, Index, Float, Boolean, Date, String, Text,
                        Column, Table, TIMESTAMP, ForeignKey, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from ..extensions import db
from ..common import utc_time, bj_time


class Wish(db.Model):
    """  这里用的北京时区。 """
    __tablename__ = "wish"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='id')
    user: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(70), nullable=True)
    create_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=bj_time, nullable=False)

    @property
    def to_dict(self):
        return {'id': self.id, 'ip': self.ip, 'comment': self.comment}

    def __repr__(self):
        return '<id=%r comment=%r ip=%r create_at=%r>' % (self.id, self.comment, self.ip, self.create_at)


# 多对多 关联表
movie_genre_table = Table(
    'movie_genre', db.Model.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genre.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_mv_genre_genre_id', 'genre_id')
)

movie_tag_table = Table(
    'movie_tag', db.Model.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_mv_tag_mv_id', 'movie_id'),
    Index('idx_mv_tag_id', 'tag_id')
)

movie_actor_table = Table(
    'movie_actor', db.Model.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id', ondelete='CASCADE'), primary_key=True),
    Column('actor_id', Integer, ForeignKey('actor.id', ondelete='CASCADE'), primary_key=True)
)

movie_director_table = Table(
    'movie_director', db.Model.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id', ondelete='CASCADE'), primary_key=True),
    Column('director_id', Integer, ForeignKey('director.id', ondelete='CASCADE'), primary_key=True)
)

tv_genre_table = Table(
    'tv_genre', db.Model.metadata,
    Column('tv_id', Integer, ForeignKey('tv.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genre.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_tv_genre_genre_id', 'genre_id')
)

tv_tag_table = Table(
    'tv_tag', db.Model.metadata,
    Column('tv_id', Integer, ForeignKey('tv.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_tv_tag_tv_id', 'tv_id'),
    Index('idx_tv_tag_id', 'tag_id')
)

tv_actor_table = Table(
    'tv_actor', db.Model.metadata,
    Column('tv_id', Integer, ForeignKey('tv.id', ondelete='CASCADE'), primary_key=True),
    Column('actor_id', Integer, ForeignKey('actor.id', ondelete='CASCADE'), primary_key=True)
)

tv_director_table = Table(
    'tv_director', db.Model.metadata,
    Column('tv_id', Integer, ForeignKey('tv.id', ondelete='CASCADE'), primary_key=True),
    Column('director_id', Integer, ForeignKey('director.id', ondelete='CASCADE'), primary_key=True)
)

tv_src_subtitle_table = Table(
    'tv_src_subtitle', db.Model.metadata,
    Column('tv_src_id', Integer, ForeignKey('tv_src.id', ondelete='CASCADE'), primary_key=True),
    Column('subtitle_id', Integer, ForeignKey('tv_subtitle.id', ondelete='CASCADE'), primary_key=True),
)

mv_src_subtitle_table = Table(
    'mv_src_subtitle', db.Model.metadata,
    Column('mv_src_id', Integer, ForeignKey('movie_src.id', ondelete='CASCADE'), primary_key=True),
    Column('subtitle_id', Integer, ForeignKey('movie_subtitle.id', ondelete='CASCADE'), primary_key=True),
)

#  通用列
int_pk = Annotated[int, mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='id')]
uuid_pk = Annotated[uuid.UUID, mapped_column(Uuid(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, comment="对外id")]


class MovieSrc(db.Model):
    __tablename__ = "movie_src"

    id: Mapped[int_pk]
    #  Movie记录删除时不删除MovieSrc记录，只把MovieSrc的movie_id外键置空(movie_id要可以为空nullable=True)
    # movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movie.id', ondelete='SET NULL'), nullable=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movie.id', ondelete='CASCADE'), nullable=False)
    uuid: Mapped[uuid_pk]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="链接是否有效,默认有效")
    provider: Mapped[str] = mapped_column(String(20), nullable=False, comment='来源。本地，直连，签名3种类型')
    media_format: Mapped[str | None] = mapped_column(String(10), nullable=True, default='mp4', comment='媒体类型')
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='画面宽')
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='画面高')
    quality: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=720, comment='画质/默认当他720(720/1080/2160)')
    ep: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,  comment='集数, 如果有上中下')
    url: Mapped[str | None] = mapped_column(String(2083), nullable=True, comment='本地:x.mp4，直连:播放链接，签名:原始链接')
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)
    movie = relationship('Movie', back_populates='movie_src')
    # 与字幕没有反向关系
    subtitles = relationship('MovieSubtitle', secondary=mv_src_subtitle_table)

    __table_args__ = (
        # CheckConstraint(
        #     '(file_name IS NOT NULL OR url IS NOT NULL)',
        #     name='check_file_path_or_url'
        # ),
        Index('idx_mv_src_movie_id_provider', 'movie_id', 'provider'),
        Index('idx_mv_src_movie_id_is_active', 'movie_id', 'is_active'),
        Index('idx_mv_src_uuid', 'uuid'),
        Index('idx_mv_src_provider', 'provider'),
        # NOTE: 如果ep集数可以为空,唯一约束不起效,可能重复添加.
        UniqueConstraint('movie_id', 'provider', 'ep', 'quality', name='uq_movie_src'),
    )

    @hybrid_property
    def is_valid_url(self):
        if not self.url:
            return False
        _url = self.url.strip()
        return _url != '' and _url.lower() not in {'null', 'none'}

    @is_valid_url.expression
    def is_valid_url(cls):  # noqa
        trimmed = func.trim(cls.url)
        return and_(
            cls.url.isnot(None),
            trimmed != '',
            func.lower(trimmed).not_in(['null', 'none'])
        )

    def __repr__(self):
        return '<id=%r provider=%r ep=%r url=%r>' % (self.id, self.provider, self.ep, self.url)


class TvSrc(db.Model):
    __tablename__ = "tv_src"

    id: Mapped[int_pk]
    tv_id: Mapped[int] = mapped_column(Integer, ForeignKey('tv.id', ondelete='CASCADE'), nullable=False)
    uuid: Mapped[uuid_pk]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="链接是否有效,默认有效")
    provider: Mapped[str] = mapped_column(String(20), nullable=False, comment='来源。本地，直连，签名3种类型')
    media_format: Mapped[str | None] = mapped_column(String(10), nullable=True, default='mp4', comment='类型')
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='画面宽')
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='画面高')
    quality: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=720, comment='画质/默认当他720(720/1080/2160)')
    season: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment='冗余字段，季数')
    ep: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment='冗余字段，集数')
    url: Mapped[str | None] = mapped_column(String(2083), nullable=True, comment='本地:x.mp4，直连:播放链接，签名:原始链接')
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)

    tv_show = relationship('TVShow', back_populates='tv_src')
    # 与字幕没有反向关系
    subtitles = relationship('TVSubtitle', secondary=tv_src_subtitle_table)
    __table_args__ = (
        Index('idx_tv_src_tv_id_provider', 'tv_id', 'provider'),
        Index('idx_tv_src_tv_id_is_active', 'tv_id', 'is_active'),
        Index('idx_tv_src_provider', 'provider'),
        Index('idx_tv_src_uuid', 'uuid'),
        UniqueConstraint('tv_id', 'provider', 'ep', 'quality', name='uq_tv_src'),
    )

    @hybrid_property
    def is_valid_url(self):
        if not self.url:
            return False
        _url = self.url.strip()
        return _url != '' and _url.lower() not in {'null', 'none'}

    @is_valid_url.expression
    def is_valid_url(cls):  # noqa
        trimmed = func.trim(cls.url)
        return and_(
            cls.url.isnot(None),
            trimmed != '',
            func.lower(trimmed).not_in(['null', 'none'])
        )

    def __repr__(self):
        return '<id=%r provider=%r ep=%r url=%r>' % (self.id, self.provider, self.ep, self.url)


class Movie(db.Model):
    __tablename__ = 'movie'
    id: Mapped[int_pk]
    uuid: Mapped[uuid_pk]
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='电影名称')
    e_title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='英语名称')
    a_title: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="别名")
    p_title: Mapped[str | None] = mapped_column(String(40), nullable=True, comment='首字母缩写')
    release_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="上映日期")
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='片长')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='简介')
    storyline: Mapped[str | None] = mapped_column(Text, nullable=True, comment="故事线")
    language: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='语言')
    country: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='国家')
    star: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="星级")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, comment="评分")
    imdb: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="imdb编号")
    create_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, nullable=False)
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)

    #     movie_src = relationship('MovieSrc', back_populates='movie', uselist=False)
    movie_src = relationship('MovieSrc', back_populates='movie', cascade="all, delete-orphan")
    # movie_src = relationship('MovieSrc', back_populates='movie', cascade="all, delete-orphan", passive_deletes=True)
    subtitles = relationship('MovieSubtitle', back_populates='movie', cascade="all, delete-orphan")
    genres = relationship('Genre', secondary=movie_genre_table, back_populates='movies')
    tags = relationship('Tag', secondary=movie_tag_table, back_populates='movies')
    actors = relationship('Actor', secondary=movie_actor_table, back_populates='movies')
    directors = relationship('Director', secondary=movie_director_table, back_populates='movies')

    __table_args__ = (
        UniqueConstraint('title', 'e_title', 'release_date', 'country', 'imdb', name='un_movie'),
        Index('idx_mv_uuid', 'uuid'),
        Index('idx_movie_update_at', update_at.desc()),
    )


class TVShow(db.Model):
    __tablename__ = 'tv'
    id: Mapped[int_pk]
    uuid: Mapped[uuid_pk]
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='电视剧名称')
    e_title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='英语名称')
    a_title: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="别名")
    p_title: Mapped[str | None] = mapped_column(String(40), nullable=True, comment='首字母缩写')
    release_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="上映日期")
    # duration: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='片长')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='简介')
    storyline: Mapped[str | None] = mapped_column(Text, nullable=True, comment="故事线")
    language: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='语言')
    country: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='国家')
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment='完结日期')
    network: Mapped[str | None] = mapped_column(String(20), nullable=True, comment='播出平台')
    season: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="季数")
    star: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="星级")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, comment="评分")
    imdb: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="imdb编号")
    create_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, nullable=False)
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)
    tv_src = relationship('TvSrc', back_populates='tv_show', cascade="all, delete-orphan")
    # tv_src = relationship('TvSrc', back_populates='tv_show', cascade="all, delete-orphan", passive_deletes=True)
    subtitles = relationship('TVSubtitle', back_populates='tv_show', cascade="all, delete-orphan")
    genres = relationship('Genre', secondary=tv_genre_table, back_populates='tv_shows')
    actors = relationship('Actor', secondary=tv_actor_table, back_populates='tv_shows')
    directors = relationship('Director', secondary=tv_director_table, back_populates='tv_shows')
    tags = relationship('Tag', secondary=tv_tag_table, back_populates='tv_shows')
    episodes = relationship('Episode', back_populates='tv_show', cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('title', 'e_title', 'release_date', 'country', 'imdb', 'season', name='un_tv_show'),
        Index('idx_tv_uuid', 'uuid'),
        # Index('idx_tv_update_at', update_at.desc(), 'id'),
        Index('idx_tv_update_at', update_at.desc()),
    )


class Episode(db.Model):
    __tablename__ = 'episode'
    id: Mapped[int_pk]
    tv_id: Mapped[int] = mapped_column(Integer, ForeignKey('tv.id', ondelete='CASCADE'), nullable=False,
                                       comment='TVShow外键')
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='集标题')
    season: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="第几季")
    episode: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="第几集")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='简介')
    duration: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='片长')
    air_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="发布日期")

    tv_show = relationship('TVShow', back_populates='episodes')
    subtitles = relationship('TVSubtitle', back_populates='episode')


class Genre(db.Model):
    __tablename__ = 'genre'
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies = relationship('Movie', secondary=movie_genre_table, back_populates='genres')
    tv_shows = relationship('TVShow', secondary=tv_genre_table, back_populates='genres')


class Tag(db.Model):
    __tablename__ = 'tag'
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    movies = relationship('Movie', secondary=movie_tag_table, back_populates='tags')
    tv_shows = relationship('TVShow', secondary=tv_tag_table, back_populates='tags')


class Actor(db.Model):
    __tablename__ = 'actor'
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(90), nullable=False, comment='演员')
    birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment='生日')
    nationality: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='国籍')

    movies = relationship('Movie', secondary=movie_actor_table, back_populates='actors')
    tv_shows = relationship('TVShow', secondary=tv_actor_table, back_populates='actors')


class Director(db.Model):
    __tablename__ = 'director'
    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(90), nullable=False, comment='导演')
    birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment='生日')
    nationality: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='国籍')

    movies = relationship('Movie', secondary=movie_director_table, back_populates='directors')
    tv_shows = relationship('TVShow', secondary=tv_director_table, back_populates='directors')


# 电影字幕表
class MovieSubtitle(db.Model):
    __tablename__ = 'movie_subtitle'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_pk]
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movie.id', ondelete='CASCADE'))
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=True)
    url: Mapped[str] = mapped_column(String(2083), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True, comment='版本: BluRay, DVD, WEB-DL...')
    trans_group: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='翻译小组')
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)

    movie = relationship('Movie', back_populates='subtitles')

    # __table_args__ = (
    #     UniqueConstraint('movie_id', 'language', 'format', 'trans_group', 'fps', 'version', name='uq_movie_subtitle'),
    # )


# 电视剧字幕表
class TVSubtitle(db.Model):
    __tablename__ = 'tv_subtitle'

    id: Mapped[int_pk]
    uuid: Mapped[uuid_pk]
    tv_id: Mapped[int] = mapped_column(Integer, ForeignKey('tv.id', ondelete='CASCADE'))
    episode_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('episode.id', ondelete='CASCADE'),
                                                   nullable=True)
    season: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='冗余季数字段')
    ep: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment='冗余集数字段')
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    format: Mapped[str | None] = mapped_column(String(10), nullable=True)
    url: Mapped[str] = mapped_column(String(2083), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True, comment='版本: BluRay, DVD, WEB-DL...')
    trans_group: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='翻译小组')
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_time, onupdate=utc_time,
                                                nullable=False)

    tv_show = relationship('TVShow', back_populates='subtitles')
    episode = relationship('Episode', back_populates='subtitles')

    # __table_args__ = (
    #     UniqueConstraint('episode_id', 'language', 'format', 'ep', 'trans_group', 'fps', 'version',  name='uq_tv_subtitle'),
    # )
