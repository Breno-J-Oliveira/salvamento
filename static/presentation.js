'use strict';
// Keep navigation available without JavaScript; collapse only on small screens.
const navigation = document.getElementById('site-navigation');
const menuToggle = document.querySelector('.nav-toggle');
if (navigation && menuToggle) {
  const compact = window.matchMedia('(max-width: 900px)');
  function setOpen(open) {
    navigation.hidden = !open;
    menuToggle.setAttribute('aria-expanded', String(open));
    menuToggle.textContent = open ? 'Fechar menu' : 'Menu';
  }
  function syncMenu() { menuToggle.hidden = !compact.matches; setOpen(!compact.matches); }
  syncMenu();
  compact.addEventListener('change', syncMenu);
  menuToggle.addEventListener('click', () => setOpen(navigation.hidden));
  navigation.addEventListener('click', event => {
    if (compact.matches && event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      navigation.querySelectorAll('details[open]').forEach(item => { item.open = false; });
      if (compact.matches && !navigation.hidden) { setOpen(false); menuToggle.focus(); }
    }
  });
  document.addEventListener('click', event => {
    navigation.querySelectorAll('details[open]').forEach(item => {
      if (!item.contains(event.target)) item.open = false;
    });
  });
}
