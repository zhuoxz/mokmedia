# MokMedia

一个简易的视频播放网站。这是我的 Flask 练习项目，前端原生js。基本上能用，但是后台管理没写。  

A simple online media streaming platform based on Flask, supporting authentication, caching, and multiple playback sources.

---

## 功能特性 | Features

- **视频播放**：支持多种画质，支持字幕  
  **Video Playback**: Supports multiple resolutions and subtitles

- **多播放源**：支持本地文件、直链 URL、第三方云服务商（如腾讯云、阿里云）  
  **Multiple Sources**: Supports local files, direct URLs, and third-party cloud services (e.g., Tencent Cloud, Alibaba Cloud)

- **用户认证**：基于 JWT，支持 Cookie（含 CSRF 保护）或 Header 两种验证方式  
  **User Authentication**: JWT-based, supports Cookie (with CSRF protection) or Authorization Header

- **防盗链**：支持本地 key 防盗链，支持为云播放链接动态签名  
  **signed URLs**: supports sign for url, dynamic signing for cloud video URLs

## 使用的框架 | Tech Stack

- **后台 | Backend**  
  - **Python 3.10+**:（开发环境：Python 3.12）| (development in Python 3.12)  
  - Flask , Flask-SQLAlchemy , Flask-JWT-Extended , Flask-Caching , Flask-Limiter , Captcha , user-agents  

- **前端 | Frontend**  
  - Bootstrap5 , Plyr.js , Swiper , Axios , lazysizes.min.js  

- **数据库**  
  - **SQLite**：开发调试 | Development & Debugging  
  - **MariaDB or MySQL**：生产部署 | Production Deployment  
  - **Redis**  

---

## 快速开始 | Quick Start

1. **克隆或者下载项目 | Clone the repo**  

    ```bash
    git clone https://github.com/cockle/mokmedia
    cd mokmedia
    ```

2. **安装依赖 | Install dependencies**  

    ```bash
    pip install -r requirements.txt
    ```

    如果安装出现错误，尝试： | If installation fails, try:
    
    ```bash
    # 或者手动安装文件里的模块 | Or install packages manually from the file
    pip install -r requirements-min.txt
    ```

3. **运行 | Run**  

    ```bash
    python run.py
    ```  

浏览器中打开 | Open your browser at:   http://localhost:5000  

---

## 部署 | Deployment

Flask + Uwsgi + Nginx

1. **额外安装项 | Install additional dependencies**  

    ```bash
    # 数据库驱动 | Database Connector:
    pip install mariadb  # or pymysql or mysql-connector-python

    # UWSGI
    pip install uwsgi
 
    # install mariadb nginx and redis server
    # 如果服务器没有的话 | if you haven't installed yet, run:
    sudo apt install mariadb-server  # or mysql-server
    sudo apt install nginx
    sudo apt install redis-server -y
    ```

2. **配置Redis | Configure Redis**  

    编辑文件：| Edit: `app -> extensions.py`  

    ```python
    # 注释掉或者删除'Option1'部分，打开'Option2'部分的注释
    # comment out or delete 'Option1' section, uncomment 'Option2' section
    # 然后设置 Redis 连接 | Then set redis connection
    redis_url = 'redis://...'
    ```

3. **配置数据库 | Configure the database**  

    创建数据库 `mokmedia` ，然后编辑 `config.py` 文件：  

    Create database `mokmedia` , then edit `config.py` fil  e:  

    ```python
    # mariadb+mariadbconnector://  |  mysql+pymysql://  |  mysql+mysqlconnector://
    # todo-mok : 连接数据库，mariadb或者mysql | set database： mariadb or mysql
    SQLALCHEMY_DATABASE_URI = 'your database url /mokmedia'
    ```

4. **将密码添加到服务器的环境变量中 | Set environment variables**  

    ```bash
    # 必须 | Required: CLEAN_CACHE_PASSWORD, PLAY_PASSWORD, SECRET_KEY, JWT_SECRET_KEY
    # 可选 | Optional: LOCAL_SIGN_KEY, TENCENT_VIDEO_KEY, ALI_VIDEO_KEY,  others...
    export SECRET_KEY= ''  JWT_SECRET_KEY=''  # more...
    ```

5. **其他 | Other**  

    编辑文件：| In: `run.py`  

    ```python
    # Development
    # app = create_app("develop")
    # app.run(host='0.0.0.0', debug=True)

    # Production
    app = create_app("product")
    app.run()
    ```

    编辑文件：| In: `app -> mmedia -> views.py`  

    ```python
    def play(mid: str, sid: str):
        # 注释掉 Development |  Comment Development section
        # return redirect(f'/static/media/video/{url}', code=302)

        # 打开 Production    |  Uncomment Production section
        response = make_response()
        response.headers['X-Accel-Redirect'] = '/protected/videos/' + url
        return response
    ```
  
    编辑文件：| In: `app -> api -> views.py`  

    ```python
    # /api/login 接口： 注释或删除 Option 2 函数， 取消 Option 1 的注释
    # For the /api/login endpoint: comment out or delete the Option 2 function, and uncomment the Option 1 function.

    # 取消注释  |  Uncomment this route
    @api_blue.route('/api/login', methods=['POST'])
    @add_id_cookie('u_id', max_age=2592000) 
    def login(u_id):
        """
        Option 1
        当redis出错，禁止登录 | When redis crashed, disable user login
        """
        # ...

    # 注释这个方法  |  Comment out this route
    #@api_blue.route('/api/login', methods=['POST'])
    # @add_id_cookie('u_id', max_age=2592000)
    # @limiter.limit("22/hour")
    # def login(u_id):
        #     """
        #     Option 2
        #     当redis出错，依然允许登录尝试 | even redis crashed，still allow login attempts.
        #     """

        # ...
    ```

6. **Uwsgi**

    编辑(示例)文件：| In: `uwsgi.ini`  

    ```ini
    # 项目根目录 | Project Directory
    basedir = 
    # 虚拟环境根目录 | Virtual Environment Directory
    virtualenv =
    ```

    创建 systemd 服务文件 | create systemd file (/etc/systemd/system/mokmedia.service)：  

    ```bash
    sudo nano /etc/systemd/system/mokmedia.service
    ```
  
    ```ini
    [Unit]
    Description=uWSGI instance for mokmedia
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory= #你的项目路径 | your project directory
    ExecStart=  /...path.../.pyenv/versions/mokmedia/bin/uwsgi --ini uwsgi.ini 
    KillSignal=SIGQUIT
    Type=notify
    NotifyAccess=all
    Restart=always
    TimeoutStopSec=10

    [Install]
    WantedBy=multi-user.target
    ```

7. **Nginx**  
   
    nginx配置文件参考: | Configuration File Example:

    ```nginx
    server {
        listen 80;

        # Domain
        server_name your.domain;

        # 项目静态文件根目录  | Project static files root directory
        set $static_root /...path.../mokmedia/app;

        # 视频存放目录 | Video storage directory
        set $video_path /...path.../video/;

        add_header X-Content-Type-Options   "nosniff";
        add_header X-Frame-Options          "SAMEORIGIN";
        
        location / {
            include uwsgi_params;
            # sock文件路径 | uwsgi sock path
            uwsgi_pass unix:/...path.../mokmedia/mokmedia.sock;
            uwsgi_param X-Real-IP $remote_addr;
            uwsgi_param X-Forwarded-For $proxy_add_x_forwarded_for;
            uwsgi_param X-Forwarded-Proto $scheme;
            uwsgi_param Host $host;
        }
   
        location /static/src/ {
            root $static_root;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /static/media/image/ {
            root $static_root;
            expires 7d;
            add_header Cache-Control "public";
        }

        # 当给视频签名时，删掉或者注释掉这个。
        # if SIGN_FOR_VIDEO=True, comment out or delete this:
        location /static/media/video/ {
            alias $video_path;
            try_files $uri @video_not_found;
            mp4;
            mp4_buffer_size 1m;
            mp4_max_buffer_size 5m;
        }

        location /protected/videos/ {
            internal;
            alias $video_path;
            try_files $uri @video_not_found;
            mp4;
            mp4_buffer_size 1m;
            mp4_max_buffer_size 5m;
            add_header Cache-Control "public, max-age=3600";
            expires 1h;
        }

        location /static/ {
            root $static_root;
        }

        location @video_not_found {
            add_header Content-Type "application/json; charset=utf-8";
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            return 404 '{"msg": "视频文件不存在"}';
        }

        access_log /var/log/nginx/mok_access.log;
        error_log /var/log/nginx/mok_error.log;
      }
    ```

## 配置说明 | Configuration  

  - **基础配置 | Core Config**
  
    - `JWT_RETURN_MODE`: 1 or 2  
    
      JWT token验证方式 (1: cookie, 2: header)，必须和前端(app/static/src/js/base.js)的配置AppConfig.JwtMode保持一致  
      JWT token verification schema (1: cookie, 2: header), Must match the frontend configuration in AppConfig.JwtMode (app/static/src/js/base.js).

    - `SIGN_FOR_VIDEO`: True or False  
  
      为视频的链接签名 | signing for all video URLs  

      - 如果 SIGN_FOR_VIDEO=True，那么 LOCAL_SIGN_KEY 必须设置  
      - If SIGN_FOR_VIDEO=True, then LOCAL_SIGN_KEY must be set  
  
    - `CLOUD_CDN_SIGN`: True or False  
  
      为云视频签名，内置了腾讯和阿里A算法。 | signing for cloud video URLs
      - 如果 CLOUD_CDN_SIGN=True，那么相关的Key必须要设置。  
      - If CLOUD_CDN_SIGN=True, then relevant Keys must be set.  

  - **添加新的视频 | Adding New Content**  

    编辑下方2个文件 | Edit one of these scripts:  

    - 电视剧、短剧 | TV series: `test -> add_drama.py`
    - 电影 | Movies: `test -> add_movie.py`

## 待解决 | TODO

1. 需要一个管理后台  

   Add an admin management backend.

2. 数据库结构需要优化  

   Optimize the database schema.

3. js我不熟，ai教我乱写一气的  

   umm...

4. plyr.js 在 iOS 设备上，当 Safari 接管全屏后字幕不显示  

   On iOS, when Plyr.js enters fullscreen(handed over to Safari’s native player), subtitle don't appear 



