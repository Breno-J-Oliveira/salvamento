"use strict";
const fold = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
function filterRows() {
  const search = document.querySelector("[data-filter]");
  if (!search) return;
  const side = document.querySelector("[data-side-filter]");
  const list = document.querySelector(search.dataset.filter);
  let visible = 0;
  list.querySelectorAll("[data-search]").forEach(item => {
    const matches = fold(item.dataset.search).includes(fold(search.value.trim())) && (!side || !side.value || item.dataset.side === side.value);
    item.hidden = !matches;
    if (matches) visible++;
  });
  const empty = document.querySelector("[data-filter-empty]");
  if (empty) empty.hidden = visible !== 0 || (!search.value && (!side || !side.value));
}
document.querySelectorAll("[data-filter]").forEach(el => el.addEventListener("input", filterRows));
document.querySelectorAll("[data-side-filter]").forEach(el => el.addEventListener("change", filterRows));
document.querySelectorAll("form[data-confirm]").forEach(form => form.addEventListener("submit", event => { if (!window.confirm(form.dataset.confirm)) event.preventDefault(); }));
document.querySelectorAll("form[data-loading]").forEach(form => form.addEventListener("submit", () => { const button = form.querySelector("button"); button.disabled = true; button.textContent = form.dataset.loading; form.setAttribute("aria-busy", "true"); }));
document.querySelectorAll("[data-print]").forEach(button => button.addEventListener("click", () => window.print()));
function updateExpiry() { document.querySelectorAll("[data-expiry]").forEach(el => { const seconds = Math.max(0, Number(el.dataset.expiry) - Date.now() / 1000); el.textContent = seconds > 0 ? Math.ceil(seconds / 60) + " min" : "Expirado — atualize a página"; }); }
updateExpiry(); setInterval(updateExpiry, 15000);
