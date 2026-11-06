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
    // Preserve a ação escolhida antes de bloquear os botões de envio.
    // Sem isso, controles disabled podem omitir save/review na serialização.
    if (event.submitter && event.submitter.name) {
      let intent = form.querySelector('[data-submit-intent]');
      if (!intent) { intent = document.createElement('input'); intent.type = 'hidden'; intent.dataset.submitIntent = ''; form.append(intent); }
      intent.name = event.submitter.name;
      intent.value = event.submitter.value;
    }
    pendingForms.add(form);
    // Outros listeners ainda podem cancelar o envio antes de bloquear os controles.
    queueMicrotask(() => {
      if (event.defaultPrevented) { pendingForms.delete(form); return; }
      form.setAttribute("aria-busy", "true");
      if (form.dataset.loading) {
        let status = form.querySelector('[data-submit-status]');
        if (!status) { status = document.createElement('p'); status.className = 'sr-only'; status.setAttribute('role', 'status'); status.dataset.submitStatus = ''; form.append(status); }
        status.textContent = form.dataset.loading;
      }
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
    form.querySelector('[data-submit-intent]')?.remove();
    const status = form.querySelector('[data-submit-status]'); if (status) status.textContent = '';
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


// Editor de perguntas: HTML inicial e campos individuais enviados ao servidor.
document.querySelectorAll('[data-question-editor]').forEach(form => {
  const list = form.querySelector('[data-question-list]');
  const status = form.querySelector('[data-editor-status]');
  const add = form.querySelector('[data-question-add]');
  const save = form.querySelector('[data-question-save]');
  let sequence = 0;
  function syncCount(message) {
    const count = list.children.length;
    status.textContent = message || count + (count === 1 ? ' pergunta no formulário.' : ' perguntas no formulário.');
    add.disabled = count >= 15; save.disabled = count === 0;
  }
  function bindQuestion(row) {
    const type = row.querySelector('[data-question-type]');
    const options = row.querySelector('[data-question-options]');
    const optionsLabel = row.querySelector('[data-question-options-label]');
    function showOptions() { optionsLabel.hidden = !['select','multiselect'].includes(type.value); options.required = !optionsLabel.hidden; }
    type.addEventListener('change', showOptions); showOptions();
    row.querySelector('[data-question-remove]').addEventListener('click', () => { row.remove(); syncCount('Pergunta removida. Salve para aplicar à próxima versão.'); add.focus(); });
  }
  Array.from(list.children).forEach(bindQuestion); add.hidden = false; syncCount();
  add.addEventListener('click', () => {
    if (list.children.length >= 15) return;
    const row = form.querySelector('[data-question-template]').content.firstElementChild.cloneNode(true);
    const existing = new Set(Array.from(list.children, item => item.dataset.questionId));
    let key; do { key = 'question_' + (++sequence); } while (existing.has(key));
    row.dataset.questionId = key; list.append(row); bindQuestion(row);
    row.querySelector('[data-question-label]').focus(); syncCount('Pergunta adicionada. Preencha o texto e escolha o formato.');
  });
  form.addEventListener('submit', event => {
    const questions = Array.from(list.children, row => {
      const type = row.querySelector('[data-question-type]').value;
      return {id:row.dataset.questionId, label:row.querySelector('[data-question-label]').value.trim(), type, required:row.querySelector('[data-question-required]').checked,
        options:['select','multiselect'].includes(type) ? row.querySelector('[data-question-options]').value.split(/\r?\n/).map(value => value.trim()).filter(Boolean) : []};
    });
    if (!questions.length || questions.some(question => question.options.length > 20 || question.options.some(option => option.length > 100) || new Set(question.options).size !== question.options.length)) {
      event.preventDefault(); status.textContent = 'Confira as opções: no máximo 20 opções únicas, com até 100 caracteres cada.'; status.focus(); return;
    }
    form.querySelectorAll('[data-question-serialized]').forEach(input => input.remove());
    function hidden(name, value) { const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value; input.dataset.questionSerialized = ''; form.append(input); }
    hidden('question_count', questions.length);
    questions.forEach((question, index) => {
      const prefix = 'question_' + index + '_';
      hidden(prefix + 'id', question.id); hidden(prefix + 'label', question.label); hidden(prefix + 'type', question.type); hidden(prefix + 'required', question.required ? '1' : '0');
      question.options.forEach(option => hidden(prefix + 'option', option));
    });
  });
});
