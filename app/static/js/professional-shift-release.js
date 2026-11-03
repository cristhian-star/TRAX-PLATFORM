/* Deadline display only. The server authorizes every release under locks. */
(() => {
  document.querySelectorAll('[data-release-form]').forEach(form => {
    const button = form.querySelector('button[type="submit"]');
    const help = form.querySelector('[data-release-help]');
    const remaining = Date.parse(form.dataset.releaseDeadline) - Date.parse(form.dataset.serverNow);
    const started = performance.now();
    function update() {
      const delay = remaining - (performance.now() - started);
      if (!Number.isFinite(delay) || delay <= 0) {
        button.disabled = true;
        help.textContent = 'Liberación no disponible: el plazo termina 12 horas antes del inicio.';
      } else if (!button.disabled) {
        window.setTimeout(update, Math.min(delay, 60000));
      }
    }
    form.addEventListener('submit', event => {
      if (remaining <= performance.now() - started || button.disabled) {
        event.preventDefault();
        update();
      }
    });
    document.addEventListener('visibilitychange', () => { if (!document.hidden) update(); });
    update();
  });
})();
