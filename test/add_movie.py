"""
这个测试用来单独向数据库添加电影的相关数据 ，表结构在 mmedia-model.py ，相关 Movie,MovieSrc,TVSubtitle....
This file is used to add movie and related content to the database.  -- mmedia-model.py : Movie,MovieSrc,MovieSubtitle....

"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.mmedia.model import Genre, Tag, Actor, Director, Movie, MovieSrc, MovieSubtitle, mv_src_subtitle_table


SQLITE3_DIR = Path(__file__).resolve().parent.parent / 'mokmedia.db'
print('--- sqlite3 location ---:', SQLITE3_DIR)

# todo-mok 这里要改成你的数据库位置，上面sqlite，下面MariaDB或者MySql
# todo-mok Change this to your own database path, select one of: sqlite/MariaDB/MySql
engine = create_engine("sqlite:///" + str(SQLITE3_DIR))
# engine = create_engine("mysql+pymysql://user:password@host/mokmedia")

Session = sessionmaker(bind=engine)
session = Session()


def get_or_create(se, model, **kwargs):
    instance = se.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        se.add(instance)
        se.flush()
        return instance, True


def utc_time():
    return datetime.now(timezone.utc)
    # return datetime.now(timezone.utc).replace(microsecond=0)


def add_movie(title,
              e_title=None,
              p_title=None,
              a_title=None,
              release_date=None,
              duration=None,
              description=None,
              storyline=None,
              language=None,
              country=None,
              star=None,
              rating=None,
              imdb=None,
              genres=None,
              tags=None,
              actors=None,
              directors=None,
              sources=None,
              subtitles=None):

    if release_date and not release_date.strip() == '':
        release_date = datetime.strptime(release_date, "%Y-%m-%d").date()
    else:
        release_date = None

    movie = Movie(
        uuid=uuid.uuid4(),
        title=title,
        e_title=e_title,
        a_title=a_title,
        p_title=p_title or title[:3],  # 默认取前3字符 todo 转换为首字母缩写
        release_date=release_date,
        duration=duration,
        description=description,
        storyline=storyline,
        language=language,
        country=country,
        star=star,
        rating=rating,
        imdb=imdb,
        # create_at=utc_time(),
        # update_at=utc_time()
    )
    session.add(movie)
    session.flush()

    if genres:
        for name in genres:
            genre, _ = get_or_create(session, Genre, name=name)
            movie.genres.append(genre)

    if tags:
        for name in tags:
            tag, _ = get_or_create(session, Tag, name=name)
            movie.tags.append(tag)

    if actors:
        for name in actors:
            actor, _ = get_or_create(session, Actor, name=name)
            movie.actors.append(actor)

    if directors:
        for name in directors:
            director, _ = get_or_create(session, Director, name=name)
            movie.directors.append(director)

    src_objects = {}
    if sources:
        for index, src in enumerate(sources, start=1):
            source = MovieSrc(
                movie_id=movie.id,
                is_active=src.get('is_active', True),
                provider=src['provider'],
                media_format=src['media_format'],
                quality=src.get('quality', 720),
                width=src.get('width'),
                height=src.get('height'),
                ep=src.get('ep', 1),
                url=src['url'],
                # update_at=utc_time()
            )
            session.add(source)
            src_objects[index] = source
        session.flush()

    subtitle_objects = {}
    if subtitles:
        for sub in subtitles:
            subtitle = MovieSubtitle(
                movie_id=movie.id,
                language=sub['language'],
                format=sub.get('format'),
                url=sub['url'],
                is_default=sub.get('is_default', False),
                fps=sub.get('fps', None),
                version=sub.get('version', None),
                trans_group=sub.get('trans_group', None),
                # update_at=utc_time()
            )
            session.add(subtitle)
            subtitle_objects[sub['index']] = subtitle
        session.flush()

    for index, src in enumerate(sources, start=1):
        tv_src = src_objects[index]
        for sub_index in src.get('binding_subtitle_index', []):
            if sub_index in subtitle_objects:
                subtitle = subtitle_objects[sub_index]
                session.execute(mv_src_subtitle_table.insert().values(
                    mv_src_id=tv_src.id,
                    subtitle_id=subtitle.id
                ))

    try:
        session.commit()
        print(f"电影《{title}》添加成功！")
    except Exception as e:
        session.rollback()
        print(f"添加失败: {e}")


def delete_movie(**kwargs):
    try:
        movie = session.query(Movie).filter_by(**kwargs).first()
        if not movie:
            print(f"❌ 未找到电影: {kwargs}")
            return
        session.delete(movie)
        session.commit()
        print(f"✅ 电影{movie.title},id={movie.id}删除成功！")
    except Exception as e:
        session.rollback()
        print(f"❌ 添加失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":

    # delete_movie()  # id=1 | title=''

    try:

        add_movie(
            title="test222",
            e_title="Test(Hls)",
            p_title='hls',
            a_title='',
            release_date="2029-09-09",
            duration=100,
            description="ep1: 可以跨域normal, ep2: 跨域阻拦 blocked by CORS",
            storyline='',
            language='test',
            country="test",
            star=2,
            rating=3,
            imdb="",
            genres=[],
            actors=[],
            directors=[],
            sources=[
                {
                    'provider': 'other',
                    'media_format': 'm3u8',
                    'quality': 720,
                    'ep': 1,
                    'url': 'https://content.jwplatform.com/manifests/vM7nH0Kl.m3u8'
                },
                {
                    'provider': 'other',
                    # 'is_active': True,
                    'media_format': 'm3u8',
                    # 'width': ,
                    # 'height': ,
                    'quality': 480,
                    'ep': 2,
                    'url': 'https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8'
                },
                # ...more...
            ],
            # subtitles=[]
        )

        # add_movie(
        #     title="测试(HLS)",
        #     e_title="Test(Hls)",
        #     p_title='hls',
        #     a_title='',
        #     release_date="2029-09-09",
        #     duration=100,
        #     description="ep1: 可以跨域normal, ep2: 跨域阻拦 blocked by CORS",
        #     storyline='',
        #     language='test',
        #     country="test",
        #     star=2,
        #     rating=3,
        #     imdb="",
        #     genres=[],
        #     actors=[],
        #     directors=[],
        #     sources=[
        #         {
        #             'provider': 'other',
        #             'media_format': 'm3u8',
        #             'quality': 720,
        #             'ep': 1,
        #             'url': 'https://content.jwplatform.com/manifests/vM7nH0Kl.m3u8'
        #         },
        #         {
        #             'provider': 'other',
        #             # 'is_active': True,
        #             'media_format': 'm3u8',
        #             # 'width': ,
        #             # 'height': ,
        #             'quality': 480,
        #             'ep': 2,
        #             'url': 'https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8'
        #         },
        #         # ...more...
        #     ],
        #     # subtitles=[]
        # )

        # add_movie(
        #     title="流浪地球3",
        #     e_title="The Wandering Earth 3",
        #     p_title='lldq3',
        #     a_title='',
        #     release_date="2027-07-12",
        #     duration=170,
        #     description="他们必须携手合作",
        #     storyline="太阳即将毁灭，人类在地球表面建造出巨大的推进器，寻找新的家园。然而宇宙之路危机四伏，为了拯救地球，流浪地球时代的年轻人再次挺身而出，展开争分夺秒的生死之战。《流浪地球3》是《流浪地球》的前传，以提出计划将建造万座行星发动机的时代为故事背景，讲述了太阳危机即将来袭，世界陷入一片恐慌之中，人类将面临末日灾难与生命存续的双重挑战故事。",
        #     language="汉语普通话",
        #     country="中国",
        #     star=5,
        #     rating=9.6,
        #     imdb="tt11122334",
        #     genres=["冒险", "科幻", "灾难"],
        #     actors=["吴京", "刘德华", "李雪健", "沙溢", "john·miya"],
        #     directors=["郭帆"],
        #     sources=[
        #         {
        #             'binding_subtitle_index': [1],
        #             'provider': 'local',
        #             'media_format': 'mp4',
        #             'width': 1280,
        #             'height': 720,
        #             'quality': 720,
        #             'ep': 1,
        #             'url': 'test720p.mp4'
        #         },
        #         {
        #             # 'binding_subtitle_index': [],
        #             'provider': 'local',
        #             # 'is_active': True,
        #             'media_format': 'mp4',
        #             'width': 854,
        #             'height': 480,
        #             'quality': 480,
        #             'ep': 1,
        #             'url': 'test480p.mp4'
        #         },
        #
        #         # ...more...
        #     ],
        #     subtitles=[
        #         {
        #             "index": 1,
        #             "language": "zh",
        #             "url": "testEp1CN720.vtt",
        #             "format": "vtt",
        #             "is_default": True,
        #             "fps": 23.976,
        #             "version": "WEB-DL",
        #             "trans_group": "PTer",
        #         }
        #     ]
        # )

        print("添加成功ok")
    except Exception as err:
        print(f"添加失败error: {err}")
