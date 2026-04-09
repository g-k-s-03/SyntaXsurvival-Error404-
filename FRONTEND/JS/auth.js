(function (global) {
  'use strict';

  var TOKEN_KEY = 'bc_token';
  var ROLE_KEY = 'bc_role';
  var USER_KEY = 'bc_user';
  var API_BASE_KEY = 'bc_api_base';
  var DEFAULT_API_BASE = 'http://localhost:8000/v1';

  function getApiBase() {
    return (localStorage.getItem(API_BASE_KEY) || DEFAULT_API_BASE).replace(/\/+$/, '');
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
  }

  function roleHome(role) {
    if (role === 'donor') return 'donor-dashboard.html';
    if (role === 'hospital') return 'hospital-dashboard.html';
    if (role === 'admin') return 'admin.html';
    return 'role.html';
  }

  function requireRole(requiredRole) {
    var token = getToken();
    var role = getRole();
    if (!token || !role) {
      window.location.href = 'login.html';
      return false;
    }
    if (role !== requiredRole) {
      window.location.href = roleHome(role);
      return false;
    }
    return true;
  }

  async function post(path, payload) {
    var res = await fetch(getApiBase() + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    });
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

  global.Auth = {
    getApiBase: getApiBase,
    getToken: getToken,
    getRole: getRole,
    isAuthenticated: isAuthenticated,
    saveSession: saveSession,
    clearSession: clearSession,
    roleHome: roleHome,
    requireRole: requireRole,
    post: post
  };
})(window);
