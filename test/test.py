import os
import time
import uuid
from hashlib import md5
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

print('\n------ tencent sign -------')
tencent_url = 'https://1211173225.vod-qcloud.com/7caa8d9eiodnq1329147621/f8cf66c65245303962159501257/caU0GZmlFL6A.mp4'
_qq_key = '111'
def tencent_sign(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        query_dict = parse_qs(parsed.query, keep_blank_values=True)
        expire_at = format(int(time.time()) + 18060, 'x')
        rlimit = 5
        directory = os.path.dirname(parsed.path) + '/'
        to_sign = f"{_qq_key}{directory}{expire_at}{rlimit}"
        sign = md5(to_sign.encode('utf-8')).hexdigest()
        query_dict['t'] = [expire_at]
        query_dict['rlimit'] = [str(rlimit)]
        query_dict['sign'] = [sign]
        new_query = urlencode(query_dict, doseq=True)
        signed_url = urlunparse(parsed._replace(query=new_query))
        return signed_url
    except:
        return None
print('url: ',tencent_sign(tencent_url))
print('------ tencent sign  end-------\n')

print('------ aliyun sign -------')
ali_url = 'http://example.aliyundoc.com/video/standard/test.mp4'
_ali_key = '111'
def url_sign_ali(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        query_dict = parse_qs(parsed.query, keep_blank_values=True)
        timestamp = str(int(time.time()))
        rand = '0'
        to_sign = f"{parsed.path}-{timestamp}-{rand}-0-{_ali_key}"
        md5_hash = md5(to_sign.encode('utf-8')).hexdigest()
        query_dict['auth_key'] = [f'{timestamp}-{rand}-0-{md5_hash}']
        new_query = urlencode(query_dict, doseq=True)
        signed_parsed = parsed._replace(query=new_query)
        signed_url = urlunparse(signed_parsed)
        return signed_url
    except:
        return None
print('url: ', url_sign_ali(ali_url))
print('------ aliyun sign  end-------\n')


print('------ local sign -------')
_sid = 'd35c4f6ebdda437e80206c16e4510380'
expire = 17537100333 + 18060
_local_key = '111'

def url_sign(sid: uuid.UUID | str, t: int) -> str:
    if isinstance(sid, uuid.UUID):
        sid = sid.hex
    string = f'{sid}{_local_key}{format(t, 'x')}'.encode()
    sign = md5(string).hexdigest()
    return sign
token = url_sign(_sid, expire)
print('url_sign token: ', token)

print('------ validate sign -------')
def validate_sign(sid: uuid.UUID | str, sign: str, t: str) -> bool:
    if isinstance(sid, uuid.UUID):
        sid = sid.hex
    try:
        string = f'{sid}{_local_key}{t}'.encode()
        token = md5(string).hexdigest()
        if token == sign:
            return True
        else:
            return False
    except:
        return False
print('validate_sign: ',validate_sign(_sid, token, format(expire, 'x')))


# from faker import Faker
# fake = Faker()
# for i in range(10):
#     print(f'{fake.name()}\n')

