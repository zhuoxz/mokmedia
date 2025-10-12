//  iconUrl: '/static/src/img/plyr.svg',

const i18n = {
  restart: '重播',
  rewind: '倒退 {seektime} 秒',
  play: '播放',
  pause: '暂停',
  fastForward: '前进 {seektime} 秒',
  seek: 'Seek',
  played: '已播放',
  buffered: '已缓存',
  currentTime: '当前',
  duration: '时长',
  volume: '音量',
  mute: '静音',
  unmute: '取消静音',
  enableCaptions: '开启字幕',
  disableCaptions: '关闭字幕',
  download: '下载',
  enterFullscreen: '进入全屏',
  exitFullscreen: '退出全屏',
  frameTitle: '播放 {title}',
  captions: '字幕',
  settings: '设置',
  pip: '画中画',
  menuBack: '返回',
  speed: '倍速',
  normal: '标准',
  quality: '画质',
  qualityBadge: {
    360: 'LD',
    480: 'SD',
    720: 'HD',
    1080: 'FHD',
    1440: '2k',
    2160: '4k',
    2880: '8k'
  },
  loop: '循环',
  start: '开始',
  end: '结束',
  all: '所有',
  reset: '重置',
  disabled: '关闭',
  enabled: '开启',
  advertisement: 'Ad',
}

const languageLabelMap = {
  cn: "中文",
  zh: "中文",
  zhCN: "简体中文",
  zhTW: "繁體中文",
  en: "English",
  enUS: "English (US)",
  enGB: "English (UK)",
  jp: "日语",
  ja: "日本語",
  ko: "韩语",
  kr: "한국어",
  fr: "Français",
  de: "Deutsch",
  es: "Español",
  ru: "Русский",
  it: "Italiano",
  pt: "Português",
  vi: "Tiếng Việt",
  th: "ภาษาไทย",
  ar: "العربية",
  tr: "Türkçe",
  hi: "हिन्दी",
  id: "Bahasa Indonesia",
  ms: "Bahasa Melayu",
  fa: "فارسی",
  he: "עברית",
  nl: "Nederlands",
  sv: "Svenska",
  pl: "Polski",
  uk: "Українська",
  cs: "Čeština",
  ro: "Română",
  hu: "Magyar",
  el: "Ελληνικά",
  da: "Dansk",
  fi: "Suomi",
  no: "Norsk",
  sk: "Slovenčina",
  bg: "Български",
  hr: "Hrvatski",
  sr: "Српски",
  sl: "Slovenščina",
  et: "Eesti",
  lv: "Latviešu",
  lt: "Lietuvių",
  cnEN: "中英双字",
  enCN: "英中双字",
  cnJP: "中日双字",
  cnKR: "中韩双字",
  cnFR: "中法双字"
};

let tips = null;
let player = null;
let hls = null;
let collapse = null;
let playlist = null;
let hasMultiQuality = false;
let isFirstPlay = true;
let extraParam = {
  mid: '',
  typ: '',
  season: 1
};
window.hlsSupport = {
  nativeHLS: false,
  hlsJS: false,
  canPlay: false
};
const providerLoading = document.getElementById('provider-loading');
const listLoading = document.getElementById('list-loading');
const playLoading = document.getElementById('play-loading');

const isMobile = window.innerWidth <= 768;

(function checkHlsSupport() {
  const hlsJsSupport = window.Hls?.isSupported?.() || false;
  const tempVideo = document.createElement('video');
  const native = Boolean(
    tempVideo.canPlayType('application/vnd.apple.mpegurl') ||
    tempVideo.canPlayType('application/x-mpegURL')
  );
  window.hlsSupport.nativeHLS = native
  window.hlsSupport.hlsJS = hlsJsSupport
  window.hlsSupport.canPlay = native || hlsJsSupport
})();

class PlaylistManager {
  constructor(btnGroupElement, epswiperWrapperElement) {
    this.src = null;
    this.providersBtn = document.getElementById(btnGroupElement);
    this.swiperWrapper = document.getElementById(epswiperWrapperElement);
    this.swiper = null;
    this.signVideo = true;
    this.currentProvider = null;
    this.targetProvider = null;
    this.targetEpisode = null;
    this.isSwitching = false;

    if (!this.providersBtn || !this.swiperWrapper) {
      console.error('PlaylistManager: 没找到元素');
      return;
    }
    this.init();
  }

  init() {
    if (this.src) {
      this.initSwiper();
    }
  }

  createProviderButtons() {
    this.providersBtn.innerHTML = '';
    const providers = Object.keys(this.src);
    if (providers.length === 0) {
      this.providersBtn.innerHTML = '<span class="text-muted">暂无播放源</span>';
      return;
    }

    providers.forEach((provider, index) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'src-btn';
      btn.dataset.source = provider;
      btn.textContent = provider;
      if (index === 0) {
        btn.classList.add('active');
        btn.disabled = true;
      }
      btn.addEventListener('click', () => this.switchProvider(provider));
      this.providersBtn.appendChild(btn);
    });
  }

  switchProvider(provider) {
    if (!this.src[provider]) return;
    if (this.currentProvider === provider) return;
    this.currentProvider = provider;
    this.updateButtonActiveState(provider);
    this.loadEpisodes(provider);
    if (collapse) {
      collapse.show();
    }
  }

  updateButtonActiveState(provider) {
    this.providersBtn.querySelectorAll('.src-btn').forEach(btn => {
      if (btn.dataset.source === provider) {
        btn.classList.add('active');
        btn.disabled = true;
      } else {
        btn.classList.remove('active');
        btn.disabled = false;
      }
    });
  }

  loadEpisodes(provider) {
    const pvdr = this.src[provider];
    this.swiperWrapper.innerHTML = '';
    const sortedEpisodes = Object.keys(pvdr).map(Number).sort((a, b) => a - b);

    const episodesPerPage = isMobile ? 21 : 80;     // 每页显示的剧集数量
    let currentSlide = document.createElement('div');
    currentSlide.className = 'swiper-slide';

    sortedEpisodes.forEach((episode, index) => {

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'src-btn';
      btn.textContent = `第 ${episode} 集`;

      if (this.targetProvider === provider && this.targetEpisode === episode) {
        btn.classList.add('active');
        btn.disabled = true;
      }

      btn.addEventListener('click', async (e) => {
        await this.switchEpisode(e.currentTarget, provider, episode);
      });
      currentSlide.appendChild(btn);
      if ((index + 1) % episodesPerPage === 0) {
        this.swiperWrapper.appendChild(currentSlide);
        currentSlide = document.createElement('div');
        currentSlide.className = 'swiper-slide';
      }
    });

    if (currentSlide.children.length > 0) {
      this.swiperWrapper.appendChild(currentSlide);
    }

    if (this.swiper) {
      this.swiper.update();
    }
  }

  async switchEpisode(btnElement, provider, episode) {
    if (isFirstPlay === true) { isFirstPlay = false; }
    tips.hide();
    if (this.isSwitching) {
      tips.show('正在请求中。。', true, false);
      return;
    }
    this.isSwitching = true;
    try {
      const qualities = this.src[provider][episode];
      if (!qualities || Object.keys(qualities).length === 0) {
        tips.show(`第${episode}集暂时没有播放源`, false, true, 2000);
        return;
      }

      let playData = null;

      if (this.signVideo) {
        playData = cache.getPlayUrl(extraParam.mid, provider, episode);
        if (!playData) {
          const sources = Object.entries(qualities).map(([quality, data]) => ({
            uuid: data.uuid,
            quality: parseInt(quality),
            suffix: data.suffix
          }));
          playData = await getPlayUrl(episode, sources);
          cache.setPlayUrl(extraParam.mid, provider, episode, playData, playData.expires);
        }
      } else {
        playData = handlePlayData(episode, qualities);
      }

      this.playVideo(playData);

      this.updateEpisodeActiveState(btnElement, provider, episode);

    } catch (e) {
      const err = apiClient.handleError(e);
      if (tips) { tips.show(`获取播放链接失败：${err}`, false, false); }
    } finally {
      this.isSwitching = false;
    }
  }

  updateEpisodeActiveState(btn, provider, episode) {
    this.swiperWrapper.querySelectorAll('.src-btn').forEach(b => {
      b.classList.remove('active');
      b.disabled = false;
    });
    btn.classList.add('active');
    btn.disabled = true;
    this.targetEpisode = episode;
    this.targetProvider = provider;
  }

  playVideo(src) {
    const totalLength = src.sources.length
    if (totalLength === 0) {
      tips.show('没有获得播放链接', false, false);
      return;
    }

    if (src.expires && Math.floor(Date.now() / 1000) > src.expires) {
      tips.show('链接过期，请刷新页面', false, false);
      return;
    }

    if (totalLength > 1) {
      hasMultiQuality = true;
    } else { hasMultiQuality = false; }

    playLoading.classList.remove('d-none');

    const hlsSrc = src.sources.filter(s =>
      s.type === 'application/x-mpegURL'
    );
    const totalHlsCount = hlsSrc.length;

    destroyHls();

    if (totalHlsCount > 0) {
      if (window.hlsSupport.nativeHLS) {
        playNormal(src);
      } else if (window.hlsSupport.hlsJS) {
        playHls(hlsSrc, totalHlsCount);
      } else {
        playLoading.classList.add('d-none');
        tips.show('你的浏览器不支持HLS格式', false, false);
      }
    } else {
      playNormal(src);
    }
  }

  initSwiper() {
    if (this.swiper) {
      return;
    }
    this.swiper = new Swiper('.swiper', {
      // cssMode: true,
      loop: false,
      direction: 'horizontal',
      // grabCursor: true, //鼠标手掌
      // autoHeight: true,
      watchOverflow: true, //只有1个的时候不拖动
      runCallbacksOnInit: false,
      // mousewheel: true,
      mousewheel: {
        enabled: true,
        eventsTarget: '.swiper',
        releaseOnEdges: true,
        forceToAxis: true
      },
      freeMode: false,
      longSwipes: false,
      // keyboard: true,
      pagination: {
        el: '.swiper-pagination',
        dynamicBullets: true,
        // clickable: true,
      },
      // slidesPerView: 'auto',
    });
  }

  refresh() {
    this.createProviderButtons();
    const first = Object.keys(this.src)[0];
    if (first) this.switchProvider(first);
  }

  updateSources(newData) {
    if (newData && newData.signVideo !== undefined && newData.playList) {
      this.signVideo = newData.signVideo;
      this.src = newData.playList;
    } else {
      this.providersBtn.innerHTML = '<span class="text-muted">数据格式错误</span>';
      this.swiperWrapper.innerHTML = '';
      return;
    }
    if (!this.src || Object.keys(this.src).length === 0) {
      this.providersBtn.innerHTML = '<span class="text-muted">暂无播放源</span>';
      this.swiperWrapper.innerHTML = '';
    } else {
      this.initSwiper();
      this.refresh();
      // MokMedia.srcData = newData;
    }
  }

  destroy() {
    if (this.swiper) {
      this.swiper.destroy(true, true);
      this.swiper = null;
    }
    if (this.providersBtn) { this.providersBtn.innerHTML = ''; }
    if (this.swiperWrapper) { this.swiperWrapper.innerHTML = ''; }
    this.currentProvider = null;
    this.targetProvider = null;
    this.targetEpisode = null;
    this.isSwitching = null;
    this.src = null;
    this.signVideo = null;
  }
}

async function getPlayUrl(ep, sources) {
  listLoading.classList.remove('d-none');
  try {
    const response = await apiClient.post('/media/api/geturl', sources, {
      params: {
        typ: extraParam.typ,
        // ep: ep,
      },
    });
    return handleSignData(ep, response.data);
  } catch (error) {
    throw error;
  } finally {
    listLoading.classList.add('d-none');
  }
}

function handlePlayData(ep, qualities) {
  const res = {
    type: 'video',
    title: `第 ${ep} 集`,
    sources: [],
    tracks: [],
  };
  Object.entries(qualities).forEach(([quality, data]) => {
    if (data.url) {
      const suffix = data.suffix || 'mp4';
      res.sources.push({
        src: data.url,
        type: suffix === 'm3u8' ? 'application/x-mpegURL' : `video/${suffix}`,
        size: parseInt(quality),
      });

      if (Array.isArray(data.sub) && data.sub.length > 0) {
        data.sub.forEach((item) => {
          if (!res.tracks.some(track => track.src === item.url)) {
            res.tracks.push({
              kind: 'subtitles',
              label: languageLabelMap[item.language] || item.language,
              srclang: item.language,
              src: item.url,
              default: item.is_default || false
            });
          }
        });
      }
    }
  });
  res.sources.sort((a, b) => a.size - b.size); //低->高
  return res;
}

function handleSignData(ep, data) {
  if (!data.sources || !Array.isArray(data.sources) || data.sources.length === 0) {
    throw new Error('没有发回视频源数据');
  }
  const res = {
    type: 'video',
    title: `第 ${ep} 集`,
    sources: [],
    tracks: [],
    expires: data.t,  // 过期时间戳
  };
  data.sources.forEach(source => {
    if (source.sign) {
      const suffix = source.suffix || 'mp4';
      const videoUrl = `${data.pre_url}${extraParam.mid}/${source.uuid}?typ=${extraParam.typ}&t=${data.t.toString(16)}&sign=${source.sign}`;
      res.sources.push({
        src: videoUrl,
        type: suffix === 'm3u8' ? 'application/x-mpegURL' : `video/${suffix}`,
        size: source.quality,
      });
    }
  });

  if (Array.isArray(data.sub) && data.sub.length > 0) {
    data.sub.forEach((item) => {
      res.tracks.push({
        kind: 'subtitles',    // 'captions'
        label: languageLabelMap[item.language] || item.language,
        srclang: item.language,
        src: item.url,
        default: item.is_default || false
      });
    });
  } else {
    // 没有字幕
  }
  res.sources.sort((a, b) => a.size - b.size);  //低->高
  return res
}

function playNormal(src) {
  try {
    player.source = src;
    player.play();
  } catch (error) {
    playLoading.classList.add('d-none');
    tips.show('数据异常，无法播放', false, false);
  }
}

function playHls(hlsSources, hlsCount) {
  hls = new window.Hls({
    debug: false,
    enableWorker: true,
    lowLatencyMode: false,
    backBufferLength: 15,
    capLevelToPlayerSize: true,
    maxBufferLength: 30
  });

  hls.on(window.Hls.Events.ERROR, (event, data) => {
    const { type, details, fatal, error } = data;
    if (fatal) {
      switch (type) {
        case 'networkError':
          if (details === 'manifestLoadError') {
            tips.show('无法播放，可能服务器不允许跨域', false, false);
            break;
          }
          tips.show('网络错误，重试', false, false);
          // hls.startLoad();
          break;
        case 'mediaError':
          tips.show('无法播放，HLS媒体错误', false, false);
          // hls.recoverMediaError();
          break;
        default:
          tips.show('流媒体播放失败', false, false);
          break;
      }
      playLoading.classList.add('d-none');
    }
  });

  hls.on(window.Hls.Events.MEDIA_ATTACHED, () => {
    hls.loadSource(hlsSources[hlsCount - 1].src);

  });

  hls.on(window.Hls.Events.MANIFEST_PARSED, function () {
    player.play().catch(error => {
      tips.show(`有可能自动播放被浏览器阻止，${error}`, false, true, 2000);
    });
  });

  hls.attachMedia(player.media);

}

function getExtraParam(elementID) {
  let mid = document.getElementById(elementID)?.getAttribute('data-mid');
  if (!mid) {
    try {
      const path = window.location.pathname;
      const regex = /^\/media\/([^\/]+)\/play$/;
      const match = path.match(regex);
      mid = match ? match[1].trim() : '';
    } catch {
      mid = '';
    }
  }
  let typ = document.getElementById(elementID)?.getAttribute('data-typ');
  if (!typ) {
    try {
      const typParam = new URLSearchParams(window.location.search).get('typ');
      typ = typParam ? typParam.trim() : '';
    } catch {
      typ = '';
    }
  }
  const season = document.getElementById(elementID)?.getAttribute('data-season');
  extraParam.mid = mid;
  extraParam.typ = typ;
  extraParam.season = season ? parseInt(season) : 1;
}

async function getPlayList() {
  const mid = extraParam.mid;
  const typ = extraParam.typ;
  if (!mid || mid === '' || !typ || typ === '') {
    if (tips) { tips.show('页面有错误，请刷新页面。', false, false); }
    return;
  }
  if (providerLoading) { providerLoading.classList.remove('d-none'); }
  try {
    const res = await apiClient.get(`/media/api/playlist/${mid}`, {
      params: {
        typ: typ
      },
      timeout: 13000
    });
    playlist.updateSources(res.data);
  } catch (e) {
    const err = apiClient.handleError(e);
    if (tips) { tips.show(`播放列表： ${err}`, false, false); }
  } finally {
    if (providerLoading) { providerLoading.classList.add('d-none'); }
    if (tips) { tips.hideLoading(); }
  }
}

function createLoginBtn() {
  playlist.providersBtn.innerHTML = '';
  playlist.swiperWrapper.innerHTML = '';
  const loginBtn = document.createElement('button');
  loginBtn.type = 'button';
  loginBtn.className = 'src-btn';
  loginBtn.textContent = '登录';
  loginBtn.onclick = () => login.show();
  playlist.providersBtn.appendChild(loginBtn);
}

function initPlayer(videoElement) {
  player = new window.Plyr(videoElement, {
    // debug: true, // ........debug 调试
    controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings', 'pip', 'fullscreen'],
    settings: ['captions', 'quality', 'speed'],
    seekTime: 5,
    volume: 0.3,
    speed: { selected: 1, options: [0.5, 1, 1.5, 2, 4] },
    quality: { default: 720, options: [4320, 2880, 2160, 1440, 1080, 720, 480] },
    tooltips: { controls: true, seek: true },
    keyboard: { focused: true, global: true },
    i18n,
    loadSprite: true,
    iconUrl: '/static/src/img/plyr.svg',
    iconPrefix: 'plyr',
    blankVideo: '',
    clickToPlay: true,
    autoplay: false,
    ratio: '16:9',
    fullscreen: { enabled: true, fallback: true, iosNative: true, container: null },
  });

  if (extraParam.mid !== '') {
    player.poster = `/static/media/image/poster/${extraParam.mid}.jpg`;
  }

  player.on('click', (event) => {  // touchstart
    if (player.touch && event.target.tagName === 'DIV') {
      player.togglePlay();
    }
  });

  player.on('canplay', () => {
    if (playLoading) { playLoading.classList.add('d-none'); }
    // if (tips) { tips.show('已就绪', false, true, 1800); }
  });

  player.on('qualitychange', () => {
    if (tips) { tips.hide(); }
  });

  player.on('error', () => {
    const error = player.media.error;
    if (error) {
      let msg = '';
      switch (error.code) {
        case 1:
          msg = '视频加载被中止';
          break;
        case 2:
          msg = '网络错误';
          break;
        case 3:
          msg = '视频解码错误';
          break;
        case 4:
           msg = '链接无效或者视频格式不支持';
          break;
        default:
          msg = error.message;
      }
      if (playLoading) { playLoading.classList.add('d-none'); }
      if (tips) {
        if (hasMultiQuality !== null && hasMultiQuality) {
          tips.show(`无法播放: ${msg}。本集可切换画质。`)
        } else {
          tips.show(`播放出错: ${msg}`, false, true, 3000);
        }
      }
    }
  });

  player.on('play', () => {
    if (AppConfig.isLogin === false) {
      if (tips) { tips.show('还没登录。', false, true, 2000); }
      if (collapse) { collapse.show(); }
      player.pause();
      return;
    }
    if (isFirstPlay) {
      player.pause();
      if (tips) { tips.show('还没有选择播放的剧集', false, true, 2000); }
      if (collapse) { collapse.show(); }
      return;
    }
    // todo 播放器内部调用时，也要处理链接过期的情况
  });
}

function destroyHls() {
  if (hls) {
    hls.stopLoad();
    hls.destroy();
    hls = null;
  }
}

function initCollapseEpisode() {
  const collapseEpisode = document.getElementById('collapseEpisode');
  collapse = bootstrap.Collapse.getOrCreateInstance(collapseEpisode);
  const detialArea = document.getElementById('detail-area');
  document.addEventListener('click', function (event) {
    const detialAreaClick = detialArea.contains(event.target);
    if (detialAreaClick && collapseEpisode.classList.contains('show')) { collapse.hide(); }
  });
}

class CacheManager {
  constructor(storageKey, storage = sessionStorage, maxSize = 60) {
    this.maxSize = maxSize;
    this.storageKey = storageKey;
    this.storage = storage;
    this.init();
  }

  init() {
    if (!this.storageKey) { throw new Error('key必须设置'); }
  }

  getPlayUrl(mid, provider, episode) {
    return this.get(`${mid}_${provider}_${episode}`);
  }

  setPlayUrl(mid, provider, episode, data, expires) {
    this.set(`${mid}_${provider}_${episode}`, data, expires);
  }

  get(key) {
    try {
      const cache = this.getCache();
      const item = cache.res.find(item => item.key === key);
      if (!item || !item.data) { return null; }
      if (this.isExpired(item.expires)) { return null; }
      return item.data;
    } catch (error) {
      return null;
    }
  }

  set(key, data, expires = null) {
    try {
      const cache = this.getCache();
      if (!data || !key) {
        return;
      }
      const existingIndex = cache.res.findIndex(item => item.key === key);
      const item = {
        key: key,
        data: data,
        expires: expires,
        timestamp: Date.now(),
      };
      if (existingIndex >= 0) {
        cache.res[existingIndex] = item;
      } else {
        cache.res.push(item);
      }
      this.saveCache(cache);
    } catch (error) {
      this.clear();
    }
  }

  getCache() {
    try {
      const cached = this.storage.getItem(this.storageKey);
      if (!cached) return { res: [] };
      const data = JSON.parse(cached);
      if (!Array.isArray(data.res)) {
        return { res: [] };
      }
      return data;
    } catch (e) {
      return { res: [] };
    }
  }

  saveCache(cache) {
    try {
      cache.res = cache.res.filter(item => !this.isExpired(item.expires));
      cache.res.sort((a, b) => b.timestamp - a.timestamp);
      if (cache.res.length > this.maxSize) {
        cache.res = cache.res.slice(0, this.maxSize);
      }
      this.storage.setItem(this.storageKey, JSON.stringify(cache));
    } catch (e) {
      this.clear();
    }
  }

  remove(key) {
    const cache = this.getCache();
    cache.res = cache.res.filter(item => item.key !== key);
  }

  clear() {
    this.storage.removeItem(this.storageKey);
  }

  isExpired(expires) {
    if (!expires) return false;
    return Math.floor(Date.now() / 1000) > expires;
  }

  keys() {
    const cache = this.getCache();
    return cache.res.map(item => item.key);
  }

  find(predicate) {
    const cache = this.getCache();
    return cache.res.filter(predicate);
  }
}


const cache = new CacheManager('playUrlCache');

document.addEventListener('DOMContentLoaded', async function () {

  getExtraParam('extra_para');

  initCollapseEpisode();

  tips = new ToastManager('tip-toast', 'tip-loading', 'tip-content');

  login = new LoginManager();

  const videoElement = document.getElementById('player');
  initPlayer(videoElement);

  playlist = new PlaylistManager('srcBtnGroup', 'epSwiperWrapper');

  apiClient.setOnAuthFailure(() => {
    createLoginBtn();
  });

  login.setOnSuccessCallback(async () => {
    playlist.providersBtn.innerHTML = '';
    tips.hide()
    await getPlayList();
  });

  if (AppConfig.isLogin) {
    await getPlayList();
  } else {
    createLoginBtn();
  }

});


window.addEventListener('beforeunload', () => {
  destroyHls();
});
