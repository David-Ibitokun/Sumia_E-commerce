// Dark Mode State Handler
(function () {
  function getPreferredTheme() {
    const saved = localStorage.getItem('sumia-theme') || localStorage.getItem('theme');
    if (saved) return saved;
    return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (document.body) {
      document.body.setAttribute('data-theme', theme);
    }
  }

  const currentTheme = getPreferredTheme();
  applyTheme(currentTheme);

  document.addEventListener('DOMContentLoaded', function () {
    applyTheme(document.documentElement.getAttribute('data-theme') || currentTheme);
    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    const activeTheme = document.documentElement.getAttribute('data-theme') || currentTheme;
    updateIcons(activeTheme);

    toggleBtns.forEach(btn => {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const active = document.documentElement.getAttribute('data-theme');
        const newTheme = active === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        try {
          localStorage.setItem('sumia-theme', newTheme);
          localStorage.setItem('theme', newTheme);
        } catch (err) {}
        updateIcons(newTheme);
      });
    });

    function updateIcons(theme) {
      toggleBtns.forEach(btn => {
        const icon = btn.querySelector('i');
        if (icon) {
          if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            btn.setAttribute('title', 'Switch to Light Mode');
            btn.setAttribute('aria-label', 'Switch to Light Mode');
          } else {
            icon.className = 'fas fa-moon';
            btn.setAttribute('title', 'Switch to Dark Mode');
            btn.setAttribute('aria-label', 'Switch to Dark Mode');
          }
        }
      });
    }
  });
})();
