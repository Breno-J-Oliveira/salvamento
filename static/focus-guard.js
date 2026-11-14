"use strict";
// Modo de foco do desafio: pede confirmação ao sair e registra uma ocorrência a cada saída da tela.
// O navegador não permite bloquear a troca de aba; por isso o objetivo é avisar e registrar.
(() => {
  const root = document.querySelector("[data-focus-guard]");
  if (!root) return;
  const url = root.dataset.url;
  const token = root.dataset.csrf;
  const counter = root.querySelector("[data-focus-count]");
  const status = root.querySelector("[data-focus-status]");
  const fullscreenButton = root.querySelector("[data-fullscreen]");
  const labels = {
    tab_hidden: "você trocou de aba ou minimizou a janela",
    window_blur: "você saiu da janela do desafio",
    fullscreen_exit: "você saiu da tela cheia",
    page_leave: "você tentou sair da página",
  };
  let total = Number(root.dataset.count || 0);
  let allowLeave = false;   // envio de formulário da própria página: recarrega sem aviso
  let labPause = false;     // abertura do laboratório em outra aba é uma saída autorizada
  let lastSent = 0;
  let wasFullscreen = false;

  function render(kind) {
    if (counter) counter.textContent = String(total);
    if (status) {
      const time = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      status.textContent = "Ocorrência registrada às " + time + ": " + labels[kind] + ".";
    }
    root.classList.add("focus-alert");
  }

  function report(kind) {
    const now = Date.now();
    if (now - lastSent < 2000) return;  // uma troca de aba dispara vários eventos
    lastSent = now;
    const body = new FormData();
    body.append("csrf_token", token);
    body.append("kind", kind);
    let queued = false;
    try { queued = navigator.sendBeacon(url, body); } catch (error) { queued = false; }
    if (!queued) {
      fetch(url, { method: "POST", body, credentials: "same-origin", keepalive: true }).catch(() => {});
    }
    total += 1;
    render(kind);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (!labPause) report("tab_hidden");
    } else if (labPause) {
      labPause = false;
    }
  });

  window.addEventListener("blur", () => {
    // Aguarda um instante: trocar de aba também dispara blur, e esse caso já é coberto acima.
    setTimeout(() => {
      if (!document.hidden && !document.hasFocus() && !labPause && !allowLeave) report("window_blur");
    }, 400);
  });
  window.addEventListener("focus", () => { if (!document.hidden) labPause = false; });

  document.addEventListener("fullscreenchange", () => {
    const now = Boolean(document.fullscreenElement);
    if (wasFullscreen && !now && !allowLeave) report("fullscreen_exit");
    wasFullscreen = now;
    if (fullscreenButton) fullscreenButton.hidden = now;
  });

  window.addEventListener("beforeunload", event => {
    if (allowLeave) return;
    report("page_leave");
    event.preventDefault();
    event.returnValue = "";
  });
  window.addEventListener("pagehide", () => { if (!allowLeave) report("page_leave"); });

  // Ao voltar pelo histórico (cache de páginas), o modo de foco volta a valer.
  window.addEventListener("pageshow", event => { if (event.persisted) { allowLeave = false; labPause = false; } });

  // Formulários desta página (enviar flag, iniciar/encerrar ambiente) recarregam a tela de propósito.
  document.querySelectorAll("main form").forEach(form => form.addEventListener("submit", () => { allowLeave = true; }));
  // O laboratório abre em outra aba por necessidade do desafio.
  document.querySelectorAll("[data-lab-link]").forEach(link => link.addEventListener("click", () => { labPause = true; }));

  if (fullscreenButton) {
    if (!document.documentElement.requestFullscreen) {
      fullscreenButton.hidden = true;
    } else {
      fullscreenButton.addEventListener("click", () => {
        document.documentElement.requestFullscreen().catch(() => {
          if (status) status.textContent = "O navegador não permitiu a tela cheia. Continue nesta tela.";
        });
      });
    }
  }
})();
