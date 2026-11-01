// Retain automatic OS theme following; omit the retired K8s memory adapter.
(() => {
  const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)');
  const syncTheme = () => {
    const dark = preferredTheme.matches;
    const root = document.documentElement;
    root.classList.toggle('dark', dark);
    root.classList.toggle('light', !dark);
    root.classList.toggle('scheme-dark', dark);
    root.classList.toggle('scheme-light', !dark);
    root.style.colorScheme = dark ? 'dark' : 'light';
    localStorage.setItem('theme-mode', dark ? 'dark' : 'light');
  };
  syncTheme();
  preferredTheme.addEventListener('change', syncTheme);
  new MutationObserver(() => {
    if (document.documentElement.classList.contains('dark') !== preferredTheme.matches) syncTheme();
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
})();
