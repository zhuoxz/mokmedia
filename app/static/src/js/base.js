window.MokMedia = window.MokMedia || {};
// window.MokMusic = window.MokMusic || {};

window.AppConfig = {
  // Type: int  1 -> Set-Cookie,  2 -> Authorization header 
  // *** 注意 | Note: *** 这个设置必须和后端验证模式保持一致，this item must be same value as backend setting
  // 位置 | location :  MonkMedia  app - config.py - class Config: JWT_RETURN_MODE = ?
  jwtMode: 2,

  isLogin: localStorage.getItem('login') === 'true' || false,

  persistent: localStorage.getItem('persist') === 'true' || false
};

let backToTop = null;

function initBackToTop() {
  backToTop = document.getElementById('back-to-top');
  const top = document.getElementById('top');
  if (!backToTop || !top) {
    console.warn('back-to-top button not initialized');
    return;
  }
  const observer = new IntersectionObserver(
    ([entry]) => {
      backToTop.classList.toggle('d-none', entry.isIntersecting);
    },
    { threshold: 0, rootMargin: '240px 0px 0px 0px' }
  );
  observer.observe(top);
  backToTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
}

function hideNavbar() {
  const collapseElement = document.getElementById('navbarCollapse');
  const navCollapse = bootstrap.Collapse.getInstance(collapseElement);
  if (navCollapse) {
    navCollapse.hide();
  }
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function setLoginStatus(login) {
  if (login) {
    AppConfig.isLogin = true;
    localStorage.setItem('login', 'true');
  } else {
    AppConfig.isLogin = false;
    localStorage.setItem('login', 'false');
  }
}

class LoginManager {
  constructor() {
    this.modal = null;
    this.isInitialized = false;
    this.onHideCallback = null;
    this.onSuccessCallback = null;
    this.captchaTimestamp = null;
    this._loginPromise = null;
    this._loginResolve = null;

    this.init();
  }
  init() {
    this.modalElement = document.getElementById('validateModal');
    if (!this.modalElement) {
      throw new Error('LoginManager: no modalElement');
      // return;
    }

    this.modal = new bootstrap.Modal(this.modalElement, {
      backdrop: 'static',
      focus: true,
      keyboard: true
    });

    this.passwdInput = document.getElementById('passwdInput');
    this.passwdTip = document.getElementById('passwdTip');
    this.captchaBox = document.getElementById('captchaBox');
    this.captchaInput = document.getElementById('captchaInput');
    this.captchaBtn = document.getElementById('captchaBtn');
    this.captchaImage = document.getElementById('captchaImage');
    this.captchaTip = document.getElementById('captchaTip');
    this.rmSwitch = document.getElementById('rmSwitch');
    this.loginBtn = document.getElementById('loginBtn');
    this.validateSpinner = document.getElementById('validateSpinner');

    if (!this.passwdInput || !this.passwdTip || !this.captchaBox || !this.captchaInput || !this.captchaBtn || !this.captchaImage || !this.captchaTip || !this.rmSwitch || !this.loginBtn || !this.validateSpinner) {
      throw new Error('LoginManager: 缺少html标签元素或元素id');
      // return;
    }

    // if (AppConfig.persistent) {
    //   this.rmSwitch.checked = true;
    // } else {
    //   this.rmSwitch.checked = false
    // }

    this.bindEvents();
    this.isInitialized = true;
  }

  bindEvents() {

    this.debouncedLogin = debounce(() => this.login(), 200);
    this.debouncedSetCaptcha = debounce(() => this.setCaptchaImage(), 200);

    this.captchaBtn.addEventListener('click', this.debouncedSetCaptcha);
    this.loginBtn.addEventListener('click', this.debouncedLogin);

    this.modalElement.addEventListener('shown.bs.modal', () => {
      this.modalElement.removeAttribute('inert');
      this.passwdInput.focus();
    });

    this.modalElement.addEventListener('hide.bs.modal', () => {
      this.passwdInput.blur();
      this.captchaInput.blur();
      this.modalElement.setAttribute('inert', '');

      this.onHideCallback?.();

      if (this._loginPromise && !AppConfig.isLogin) {
        this._loginResolve(false);
        this._loginResolve = null;
        this._loginPromise = null;
      }
    });

    // this.rmSwitch.addEventListener('change', function (e) {
    // });

    window.addEventListener('storage', (e) => {
      if (e.key === 'persist') {
        if (e.newValue !== null) {
          const value = e.newValue === 'true';
          if (AppConfig.persistent !== value) {
            AppConfig.persistent = value;
            if (this.rmSwitch) { this.rmSwitch.checked = value; }
          }
        }
      }
      if (e.key === 'login') {
        if (e.newValue !== null) {
          const value = e.newValue === 'true';
          if (AppConfig.isLogin !== value) {
            AppConfig.isLogin = value;
          }
          if (!value) { logout(); }
        } else {
          // sessionStorage.setItem('login', 'false');
          // AppConfig.isLogin = false;
        }
      }
    });

    document.addEventListener('keydown', (e) => {  // 'keypress' keydown
      if (e.key === 'Enter') {
        e.preventDefault();
        if (this.modalElement.classList.contains('show') === true) {
          this.passwdInput.blur();
          this.loginBtn.focus();
          this.debouncedLogin();
        }
      }
    });
  }

  waitForLogin() {
    if (AppConfig.isLogin) {
      return Promise.resolve(true);
    }

    if (this._loginPromise) {
      return this._loginPromise;
    }
    this._loginPromise = new Promise((resolve) => {
      this._loginResolve = resolve;
    });

    this.show();
    return this._loginPromise;
  }

  _onLoginSuccess() {
    if (this.onSuccessCallback) {
      this.onSuccessCallback();
    }

    if (this._loginResolve) {
      this._loginResolve(true);
      this._loginResolve = null;
      this._loginPromise = null;
    }
  }

  setOnHideCallback(callback) { this.onHideCallback = callback; }
  setOnSuccessCallback(callback) { this.onSuccessCallback = callback; }

  show() {
    if (!this.isInitialized) {
      try {
        this.init();
      } catch (err) {
        if (tips) { tips.show('登录模块加载出错', false, false); } else { console.error(err.message); }
      }
    }
    this.modal.show();
  }

  hide() {
    this.modal.hide();
  }

  _passwdCheck() {
    const pd = this.passwdInput.value
    return pd.length > 0 && pd.length < 6 && /^[a-zA-Z0-9]*$/.test(pd)
  }

  _captchaCheck() {
    const cc = this.captchaInput.value.replace(/\s+/g, '');
    return cc.length > 0 && cc.length < 7 && /^[a-zA-Z0-9]*$/.test(cc)
  }

  _isCaptchaExpired() {
    if (!this.captchaTimestamp) {
      return true;
    }
    const elapsed = Math.floor(Date.now() / 1000) - this.captchaTimestamp;
    return elapsed > 200; // 验证码过期时间 | captcha expiry date
  }

  _setNormalTips(msg) {
    this.captchaInput.classList.remove('is-invalid');
    // this.captchaTip.textContent = '';
    this.passwdInput.classList.add('is-invalid');
    this.passwdTip.textContent = msg;
    this.passwdInput.focus();
  }

  async setCaptchaImage() {

    this.captchaBtn.disabled = true;
    this.validateSpinner.classList.remove('d-none');
    this.captchaInput.value = '';
    this.captchaInput.classList.remove('is-invalid');
    this.captchaTip.textContent = '';

    try {
      const res = await axios.get('/api/captcha', {
        responseType: 'blob',
        timeout: 11000
      });
      this.captchaImage.src = URL.createObjectURL(res.data);
      this.captchaTimestamp = Math.floor(Date.now() / 1000);
    } catch (error) {
      this.handleCaptchaError(error);
      this.captchaImage.src = 'data:image/gif;base64,R0lGODlhgAAgAIAAAP///wAAACH5BAEAAAAALAAAAACAAAAAAQAOhAAAOw==';
      this.captchaTimestamp = null;
    } finally {
      this.validateSpinner.classList.add('d-none');
      this.captchaBtn.disabled = false;
    }
  }

  resetModalState() {
    this.passwdInput.value = '';
    this.passwdInput.classList.remove('is-invalid');
    this.captchaInput.value = '';
    this.captchaInput.classList.remove('is-invalid');
    this.passwdTip.textContent = '';
    this.captchaTip.textContent = '';
    this.captchaImage.src = 'data:image/gif;base64,R0lGODlhgAAgAIAAAP///wAAACH5BAEAAAAALAAAAACAAAAAAQAOhAAAOw==';
    this.captchaBox.classList.add('d-none');
    this.validateSpinner.classList.add('d-none');
  }

  async login() {

    this.passwdInput.classList.remove('is-invalid');
    this.captchaInput.classList.remove('is-invalid');
    this.validateSpinner.classList.remove('d-none');

    if (this.captchaBox.classList.contains('d-none') === false) {
      if (this._isCaptchaExpired()) {
        this.captchaInput.classList.add('is-invalid');
        this.captchaTip.textContent = '验证码过期或失效，请刷新';
        this.captchaInput.focus();
        this.validateSpinner.classList.add('d-none');
        this.captchaTimestamp = null;
        return false;
      }
      if (!this._captchaCheck()) {
        this.captchaInput.classList.add('is-invalid');
        this.captchaTip.textContent = '验证码不合规';
        this.captchaInput.focus();
        this.validateSpinner.classList.add('d-none');
        return false;
      }
    }
    this.captchaTip.textContent = '';
    if (!this._passwdCheck()) {
      this.passwdInput.classList.add('is-invalid');
      this.passwdTip.textContent = '口令不合规';
      this.validateSpinner.classList.add('d-none');

      this.passwdInput.focus();
      return false;
    }
    // this.passwdTip.textContent = '';
    this.loginBtn.disabled = true;
    this.rmSwitch.disabled = true;

    const remember = this.rmSwitch.checked;
    try {
      const res = await axios.post('/api/login', {
        pd: md5(this.passwdInput.value),
        captcha: this.captchaInput.value || '',
        rm: remember
      }, {
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
        },
        timeout: 15000
      });

      const { token, re_token, jwt_mode } = res.data;

      if (jwt_mode && jwt_mode != AppConfig.jwtMode) {
        throw new Error('验证模式不匹配！');
      }

      if (AppConfig.jwtMode == 2) {
        if (!token || !re_token) {
          throw new Error('未获得token');
        }
        try {
          setToken('l_tk', token, remember);
          setToken('re_tk', re_token, remember);
        } catch (e) {
          throw new Error('已登录但无法使用存储，请检查浏览器设置');
        }
      }

      AppConfig.persistent = remember;
      localStorage.setItem('persist', remember);
      setLoginStatus(true);
      this._onLoginSuccess();
      this.hide();
      this.resetModalState();

    } catch (error) {
      this.handleLoginError(error);
    } finally {
      this.validateSpinner.classList.add('d-none');
      this.loginBtn.disabled = false;
      this.rmSwitch.disabled = false;
    }
  }

  handleLoginError(error) {
    if (error.response) {
      const { status, data } = error.response;

      if (data && typeof data === 'object') {
        switch (status) {
          case 401:
            if (data.code === 1) {
              this.captchaInput.classList.add('is-invalid');
              this.captchaInput.value = '';
              this.captchaTip.textContent = data.msg || '无法加载验证码';
              this.captchaInput.focus();
            }
            // else if (data.code === 2) {
            else {
              this.passwdInput.classList.add('is-invalid');
              this.passwdTip.textContent = data.msg || '登录失败';
              this.passwdInput.focus();
            }
            if (data.will_show) {
              this.setCaptchaImage();
              this.captchaBox.classList.remove('d-none');
              this.captchaInput.focus();
            }
            if (data.show_captcha) {
              this.captchaBox.classList.remove('d-none');
            }
            return;
          case 429:
            this._setNormalTips('尝试次数过多，请6小时后重试');
            return;
          default:
            this._setNormalTips(data.msg || '服务器出错');
            return;
        }
      } else {
        this._setNormalTips('接口错误');
        return;
      }

    } else if (error.request) {
      if (error.code === 'ECONNABORTED') {
        this._setNormalTips('请求超时，请稍后重试');
      } else if (navigator.onLine === false) {
        this._setNormalTips('网络连接已断开');
      } else {
        this._setNormalTips('网络错误或无响应');
      }
      return;
    } else if (error instanceof Error && error.message) {
      this._setNormalTips(error.message || '意外错误');
      return;
    }
    else {
      this._setNormalTips('发生未知错误');
      return;
    }
  }

  handleCaptchaError(error) {
    this.captchaInput.classList.add('is-invalid');
    this.captchaInput.value = '';
    this.captchaInput.focus();
    if (error.response) {
      const { status, data } = error.response;
      if (data && typeof data === 'object') {
        switch (status) {
          case 429:
            this.captchaTip.textContent = '请求频繁，请稍后再试';
            return;
          default:
            this.captchaTip.textContent = data.msg || '获取验证码失败';
            return;
        }
      } else {
        this.captchaTip.textContent = '接口错误';
        return;
      }
    } else if (error.request) {
      if (error.code === 'ECONNABORTED') {
        this.captchaTip.textContent = '请求超时，请稍后重试';
      } else if (navigator.onLine === false) {
        this.captchaTip.textContent = '网络连接已断开';
      } else {
        this.captchaTip.textContent = '网络错误或无响应';
      }
      return;
    } else {
      this.captchaTip.textContent = '发生未知错误';
      return;
    }
  }
}

async function logout() {
  if (tips) { tips.show('退出中，正在清理。', true, false); }
  if (AppConfig.jwtMode === 1) {
    try {
      await axios.post('/api/logout');
      if (tips) { tips.show('已退出', true, 2000); }
    } catch (err) {
      if (tips) { tips.show(`退出异常: ${err}`, true, 2000); }
    }
  } else if (AppConfig.jwtMode === 2) {
    clearAllToken();
    if (tips) { tips.show('已退出', true, 2000); }
  }
  localStorage.removeItem('persist');
  localStorage.removeItem('login');
  localStorage.removeItem('plyr');
  sessionStorage.removeItem('playUrlCache');
  window.location.reload();
}

function getToken(name, defaultValue = '') {
  let value = localStorage.getItem(name);
  if (value !== null) {
    return value;
  }
  value = sessionStorage.getItem(name);
  if (value !== null) {
    return value;
  }
  value = defaultValue;
  return value;
}

function setToken(name, value, persist = AppConfig.persistent) {
  if (persist) {
    localStorage.setItem(name, value);
  } else {
    sessionStorage.setItem(name, value);
  }
}

function getCSRFToken(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function clearToken(persist = AppConfig.persistent) {
  if (persist) {
    localStorage.removeItem('l_tk');
    localStorage.removeItem('re_tk');
  } else {
    sessionStorage.removeItem('l_tk');
    sessionStorage.removeItem('re_tk');
  }
}

function clearAllToken() {
  localStorage.removeItem('l_tk');
  sessionStorage.removeItem('l_tk');
  localStorage.removeItem('re_tk');
  sessionStorage.removeItem('re_tk');
}


class ToastManager {
  constructor(toastId, loadingId, contentId) {
    this.toastId = toastId;
    this.loadingId = loadingId;
    this.contentId = contentId;
    this.toastEl = null;
    this.loadingEl = null;
    this.contentEl = null;
    this.toast = null;
    this.timer = null;
    this.isInitialized = false;
    this.init();
  }

  init() {
    if (this.isInitialized) return;
    this.toastEl = document.getElementById(this.toastId);
    if (!this.toastEl) {
      console.warn(`提示未加载，Toast元素ID "${this.toastId}" 未找到。`);
      return;
    }
    this.loadingEl = this.toastEl.querySelector(`#${this.loadingId}`);
    this.contentEl = this.toastEl.querySelector(`#${this.contentId}`);

    if (!this.loadingEl || !this.contentEl) {
      console.warn(`提示未加载，Id${this.loadingId}或${this.contentId}未找到。`);
      return;
    }
    this.toast = bootstrap.Toast.getOrCreateInstance(this.toastEl, {
      animation: true,
      autohide: false
    });
    this.toastEl.addEventListener('hidden.bs.toast', () => {
      // if (this.loadingEl) this.loadingEl.classList.add('d-none');
      this.contentEl.textContent = '';
      this.clearTimers();
    });
    this.isInitialized = true;
  }

  show(msg, showLoading = false, autoHide = false, duration = 6000) {
    if (!this.isInitialized) return;
    this.clearTimers();
    if (showLoading) { this.showLoading(); } else { this.hideLoading(); }
    this.contentEl.textContent = msg;
    if (autoHide) {
      this.timer = setTimeout(() => {
        this.hide();
      }, duration);
    }
    if (!this.toast.isShown()) this.toast.show();
  }

  hide() {
    this.toast.hide();
  }

  showLoading() {
    if (this.loadingEl) {
      this.loadingEl.classList.remove('d-none');
      // this.loadingEl.classList.remove('invisible');
    }
  }

  hideLoading() {
    if (this.loadingEl) {
      this.loadingEl.classList.add('d-none');
    }
  }

  clearTimers() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}

window.AuthCookie = (function () {

  let refreshPromise = null;
  let onAuthFailure = null;
  const MAX_RETRY = 2;

  async function refreshToken() {
    await axios.post('/api/refresh-token', {
      rm: AppConfig.persistent ?? false
    }, {
      withCredentials: true,
      headers: {
        'X-CSRF-Token': getCSRFToken('csrf_refresh_token')
      }
    });
    return true;
  }

  async function request(config) {
    if (typeof config._retry === 'undefined') {
      config._retry = 0;
    }

    if (typeof config.timeout === 'undefined') {
      config.timeout = 15000;
    }

    config.withCredentials = true;

    config.headers = {
      'Content-Type': 'application/json; charset=utf-8',
      ...config.headers,
      'X-CSRF-Token': getCSRFToken('csrf_access_token')
    };

    try {
      return await axios(config);
    } catch (error) {
      const status = error.response?.status;
      const code = error.response?.data?.code;

      if (status === 401 && [3302, 3304, 3306].includes(code)) {
        if (config._retry >= MAX_RETRY) {
          // if (config._retry) {
          throw error;
        }

        if (!refreshPromise) {
          refreshPromise = (async () => {
            try {
              await refreshToken();
              return true;
            } catch (err) {
              throw err;
            } finally {
              refreshPromise = null;
            }
          })();
        }

        try {
          await refreshPromise;
          const retryConfig = { ...config };
          retryConfig._retry += 1;
          // retryConfig._retry = true;
          retryConfig.headers['X-CSRF-Token'] = getCSRFToken('csrf_access_token');
          return await request(retryConfig);
        } catch (err) {
          throw err;
        }
      }
      throw error;
    }
  }

  function handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      const msg = data && typeof data === 'object' ? data.msg : null;
      switch (status) {
        case 400:
          return msg || '请求参数错误';
        case 429:
          return msg || '请求太频繁，请稍后再试';
        case 401:
          setLoginStatus(false);
          if (onAuthFailure) {
            onAuthFailure();
          }
          return msg || '认证失败，请重新登录';
        case 403:
          return '权限不足，访问被拒绝';
        case 404:
          return msg || '请求的资源不存在';
        case 500:
          return '服务器内部错误';
        default:
          return msg || '操作失败，请稍后重试';
      }
    } else if (error.request) {
      if (error.code === 'ECONNABORTED') {
        return '请求超时，请检查网络或重试';
      } else if (error.message && error.message.includes('timeout')) {
        return '请求超时';
      } else if (navigator.onLine === false) {
        return '网络连接已断开';
      } else {
        return '网络错误或无响应';
      }
    } else if (error instanceof Error && error.message) {
      return error.message || '未知错误';
    }
    else {
      return '未知错误';
    }
  }

  return {
    get(url, config = {}) {
      return request({ method: 'get', url, ...config });
    },
    post(url, data, config = {}) {
      return request({ method: 'post', url, data, ...config });
    },
    put(url, data, config = {}) {
      return request({ method: 'put', url, data, ...config });
    },
    delete(url, config = {}) {
      return request({ method: 'delete', url, ...config });
    },
    setOnAuthFailure(callback) {
      if (typeof callback === 'function' || callback === null) {
        onAuthFailure = callback;
      }
    },
    handleError,
  };
})();

window.AuthHeader = (function () {

  let refreshPromise = null;
  let onAuthFailure = null;
  const MAX_RETRY = 1;

  async function refreshToken() {
    const response = await axios.post('/api/refresh-token', {}, {
      headers: {
        'Authorization': `Bearer ${getToken('re_tk')}`,
      }
    });
    const newToken = response.data.token;
    if (!newToken) throw new Error('刷新接口异常');
    setToken('l_tk', newToken);
    return newToken;
  }

  async function request(config) {
    if (typeof config._retry === 'undefined') {
      config._retry = 0;
    }

    if (typeof config.timeout === 'undefined') {
      config.timeout = 15000;
    }

    config.headers = {
      'Content-Type': 'application/json; charset=utf-8',
      ...config.headers,
      'Authorization': `Bearer ${getToken('l_tk')}`,
    };

    try {
      return await axios(config);
    } catch (error) {
      const status = error.response?.status;
      const code = error.response?.data?.code;

      if (status === 401 && [3304, 3306].includes(code)) {
        if (config._retry >= MAX_RETRY) {
          // if (config._retry) {
          throw error;
        }

        if (!refreshPromise) {
          refreshPromise = (async () => {
            try {
              const newToken = await refreshToken();
              return newToken;
            } catch (err) {
              throw err;
            } finally {
              refreshPromise = null;
            }
          })();
        }

        try {
          const newToken = await refreshPromise;
          const retryConfig = { ...config };
          retryConfig._retry += 1;
          // retryConfig._retry = true;
          retryConfig.headers['Authorization'] = `Bearer ${newToken}`;
          return await request(retryConfig);
        } catch (err) {
          throw err;
        }
      }
      throw error;
    }
  }

  function handleError(error) {
    if (error.response) {
      const { status, data } = error.response;
      const msg = data && typeof data === 'object' ? data.msg : null;
      switch (status) {
        case 400:
          return msg || '请求参数错误';
        case 429:
          return msg || '请求太频繁，请稍后再试';
        case 401:
          setLoginStatus(false);
          clearAllToken();
          if (onAuthFailure) {
            onAuthFailure();
          }
          return msg || '认证失败，请重新登录';
        case 403:
          return '权限不足，访问被拒绝';
        case 404:
          return msg || '请求的资源不存在';
        case 500:
          return '服务器内部错误';
        default:
          return msg || '操作失败，请稍后重试';
      }
    } else if (error.request) {
      if (error.code === 'ECONNABORTED') {
        return '请求超时，请检查网络或重试';
      } else if (error.message && error.message.includes('timeout')) {
        return '请求超时';
      } else if (navigator.onLine === false) {
        return '网络连接已断开';
      } else {
        return '网络错误或无响应';
      }
    } else if (error instanceof Error && error.message) {
      return error.message || '未知错误';
    }
    else {
      return '未知错误';
    }
  }

  return {
    get(url, config = {}) {
      return request({ method: 'get', url, ...config });
    },
    post(url, data, config = {}) {
      return request({ method: 'post', url, data, ...config });
    },
    put(url, data, config = {}) {
      return request({ method: 'put', url, data, ...config });
    },
    delete(url, config = {}) {
      return request({ method: 'delete', url, ...config });
    },
    setOnAuthFailure(callback) {
      if (typeof callback === 'function' || callback === null) {
        onAuthFailure = callback;
      }
    },
    handleError,
  };
})();

const apiClient = AppConfig.jwtMode === 1 ? window.AuthCookie : window.AuthHeader

document.addEventListener('DOMContentLoaded', function () {

  initBackToTop();

  document.querySelector('.logout-item').addEventListener('click', function (e) {
    e.preventDefault();
    logout();
  });

})