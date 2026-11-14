// Aplica o tema antes da pintura para evitar piscar. Padrão: preferência do sistema.
(function () {
  var t = null;
  try { t = localStorage.getItem('pt-theme'); } catch (e) {}
  if (t !== 'light' && t !== 'dark') t = (window.matchMedia && matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('[data-theme-toggle]');
    if (!b) return;
    var next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    b.setAttribute('aria-pressed', next === 'light' ? 'true' : 'false');
    b.setAttribute('aria-label', next === 'light' ? 'Usar tema escuro' : 'Usar tema claro');
    try { localStorage.setItem('pt-theme', next); } catch (e) {}
  });
  document.addEventListener('DOMContentLoaded', function () {
    var light = document.documentElement.getAttribute('data-theme') === 'light';
    document.querySelectorAll('[data-theme-toggle]').forEach(function (b) {
      b.setAttribute('aria-pressed', light ? 'true' : 'false');
      b.setAttribute('aria-label', light ? 'Usar tema escuro' : 'Usar tema claro');
    });
  });
})();
