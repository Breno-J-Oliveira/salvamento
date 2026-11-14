"use strict";
const fold = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
function filterRows() {
  const search = document.querySelector("[data-filter]");
  if (!search) return;
  const side = document.querySelector("[data-side-filter]");
  const audience = document.querySelector("[data-audience-filter]");
  const list = document.querySelector(search.dataset.filter);
  if (!list) return;
  let visible = 0;
  list.querySelectorAll("[data-search]").forEach(item => {
    // Desafios para "Todos" aparecem em qualquer filtro de público.
    const audienceMatch = !audience || !audience.value || !item.dataset.audience || item.dataset.audience === audience.value || item.dataset.audience === "Todos";
    const matches = fold(item.dataset.search).includes(fold(search.value.trim())) && (!side || !side.value || item.dataset.side === side.value) && audienceMatch;
    item.hidden = !matches;
    if (matches) visible++;
  });
  const empty = document.querySelector("[data-filter-empty]");
  if (empty) empty.hidden = visible !== 0 || (!search.value && (!side || !side.value) && (!audience || !audience.value));
  let status = document.querySelector("[data-filter-status]");
  if (!status) {
    status = document.createElement("p"); status.className = "sr-only"; status.dataset.filterStatus = "";
    status.setAttribute("role", "status"); search.parentElement.append(status);
  }
  status.textContent = visible + (visible === 1 ? " resultado encontrado." : " resultados encontrados.");
}
document.querySelectorAll("[data-filter]").forEach(el => el.addEventListener("input", filterRows));
document.querySelectorAll("[data-side-filter],[data-audience-filter]").forEach(el => el.addEventListener("change", filterRows));

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


// Editor de perguntas: serialização compatível e prévia somente local.
document.querySelectorAll('[data-question-editor]').forEach(form => {
  const list = form.querySelector('[data-question-list]');
  const status = form.querySelector('[data-editor-status]');
  const add = form.querySelector('[data-question-add]');
  const save = form.querySelector('[data-question-save]');
  const preview = form.querySelector('[data-question-preview]');
  const undo = form.querySelector('[data-question-undo]');
  let sequence = 0, submitting = false, lastRemoved = null;
  const optionValues = row => row.querySelector('[data-question-options]').value.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
  function questions() {
    return Array.from(list.children, row => {
      const type = row.querySelector('[data-question-type]').value;
      return {id:row.dataset.questionId, label:row.querySelector('[data-question-label]').value.trim(), type,
        required:row.querySelector('[data-question-required]').checked,
        options:['select','multiselect'].includes(type) ? optionValues(row) : [],
        correct:type === 'select' ? row.querySelector('[data-question-answer]').value : ''};
    });
  }
  function newKey() {
    const existing = new Set(Array.from(list.children, row => row.dataset.questionId));
    if (lastRemoved) existing.add(lastRemoved.row.dataset.questionId);
    let key; do { key = 'question_' + (++sequence); } while (existing.has(key));
    return key;
  }
  function renderPreview() {
    if (!preview) return;
    preview.replaceChildren();
    questions().forEach((q, index) => {
      const field = document.createElement('fieldset'); field.className = 'question-preview-field';
      const legend = document.createElement('legend'); legend.textContent = (index + 1) + '. ' + (q.label || 'Pergunta sem título') + (q.required ? ' *' : ''); field.append(legend);
      if (['select','multiselect'].includes(q.type)) {
        q.options.forEach(value => {
          const label = document.createElement('label'); label.className = 'choice-label';
          const input = document.createElement('input'); input.type = q.type === 'select' ? 'radio' : 'checkbox'; input.disabled = true;
          label.append(input, document.createTextNode(value)); field.append(label);
        });
        if (!q.options.length) { const note = document.createElement('p'); note.textContent = 'Adicione opções para conferir este formato.'; field.append(note); }
      } else {
        const input = document.createElement(q.type === 'textarea' ? 'textarea' : 'input');
        if (input.tagName === 'INPUT') input.type = ['number','url'].includes(q.type) ? q.type : 'text';
        input.disabled = true; input.setAttribute('aria-label', q.label || 'Resposta'); if (q.type === 'textarea') input.rows = 3;
        field.append(input);
      }
      preview.append(field);
    });
  }
  function syncCount(message) {
    const rows = Array.from(list.children), count = rows.length;
    status.textContent = message || count + (count === 1 ? ' pergunta no formulário.' : ' perguntas no formulário.');
    add.disabled = count >= 15; save.disabled = count === 0;
    undo.hidden = !lastRemoved; undo.disabled = count >= 15;
    rows.forEach((row, index) => {
      row.querySelector('legend').textContent = 'Pergunta ' + (index + 1);
      row.querySelector('[data-question-up]').disabled = index === 0;
      row.querySelector('[data-question-down]').disabled = index === count - 1;
      row.querySelector('[data-question-duplicate]').disabled = count >= 15;
    });
    renderPreview();
  }
  function bindQuestion(row) {
    const type = row.querySelector('[data-question-type]'), text = row.querySelector('[data-question-label]');
    const options = row.querySelector('[data-question-options]'), optionsLabel = row.querySelector('[data-question-options-label]');
    const answer = row.querySelector('[data-question-answer]'), answerLabel = row.querySelector('[data-question-answer-label]');
    const textCount = document.createElement('span'); textCount.className = 'field-help'; textCount.dataset.questionTextCount = ''; text.after(textCount);
    const optionsCount = document.createElement('span'); optionsCount.className = 'field-help'; optionsCount.dataset.questionOptionsCount = ''; options.after(optionsCount);
    function refreshAnswer() {
      const selected = answer.value || answer.dataset.current || '';
      answer.replaceChildren(new Option('Sem correção automática', ''));
      optionValues(row).forEach(value => answer.add(new Option(value, value)));
      if (Array.from(answer.options).some(option => option.value === selected)) answer.value = selected;
      answer.dataset.current = '';
    }
    function counters() {
      textCount.textContent = text.value.length + '/200 caracteres';
      const values = optionValues(row), valid = values.length <= 20 && values.every(value => value.length <= 100) && new Set(values).size === values.length;
      optionsCount.textContent = values.length + '/20 opções' + (valid ? '' : ' — confira duplicatas e o limite de 100 caracteres por opção.');
      options.setCustomValidity(!optionsLabel.hidden && !valid ? 'Use até 20 opções diferentes, com até 100 caracteres cada.' : '');
    }
    function showOptions() {
      optionsLabel.hidden = !['select','multiselect'].includes(type.value); options.required = !optionsLabel.hidden;
      answerLabel.hidden = type.value !== 'select'; refreshAnswer(); counters(); renderPreview();
    }
    options.addEventListener('input', () => { refreshAnswer(); counters(); });
    type.addEventListener('change', showOptions);
    row.addEventListener('input', () => { counters(); renderPreview(); });
    row.addEventListener('change', renderPreview);
    row.querySelector('[data-question-remove]').addEventListener('click', () => { lastRemoved = {row, next:row.nextElementSibling}; row.remove(); syncCount('Pergunta removida. Você pode desfazer a última remoção antes de salvar.'); undo.focus(); });
    row.querySelector('[data-question-up]').addEventListener('click', event => {
      const previous = row.previousElementSibling; if (!previous) return;
      list.insertBefore(row, previous); syncCount('Pergunta movida para cima. Salve para aplicar a nova ordem.'); event.currentTarget.focus();
    });
    row.querySelector('[data-question-down]').addEventListener('click', event => {
      const next = row.nextElementSibling; if (!next) return;
      list.insertBefore(next, row); syncCount('Pergunta movida para baixo. Salve para aplicar a nova ordem.'); event.currentTarget.focus();
    });
    row.querySelector('[data-question-duplicate]').addEventListener('click', () => {
      if (list.children.length >= 15) return;
      const copy = form.querySelector('[data-question-template]').content.firstElementChild.cloneNode(true);
      copy.dataset.questionId = newKey();
      for (const selector of ['[data-question-label]','[data-question-type]','[data-question-options]']) copy.querySelector(selector).value = row.querySelector(selector).value;
      copy.querySelector('[data-question-required]').checked = row.querySelector('[data-question-required]').checked;
      copy.querySelector('[data-question-answer]').dataset.current = answer.value;
      row.after(copy); bindQuestion(copy); syncCount('Pergunta duplicada com novo identificador. Revise antes de salvar.'); copy.querySelector('[data-question-label]').focus();
    });
    showOptions();
  }
  Array.from(list.children).forEach(bindQuestion); add.hidden = false; syncCount();
  undo.addEventListener('click', () => {
    if (!lastRemoved || submitting || list.children.length >= 15) return;
    const {row, next} = lastRemoved;
    if (next && next.parentElement === list) list.insertBefore(row, next); else list.append(row);
    lastRemoved = null; syncCount('Pergunta restaurada com suas opções e gabarito.'); row.querySelector('[data-question-label]').focus();
  });
  const initialState = JSON.stringify(questions());
  window.addEventListener('beforeunload', event => {
    if (!submitting && JSON.stringify(questions()) !== initialState) { event.preventDefault(); event.returnValue = ''; }
  });
  add.addEventListener('click', () => {
    if (list.children.length >= 15) return;
    const row = form.querySelector('[data-question-template]').content.firstElementChild.cloneNode(true);
    row.dataset.questionId = newKey(); list.append(row); bindQuestion(row);
    row.querySelector('[data-question-label]').focus(); syncCount('Pergunta adicionada. Preencha o texto e escolha o formato.');
  });
  form.addEventListener('submit', event => {
    const items = questions();
    if (!items.length || items.some(q => q.options.length > 20 || q.options.some(option => option.length > 100) || new Set(q.options).size !== q.options.length)) {
      event.preventDefault(); status.textContent = 'Confira as opções: no máximo 20 opções únicas, com até 100 caracteres cada.'; status.focus(); return;
    }
    form.querySelectorAll('[data-question-serialized]').forEach(input => input.remove());
    function hidden(name, value) { const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value; input.dataset.questionSerialized = ''; form.append(input); }
    hidden('question_count', items.length);
    items.forEach((q, index) => {
      const prefix = 'question_' + index + '_';
      hidden(prefix + 'id', q.id); hidden(prefix + 'label', q.label); hidden(prefix + 'type', q.type); hidden(prefix + 'required', q.required ? '1' : '0'); hidden(prefix + 'correct', q.correct);
      q.options.forEach(option => hidden(prefix + 'option', option));
    });
    queueMicrotask(() => { if (!event.defaultPrevented) { submitting = true; lastRemoved = null; undo.hidden = true; } });
  });
});
