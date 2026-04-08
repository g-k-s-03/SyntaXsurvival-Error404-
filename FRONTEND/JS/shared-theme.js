(() => {
  const storageKey = "bb_theme";
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(storageKey, theme);
    } catch (_) {}
  }

  function getSavedTheme() {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved === "light" || saved === "dark") return saved;
    } catch (_) {}
    return "dark";
  }

  function ensureToggle() {
    if (document.querySelector(".theme-toggle")) return;
    const host = document.querySelector(".nav-right") || document.querySelector(".nav-inner");
    if (!host) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "theme-toggle";
    btn.setAttribute("aria-label", "Toggle light and dark theme");

    const render = () => {
      const dark = root.getAttribute("data-theme") !== "light";
      btn.textContent = dark ? "Light" : "Dark";
      btn.setAttribute("title", dark ? "Switch to light mode" : "Switch to dark mode");
    };

    btn.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      applyTheme(next);
      render();
    });

    host.appendChild(btn);
    render();
  }

  applyTheme(getSavedTheme());
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureToggle);
  } else {
    ensureToggle();
  }
})();
