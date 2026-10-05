(function () {
    'use strict';
    const instances = new WeakMap();
    function init(root, env) {
        if (!root) return;
        if (instances.has(root)) return instances.get(root);
        const button = root.querySelector('.featured-bands__toggle');
        if (!button) return;
        const { doc, win, media } = env;
        let paused = false, suspended = false, hovered = false, focused = false;
        const listeners = [];
        function on(target, name, callback) {
            target.addEventListener(name, callback);
            listeners.push(() => target.removeEventListener(name, callback));
        }
        function update() {
            root.toggleAttribute('data-bands-paused', paused || media.matches || doc.hidden || suspended || hovered || focused);
            root.toggleAttribute('data-bands-static', media.matches);
            button.hidden = media.matches;
            button.setAttribute('aria-pressed', String(paused));
            button.setAttribute('aria-label', (paused ? 'Reanudar' : 'Pausar') + ' fotografías de Oficios destacados');
            button.querySelector('span').textContent = paused ? '▶' : 'Ⅱ';
        }
        function dispose() {
            listeners.forEach(remove => remove());
            root.removeAttribute('data-bands-ready');
            root.removeAttribute('data-bands-paused');
            root.removeAttribute('data-bands-static');
            root.removeAttribute('data-bands-browse');
            button.hidden = true;
            instances.delete(root);
        }
        on(button, 'click', () => { paused = !paused; update(); });
        on(root, 'mouseenter', () => { hovered = true; update(); });
        on(root, 'mouseleave', () => { hovered = false; update(); });
        on(root, 'focusin', event => {
            focused = true;
            // Keyboard users browse the original links in static, scrollable rows.
            if (event.target.matches('.featured-bands__card:focus-visible')) {
                root.setAttribute('data-bands-browse', '');
                event.target.scrollIntoView({ block: 'nearest', inline: 'nearest' });
            }
            update();
        });
        on(root, 'focusout', event => {
            focused = root.contains(event.relatedTarget);
            if (!focused) {
                root.removeAttribute('data-bands-browse');
                root.querySelectorAll('.featured-bands__row').forEach(row => { row.scrollLeft = 0; });
            }
            update();
        });
        on(doc, 'visibilitychange', update);
        on(media, 'change', update);
        on(win, 'pagehide', event => { if (event.persisted) { suspended = true; update(); } else dispose(); });
        on(win, 'pageshow', () => { suspended = false; update(); });
        instances.set(root, dispose);
        update();
        root.setAttribute('data-bands-ready', '');
        return dispose;
    }
    if (typeof module !== 'undefined' && module.exports) module.exports = { init };
    if (typeof document !== 'undefined') {
        const root = document.querySelector('.featured-bands');
        if (root) init(root, { doc: document, win: window, media: window.matchMedia('(prefers-reduced-motion: reduce)') });
    }
}());
