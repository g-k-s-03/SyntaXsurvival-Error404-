(function (global) {
  'use strict';

  var TOKEN_KEY = 'bc_token';
  var ROLE_KEY = 'bc_role';
  var USER_KEY = 'bc_user';
  var API_BASE_KEY = 'bc_api_base';
  var OFFLINE_MODE_KEY = 'bc_offline_mode';
  var OFFLINE_OTP_KEY = 'bc_offline_otp';
  // Production default (Render). Can be overridden via ?api_base=...
  var DEFAULT_API_BASE = 'https://syntaxsurvival-error404.onrender.com/v1';

  function applyApiBaseFromUrl() {
    try {
      var params = new URLSearchParams(window.location.search || '');
      var apiBase = params.get('api_base');
      if (!apiBase) return;
      apiBase = String(apiBase).trim().replace(/\/+$/, '');
      if (!/^https?:\/\//i.test(apiBase)) return;
      localStorage.setItem(API_BASE_KEY, apiBase);
    } catch (_) {}
  }

  applyApiBaseFromUrl();

  function isLocalhostHost(hostname) {
    var h = String(hostname || '').toLowerCase();
    return h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0';
  }

  function isLocalApiBase(apiBase) {
    var s = String(apiBase || '').toLowerCase();
    return s.indexOf('http://localhost') === 0 || s.indexOf('http://127.0.0.1') === 0;
  }

  function getApiBase() {
    var stored = localStorage.getItem(API_BASE_KEY) || '';
    // If we're on a deployed site and a stale localhost api_base is stored,
    // ignore it to avoid browser LAN-access prompts for shared links.
    if (stored && isLocalApiBase(stored) && !isLocalhostHost(window.location.hostname)) {
      stored = '';
    }
    return (stored || DEFAULT_API_BASE).replace(/\/+$/, '');
  }

  function normalizePhone(raw) {
    return String(raw || '').replace(/\D/g, '').slice(-10);
  }

  function normalizeBloodGroup(raw) {
    var v = String(raw || '').toUpperCase().replace(/\s+/g, '').replace('−', '-');
    var allowed = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
    return allowed.indexOf(v) >= 0 ? v : '';
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
  }

  function getRole() {
    return localStorage.getItem(ROLE_KEY) || '';
  }

  function isAuthenticated() {
    return !!getToken();
  }

  function saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token || '');
    if (user && user.role) localStorage.setItem(ROLE_KEY, String(user.role));
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(OFFLINE_MODE_KEY);
  }

  function isOfflineMode() {
    return localStorage.getItem(OFFLINE_MODE_KEY) === '1';
  }

  function roleHome(role) {
    if (role === 'donor') return 'donor-dashboard.html';
    if (role === 'hospital') return 'hospital-dashboard.html';
    if (role === 'admin') return 'admin.html';
    return 'role.html';
  }

  function requireRole(requiredRole) {
    var role = getRole();
    var token = getToken();
    if (!token || role !== requiredRole) {
      window.location.href = token ? roleHome(role) : 'login.html';
      return false;
    }
    return true;
  }

  async function apiFetch(path, options) {
    options = options || {};
    var method = options.method || 'GET';
    var withAuth = options.withAuth !== false;
    var timeoutMs = Number(options.timeoutMs || 12000);
    var headers = { 'Content-Type': 'application/json' };
    if (withAuth && getToken()) headers.Authorization = 'Bearer ' + getToken();
    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, timeoutMs);
    var res;
    try {
      res = await fetch(getApiBase() + path, {
        method: method,
        headers: headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal
      });
    } catch (err) {
      var netErr = new Error('Network unavailable or too slow. Please retry.');
      netErr.code = 'NETWORK';
      netErr.cause = err;
      throw netErr;
    } finally {
      clearTimeout(timeout);
    }
    var data = {};
    try {
      data = await res.json();
    } catch (_) {}
    if (!res.ok) {
      var msg = (data && data.detail) ? data.detail : 'Request failed';
      throw new Error(msg);
    }
    return data;
  }

  async function post(path, payload, withAuth, options) {
    options = options || {};
    return apiFetch(path, { method: 'POST', body: payload || {}, withAuth: withAuth, timeoutMs: options.timeoutMs });
  }

  function createOfflineOtpChallenge(phone) {
    var code = String(Math.floor(Math.random() * 1000000)).padStart(6, '0');
    var expiresAt = Date.now() + (10 * 60 * 1000);
    sessionStorage.setItem(OFFLINE_OTP_KEY, JSON.stringify({
      phone: normalizePhone(phone),
      code: code,
      expiresAt: expiresAt
    }));
    return { code: code, expiresAt: expiresAt };
  }

  function verifyOfflineOtpChallenge(phone, code) {
    var raw = sessionStorage.getItem(OFFLINE_OTP_KEY);
    if (!raw) return false;
    try {
      var row = JSON.parse(raw);
      if (!row || row.phone !== normalizePhone(phone)) return false;
      if (Date.now() > Number(row.expiresAt || 0)) return false;
      if (String(row.code || '') !== String(code || '')) return false;
      sessionStorage.removeItem(OFFLINE_OTP_KEY);
      return true;
    } catch (_) {
      return false;
    }
  }

  function startOfflineSession(phone, role) {
    var normalizedRole = String(role || '').trim();
    var normalizedPhone = normalizePhone(phone);
    var offlineUser = {
      id: 'offline-' + normalizedPhone,
      phone: normalizedPhone,
      role: normalizedRole,
      phone_verified: true,
      offline_mode: true
    };
    saveSession('offline-token-' + Date.now(), offlineUser);
    localStorage.setItem(OFFLINE_MODE_KEY, '1');
    return offlineUser;
  }

  async function fetchMe(options) {
    options = options || {};
    var data = await apiFetch('/me', { method: 'GET', withAuth: true, timeoutMs: options.timeoutMs });
    if (data && data.user && data.user.role) {
      localStorage.setItem(ROLE_KEY, String(data.user.role));
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    }
    return data;
  }

  async function enforceRole(requiredRole) {
    var token = getToken();
    if (!token) {
      window.location.href = 'login.html';
      return false;
    }
    try {
      var me = await fetchMe();
      var role = me && me.user ? me.user.role : '';
      if (role !== requiredRole) {
        window.location.href = roleHome(role);
        return false;
      }
      return true;
    } catch (err) {
      // On slow/unstable networks, don't hard-logout. Fall back to cached role.
      if (err && err.code === 'NETWORK') {
        var cachedRole = getRole();
        if (cachedRole === requiredRole) return true;
        if (cachedRole) window.location.href = roleHome(cachedRole);
        return false;
      }
      clearSession();
      window.location.href = 'login.html';
      return false;
    }
  }

  async function syncPendingProfile() {
    var raw = sessionStorage.getItem('bc_pending_profile');
    if (!raw) return { synced: false };
    var pending;
    try {
      pending = JSON.parse(raw);
    } catch (_) {
      sessionStorage.removeItem('bc_pending_profile');
      return { synced: false };
    }
    if (!pending || !pending.type || !pending.payload) {
      sessionStorage.removeItem('bc_pending_profile');
      return { synced: false };
    }
    var path = pending.type === 'donor' ? '/profiles/donor' : '/profiles/hospital';
    await post(path, pending.payload, true);
    sessionStorage.removeItem('bc_pending_profile');
    return { synced: true };
  }

  global.Auth = {
    getApiBase: getApiBase,
    getToken: getToken,
    getRole: getRole,
    isAuthenticated: isAuthenticated,
    saveSession: saveSession,
    clearSession: clearSession,
    normalizePhone: normalizePhone,
    normalizeBloodGroup: normalizeBloodGroup,
    roleHome: roleHome,
    requireRole: requireRole,
    apiFetch: apiFetch,
    fetchMe: fetchMe,
    enforceRole: enforceRole,
    syncPendingProfile: syncPendingProfile,
    post: post,
    isOfflineMode: isOfflineMode,
    createOfflineOtpChallenge: createOfflineOtpChallenge,
    verifyOfflineOtpChallenge: verifyOfflineOtpChallenge,
    startOfflineSession: startOfflineSession
  };
})(window);
