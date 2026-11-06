"use strict";
const fold = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
function filterRows() {
  const search = document.querySelector("[data-filter]");
  if (!search) return;
  const side = document.querySelector("[data-side-filter]");
  const list = document.querySelector(search.dataset.filter);
  if (!list) return;
  let visible = 0;
  list.querySelectorAll("[data-search]").forEach(item => {
    const matches = fold(item.dataset.search).includes(fold(search.value.trim())) && (!side || !side.value || item.dataset.side === side.value);
    item.hidden = !matches;
    if (matches) visible++;
  });
  const empty = document.querySelector("[data-filter-empty]");
  if (empty) empty.hidden = visible !== 0 || (!search.value && (!side || !side.value));
  let status = document.querySelector("[data-filter-status]");
  if (!status) {
    status = document.createElement("p"); status.className = "sr-only"; status.dataset.filterStatus = "";
    status.setAttribute("role", "status"); search.parentElement.append(status);
  }
  status.textContent = visible + (visible === 1 ? " resultado encontrado." : " resultados encontrados.");
}
document.querySelectorAll("[data-filter]").forEach(el => el.addEventListener("input", filterRows));
document.querySelectorAll("[data-side-filter]").forEach(el => el.addEventListener("change", filterRows));

const pendingForms = new WeakSet();
const originalButtons = new WeakMap();
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener("submit", event => {
    if (event.defaultPrevented) return;
    if (pendingForms.has(form)) { event.preventDefault(); return; }
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) { event.preventDefault(); return; }
    pendingForms.add(form);
    // Outros listeners ainda podem cancelar o envio antes de bloquear os controles.
    queueMicrotask(() => {
      if (event.defaultPrevented) { pendingForms.delete(form); return; }
      form.setAttribute("aria-busy", "true");
      form.querySelectorAll('button:not([type="button"]), input[type="submit"]').forEach(button => {
        originalButtons.set(button, { disabled: button.disabled, text: button.textContent });
        button.disabled = true;
        if (form.dataset.loading && button.tagName === "BUTTON") button.textContent = form.dataset.loading;
      });
    });
  });
});
window.addEventListener("pageshow", () => {
  document.querySelectorAll('form[aria-busy="true"]').forEach(form => {
    pendingForms.delete(form); form.removeAttribute("aria-busy");
    form.querySelectorAll("button, input[type=submit]").forEach(button => {
      const original = originalButtons.get(button);
      if (original) { button.disabled = original.disabled; button.textContent = original.text; }
    });
  });
  filterRows(); updateExpiry();
});
document.querySelectorAll("[data-print]").forEach(button => button.addEventListener("click", () => window.print()));
function updateExpiry() {
  document.querySelectorAll("[data-expiry]").forEach(el => {
    const expiry = Number(el.dataset.expiry);
    if (!Number.isFinite(expiry)) return;
    const seconds = Math.max(0, expiry - Date.now() / 1000);
    el.textContent = seconds > 0 ? Math.ceil(seconds / 60) + " min" : "Expirado — atualize a página";
  });
}
updateExpiry(); setInterval(updateExpiry, 15000);
