/* Local disclosure: opening never mutates notification state. */
(() => {
    'use strict';
    const root = document.querySelector('[data-notification-root]');
    if (!root) return;
    const button = root.querySelector('[data-notification-toggle]');
    const panel = root.querySelector('#pw-notification-panel');
    const position = () => {
        const rect = button.getBoundingClientRect();
        const viewportWidth = document.documentElement.clientWidth;
        const width = Math.min(380, viewportWidth - 24);
        panel.style.width = `${width}px`;
        panel.style.left = `${Math.max(12, Math.min(rect.right - width, viewportWidth - width - 12))}px`;
        panel.style.top = `${rect.bottom + 10}px`;
        panel.style.maxHeight = `${Math.max(0, Math.min(520, window.innerHeight - rect.bottom - 22))}px`;
    };
    const close = (restoreFocus = false) => {
        panel.hidden = true;
        button.setAttribute('aria-expanded', 'false');
        if (restoreFocus) button.focus();
    };
    button.hidden = false;
    button.addEventListener('click', () => {
        if (!panel.hidden) { close(); return; }
        position();
        panel.hidden = false;
        button.setAttribute('aria-expanded', 'true');
    });
    document.addEventListener('click', event => {
        if (!panel.hidden && !root.contains(event.target)) close(panel.contains(document.activeElement));
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !panel.hidden) {
            event.preventDefault();
            close(true);
        }
    });
    root.addEventListener('focusout', event => {
        if (event.relatedTarget && !root.contains(event.relatedTarget)) close();
    });
    window.addEventListener('resize', () => { if (!panel.hidden) position(); });
    window.addEventListener('scroll', () => { if (!panel.hidden) close(panel.contains(document.activeElement)); }, { passive: true });
    window.addEventListener('pagehide', () => close());
})();
