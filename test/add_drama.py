"""
这个测试用来单独向数据库添加电视剧/短剧一类的相关数据 ，表结构在 mmedia-model.py ，相关 TVShow,TvSrc,TVSubtitle....
This file is used to add drama/short-drama and related content to the database.  -- mmedia-model.py : TVShow,TvSrc,TVSubtitle....
"""

import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.mmedia.model import Genre, Tag, Actor, Director, TVShow, TvSrc, TVSubtitle, Episode, tv_src_subtitle_table


SQLITE3_DIR = Path(__file__).resolve().parent.parent / 'mokmedia.db'
print('--- sqlite3 location ---:', SQLITE3_DIR)

# todo 这里要改成你的数据库位置，上面sqlite，下面MariaDB或者MySql
# todo Change this to your own database path, select one of: sqlite/MariaDB/MySql
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


def set_time():
    return datetime.now(ZoneInfo("UTC"))


def add_drama(title,
              e_title=None,
              a_title=None,
              p_title=None,
              release_date=None,
              end_date=None,
              description=None,
              storyline=None,
              language=None,
              country=None,
              network=None,
              season=None,
              star=None,
              rating=None,
              imdb=None,
              genres=None,
              tags=None,
              actors=None,
              directors=None,
              episodes_data=None,
              tv_sources=None,
              tv_subtitles=None,
              tv_episodes=None
              ):
    if release_date and not release_date.strip() == '':
        release_date = datetime.strptime(release_date, "%Y-%m-%d").date()
    else:
        release_date = None

    if end_date and not end_date.strip() == '':
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = None

    drama = TVShow(
        # uuid=uuid.uuid4(),
        title=title,
        e_title=e_title,
        a_title=a_title,
        p_title=p_title or title[:3],
        release_date=release_date,
        end_date=end_date,
        description=description,
        storyline=storyline,
        language=language,
        country=country,
        network=network,
        season=season,
        star=star,
        rating=rating,
        imdb=imdb,
        # create_at=set_time(),
        # update_at=set_time()
    )
    session.add(drama)
    session.flush()

    if genres:
        for name in genres:
            genre, _ = get_or_create(session, Genre, name=name)
            drama.genres.append(genre)

    if tags:
        for name in tags:
            tag, _ = get_or_create(session, Tag, name=name)
            drama.tags.append(tag)

    if actors:
        for name in actors:
            actor, _ = get_or_create(session, Actor, name=name)
            drama.actors.append(actor)

    if directors:
        for name in directors:
            director, _ = get_or_create(session, Director, name=name)
            drama.directors.append(director)

    tv_src_objects = {}
    if tv_sources:
        for index, src in enumerate(tv_sources, start=1):
            tv_src = TvSrc(
                tv_id=drama.id,
                # uuid=uuid.uuid4(),
                is_active=src.get('is_active', True),
                provider=src['provider'],
                media_format=src.get('media_format', 'mp4'),
                quality=src.get('quality', 480),
                width=src.get('width', None),
                height=src.get('height', None),
                url=src['url'],
                season=src.get('season', 1),
                ep=src['ep']
                # update_at=set_time()
            )
            session.add(tv_src)
            tv_src_objects[index] = tv_src
        session.flush()

    subtitle_objects = {}
    if tv_subtitles:
        for sub in tv_subtitles:
            subtitle = TVSubtitle(
                tv_id=drama.id,
                # episode_id=None,
                episode_id=sub.get('episode_id'),
                language=sub['language'],
                season=sub.get('season', 1),
                ep=sub.get('ep', None),
                format=sub.get('format', None),
                version=sub.get('version', None),
                fps=sub.get('fps', None),
                trans_group=sub.get('trans_group', None),
                url=sub['url'],
                is_default=sub.get('is_default', False)
                # update_at=set_time()
            )
            session.add(subtitle)
            subtitle_objects[sub['index']] = subtitle
        session.flush()

    for index, src in enumerate(tv_sources, start=1):
        tv_src = tv_src_objects[index]
        for sub_index in src.get('binding_subtitle_index', []):
            if sub_index in subtitle_objects:
                subtitle = subtitle_objects[sub_index]
                session.execute(tv_src_subtitle_table.insert().values(
                    tv_src_id=tv_src.id,
                    subtitle_id=subtitle.id
                ))

    if tv_episodes:
        for ep in tv_episodes:
            episode = Episode(
                tv_id=drama.id,
                title=ep['title'],
                season=ep['season'],
                episode=ep['episode'],
                description=ep['description'],
                duration=ep['duration'],
                air_date=ep['air_date'],
            )
            session.add(episode)
            session.flush()

    # if episodes_data:
    #     for season_info in episodes_data:
    #         season_num = season_info['season']
    #
    #         for ep_data in season_info.get('episodes', []):
    #             air_date = None
    #             if ep_data.get('release_date'):
    #                 try:
    #                     air_date = datetime.strptime(ep_data['release_date'], "%Y-%m-%d").date()
    #                 except ValueError:
    #                     air_date = None
    #
    #             episode = Episode(
    #                 tv_id=drama.id,
    #                 season=season_num,
    #                 episode=ep_data['episode'],
    #                 title=ep_data.get('title', f"第{ep_data.get('episode')}集"),
    #                 duration=ep_data.get('duration', None),
    #                 description=ep_data.get('description', None),
    #                 air_date=air_date
    #                 # create_at=set_time(),
    #                 # update_at=set_time()
    #             )
    #             session.add(episode)
    #             session.flush()
    #
    #             for src in ep_data.get('sources', []):
    #                 ep_src = TvSrc(
    #                     tv_id=drama.id,
    #                     # uuid=uuid.uuid4(),
    #                     is_active=src.get('is_active', True),
    #                     provider=src['provider'],
    #                     media_format=src['media_format'],
    #                     quality=src.get('quality', 480),
    #                     width=src.get('width', None),
    #                     height=src.get('height', None),
    #                     ep=ep_data['episode'],
    #                     url=src['url'],
    #                     # update_at=set_time()
    #                 )
    #                 session.add(ep_src)
    #
    #             for sub in ep_data.get('subtitles', []):
    #                 ep_subtitle = TVSubtitle(
    #                     # uuid=uuid.uuid4(),
    #                     tv_id=drama.id,
    #                     episode_id=episode.id,
    #                     season=sub.get('season', None),
    #                     ep=ep_data['episode'],
    #                     language=sub['language'],
    #                     url=sub['url'],
    #                     format=sub['format'],
    #                     version=sub.get('version', None),
    #                     trans_group=sub.get('trans_group', None),
    #                     fps=sub.get('fps', None),
    #                     is_default=sub.get('is_default', False),
    #                     # update_at=set_time()
    #                 )
    #                 session.add(ep_subtitle)

    try:
        session.commit()
        print(f"✅ 电视剧《{title}》添加成功！UUID: {drama.id} {drama.uuid}")
        return drama
    except Exception as e:
        session.rollback()
        print(f"❌ 添加失败: {e}")
        raise
    finally:
        if session.is_active:
            session.close()


def delete_drama(**kwargs):
    try:
        tv_show = session.query(TVShow).filter_by(**kwargs).first()
        if not tv_show:
            print(f"❌ 未找到电视剧: {kwargs}")
            return
        session.delete(tv_show)
        session.commit()
        print(f"✅ 电视剧{tv_show.title},id={tv_show.id}删除成功！")
    except Exception as e:
        session.rollback()
        print(f"❌ 添加失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # 删除电视剧 delete drama
    # delete_drama(title="无耻之徒")
    # delete_drama(id=1)

    try:

        add_drama(
            title="我投喂了古代大将军222",
            e_title="",
            a_title="",
            p_title="wtwlgddjj",
            release_date="2024-09-08",
            end_date="2027-05-03",
            description="倒狗粮，得黄金，现代女孩的神秘聚宝盆，古代将军的财富源泉。",
            storyline="富家千金林宛瑜，意外发现自家狗狗吃饭的聚宝盆连通古今，与两千年前的少年冠军侯霍渊相识，恰逢异族入侵，百姓民不聊生，更有饥荒伴随，霍渊率霍家军，独守国门，直至弹尽粮绝，好在祈求神明庇佑之时，通过聚宝盆呼应上了林宛瑜，从此，得到林宛瑜投喂娇养的少年大将军，带领军民横扫异族，捍卫国土，使天下海晏河清！",
            language="国语",
            country="中国",
            network="果果",
            season=1,
            star=5,
            rating=8.1,
            imdb="tt11223306",
            genres=["短剧", "古装"],
            tags=[],
            actors=['李柯以', '王宇威'],
            directors=['不知道啊'],
            tv_sources=[
                {
                    "binding_subtitle_index": [],  # tv_subtitles item -> key: 'index'
                    "provider": "本站",
                    'is_active': True,
                    "media_format": "mp4",
                    "quality": 720,
                    "width": 1280,
                    "height": 720,
                    "season": 1,
                    "ep": 1,
                    "url": "test720p.mp4"
                },
                {
                    "binding_subtitle_index": [],
                    "provider": "本站",
                    'is_active': True,
                    "media_format": "mp4",
                    "quality": 480,
                    "width": 854,
                    "height": 480,
                    "season": 1,
                    "ep": 1,
                    "url": "test480p.mp4"
                },
                {
                    "binding_subtitle_index": [],
                    "provider": "外站",
                    'is_active': True,
                    "media_format": "mp4",
                    "quality": 480,
                    "width": 720,
                    "height": 576,
                    "season": 1,
                    "ep": 1,
                    "url": "https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-576p.mp4"
                },
                {
                    "binding_subtitle_index": [],
                    "provider": "外站",
                    # 'is_active': True,
                    "media_format": "mp4",
                    "quality": 720,
                    "width": 1280,
                    "height": 720,
                    "season": 1,
                    "ep": 1,
                    "url": "https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-720p.mp4"
                },
                {
                    "binding_subtitle_index": [],
                    "provider": "外站",
                    # 'is_active': True,
                    "media_format": "mp4",
                    "quality": 1080,
                    "width": 1920,
                    "height": 1080,
                    "season": 1,
                    "ep": 1,
                    "url": "https://cdn.plyr.io/static/demo/View_From_A_Blue_Moon_Trailer-1080p.mp4"
                },
                {
                    "binding_subtitle_index": [],
                    "provider": "外站",
                    # 'is_active': True,
                    "media_format": "mp4",
                    "quality": 480,
                    "width": 854,
                    "height": 480,
                    "season": 1,
                    "ep": 2,
                    "url": "https://media.w3.org/2010/05/sintel/trailer.mp4"
                },
            ],
            # tv_subtitles=[]
        )

        # add_drama(
        #     title="无耻之徒",
        #     e_title="Shameles",
        #     a_title="无耻家庭",
        #     p_title="wczt",
        #     release_date="2027-04-01",
        #     end_date="2027-05-03",
        #     description="在芝加哥南部的一个工人阶级社区中，加拉格尔家族继续他们的混乱生活。尽管父亲弗兰克的缺席，这个大家庭依旧面临着经济困境、法律问题和个人挑战，但他们总能找到办法生存下去。",
        #     storyline="随着时间的推移，每个家庭成员都在为自己的未来而奋斗。伊恩终于找到了真爱，并开始考虑组建自己的家庭；莉普努力戒酒并试图成为更好的父亲；黛比则在寻找平衡工作与照顾孩子的道路；凯尔西在大学里追求她的梦想，同时也在探索自己的性取向；而卡门，作为最小的孩子，正在经历青春期的成长烦恼。",
        #     language="英语",
        #     country="美国",
        #     network="QiDia",
        #     season=12,
        #     star=5,
        #     rating=9.1,
        #     imdb="tt33669912",
        #     genres=["剧情", "喜剧"],
        #     tags=[],
        #     actors=['Beth Jimenez', 'Christopher Avery', 'Terri Perez', 'Erica Herrera'],
        #     directors=["Troy Lyons", 'Michael Wood'],
        #     tv_sources=[
        #         {
        #             "binding_subtitle_index": [1],  # tv_subtitles item -> key: 'index'
        #             "provider": "外链1",
        #             'is_active': True,
        #             "media_format": "mp4",
        #             "quality": 720,
        #             "width": 1280,
        #             "height": 538,
        #             "season": 12,
        #             "ep": 1,
        #             "url": "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4"
        #         },
        #         {
        #             "binding_subtitle_index": [3],
        #             "provider": "外链1",
        #             'is_active': True,
        #             "media_format": "mp4",
        #             "quality": 480,
        #             "width": 854,
        #             "height": 480,
        #             "season": 12,
        #             "ep": 1,
        #             "url": "https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-480p.mp4"
        #         },
        #         {
        #             "binding_subtitle_index": [2],
        #             "provider": "外链1",
        #             'is_active': True,
        #             "media_format": "mp4",
        #             "quality": 480,
        #             "width": 854,
        #             "height": 480,
        #             "season": 12,
        #             "ep": 2,
        #             "url": "https://media.w3.org/2010/05/sintel/trailer.mp4"
        #         },
        #     ],
        #     tv_subtitles=[
        #         {
        #             "index": 1,
        #             "language": "cn",
        #             "url": "testEp1CN720.vtt",
        #             "format": "vtt",
        #             "is_default": True,
        #             "fps": 23.976,
        #             "version": "WEB-DL",
        #             "trans_group": "PTer",
        #             "season": 12,
        #             "ep": 1
        #         },
        #         {
        #             "index": 2,
        #             "language": "en",
        #             "url": "testEp1EN480.vtt",
        #             "format": "vtt",
        #             "is_default": True,
        #             "fps": 23.976,
        #             "version": "WEB-DL",
        #             "trans_group": "PTer",
        #             "season": 12,
        #             "ep": 2
        #         },
        #         {
        #             "index": 3,
        #             "language": "en",
        #             "url": "testEp2EN480.vtt",
        #             "format": "vtt",
        #             "is_default": True,
        #             "fps": 23.976,
        #             "version": "WEB-DL",
        #             "trans_group": "PTer",
        #             "season": 12,
        #             "ep": 1
        #         }
        #     ]
        # )

        print("🎉 电视剧添加成功")
    except Exception as err:
        print(f"❌ 添加失败: {err}")
