/* Local, explicit copy only. No navigation, fetch, or financial operation. */
(function () {
  'use strict';
  document.querySelectorAll('[data-collection-copy]').forEach(function (root) {
    var input = root.querySelector('input');
    var button = root.querySelector('[data-copy-button]');
    var status = root.querySelector('[data-copy-status]');
    if (!input || !button || !status) return;
    button.hidden = false;
    button.addEventListener('click', async function () {
      try {
        if (!navigator.clipboard || !window.isSecureContext) throw new Error('manual');
        await navigator.clipboard.writeText(input.value);
        status.textContent = 'Enlace simulado copiado.';
      } catch (_) {
        input.focus(); input.select();
        status.textContent = 'Enlace seleccionado. Usá Copiar o Ctrl+C para copiarlo.';
      }
    });
  });
}());
