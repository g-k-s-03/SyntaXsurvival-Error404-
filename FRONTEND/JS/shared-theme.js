(function () {
  var KEY = 'bc_theme';
  var root = document.documentElement;

  function getTheme() {
    return localStorage.getItem(KEY) === 'light' ? 'light' : 'dark';
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme');
    }
    try {
      localStorage.setItem(KEY, theme);
    } catch (_) {}
    syncToggleLabels();
  }

  function syncToggleLabels() {
    var t = getTheme();
    document.querySelectorAll('.theme-toggle').forEach(function (btn) {
      btn.textContent = t === 'light' ? 'Dark mode' : 'Light mode';
      btn.setAttribute('aria-pressed', t === 'light' ? 'true' : 'false');
    });
  }

  applyTheme(getTheme());

  document.querySelectorAll('.theme-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      applyTheme(getTheme() === 'light' ? 'dark' : 'light');
    });
  });

  window.addEventListener('storage', function (e) {
    if (e.key === KEY) applyTheme(getTheme());
  });
})();
