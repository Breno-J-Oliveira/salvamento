(() => {
  'use strict';

  const root = document.querySelector('[data-remote-session]');
  if (!root) return;

  const transcript = root.querySelector('[data-command-history]');
  const pollStatus = root.querySelector('[data-poll-status]');
  const sessionStatus = root.querySelector('[data-session-status]');
  const agentStatus = root.querySelector('[data-agent-status]');
  const commandForm = root.querySelector('[data-command-form]');
  const commandButton = root.querySelector('[data-command-submit]');
  const notes = root.querySelector('[data-remote-notes]');
  const commandLabels = {
    queued: 'Na fila', running: 'Executando', completed: 'Concluído',
    failed: 'Falhou', interrupted: 'Interrompido'
  };
  const sessionLabels = {active: 'Em andamento', ended: 'Encerrada', expired: 'Prazo encerrado'};
  let previousCommands = '';
  let previousNotes = '';
  let stopped = root.dataset.sessionState !== 'active';
  let failures = 0;

  const expiry = root.querySelector('[data-session-expiry]');
  const expiresAt = Number(root.dataset.expiresAt);
  if (Number.isFinite(expiresAt) && expiresAt > 0) {
    const date = new Date(expiresAt * 1000);
    expiry.dateTime = date.toISOString();
    expiry.textContent = date.toLocaleString('pt-BR', {timeZone: 'America/Sao_Paulo'}) + ' · Brasília';
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = text;
    return node;
  }

  function renderCommands(commands) {
    const serialized = JSON.stringify(commands);
    if (serialized === previousCommands) return;
    // Preserve the reader's selection while they copy an item from the transcript.
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed && transcript.contains(selection.anchorNode)) return;
    previousCommands = serialized;
    const scrollTop = transcript.scrollTop;
    const fragment = document.createDocumentFragment();
    commands.forEach(command => {
      const article = element('article', 'remote-command', '');
      article.dataset.commandId = String(command.id);
      const heading = element('div', 'remote-command-heading', '');
      const prompt = element('span', 'remote-prompt', '$');
      prompt.setAttribute('aria-hidden', 'true');
      heading.append(prompt, element('code', '', command.command),
        element('span', 'remote-command-state', commandLabels[command.status] || command.status));
      const waiting = command.status === 'queued' || command.status === 'running';
      article.append(heading, element('pre', '', command.output || (waiting ? 'Aguardando resultado…' : 'Sem saída registrada.')));
      if (command.exit_code !== null && command.exit_code !== undefined) {
        article.append(element('p', 'remote-exit', 'Código de saída ' + command.exit_code));
      }
      fragment.append(article);
    });
    if (!commands.length) fragment.append(element('p', 'remote-transcript-empty', 'Nenhum comando registrado.'));
    transcript.replaceChildren(fragment);
    transcript.scrollTop = scrollTop;
  }

  function renderNotes(items) {
    if (!notes) return;
    const serialized = JSON.stringify(items);
    if (serialized === previousNotes) return;
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed && notes.contains(selection.anchorNode)) return;
    previousNotes = serialized;
    const fragment = document.createDocumentFragment();
    items.forEach(note => {
      const article = element('article', 'remote-note', '');
      article.append(element('p', '', note.body));
      fragment.append(article);
    });
    if (!items.length) fragment.append(element('p', 'field-help', 'Nenhuma observação registrada.'));
    notes.replaceChildren(fragment);
  }

  function update(data) {
    const current = data.session;
    const active = current.status === 'active';
    const pending = data.commands.some(command => command.status === 'queued' || command.status === 'running');
    sessionStatus.textContent = sessionLabels[current.status] || current.status;
    sessionStatus.dataset.state = current.status;
    agentStatus.textContent = current.machine_online ? 'Ambiente conectado' : 'Aguardando conexão do ambiente';
    if (commandButton) commandButton.disabled = !active || !current.machine_online || pending;
    if (commandForm) commandForm.querySelector('textarea').disabled = !active;
    root.querySelector('[data-end-form]').hidden = !active;
    if (!active) root.querySelector('[data-end-description]').textContent = 'O histórico foi preservado. Este ambiente foi retirado de uso.';
    renderCommands(data.commands);
    renderNotes(data.notes || []);
    pollStatus.dataset.error = 'false';
    const message = active ? (pending ? 'Comando em andamento. Acompanhando o resultado.' : 'Histórico atualizado. Acompanhamento ativo.') : 'Sessão encerrada. Histórico atualizado.';
    if (pollStatus.textContent !== message) pollStatus.textContent = message;
    stopped = !active;
  }

  async function poll() {
    if (stopped) return;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(root.dataset.eventsUrl, {
        credentials: 'same-origin', cache: 'no-store', redirect: 'error',
        headers: {'Accept': 'application/json'}, signal: controller.signal
      });
      if (!response.ok) throw new Error('Status ' + response.status);
      const data = await response.json();
      if (!data.session || !Array.isArray(data.commands)) throw new Error('Resposta inválida');
      update(data);
      failures = 0;
    } catch (_) {
      failures += 1;
      pollStatus.dataset.error = 'true';
      pollStatus.textContent = 'A atualização perdeu a conexão. O histórico exibido pode estar desatualizado. Tentando novamente…';
      if (commandButton) commandButton.disabled = true;
    } finally {
      window.clearTimeout(timeout);
      if (!stopped) window.setTimeout(poll, failures > 2 ? 10000 : 3000);
    }
  }

  window.addEventListener('pagehide', () => { stopped = true; });
  if (!stopped) poll();
})();
