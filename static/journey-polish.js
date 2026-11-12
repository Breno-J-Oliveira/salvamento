"use strict";
document.querySelectorAll("[data-password-toggle]").forEach(button => {
  const input = document.getElementById(button.getAttribute("aria-controls"));
  if (!input) return;
  button.hidden = false;
  button.addEventListener("click", () => {
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    button.setAttribute("aria-pressed", String(visible));
    button.textContent = visible ? "Ocultar senha" : "Mostrar senha";
  });
});
