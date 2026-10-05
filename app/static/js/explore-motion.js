(function () {
    'use strict';
    const instances = new WeakMap();
    function init(root, env) {
        if (!root) return;
        if (instances.has(root)) return instances.get(root);
        const slides = Array.from(root.querySelectorAll('.explore-scenes__image'));
        if (slides.length < 2) return;
        const { doc, win, media } = env;
        let index = 0, timer = null, hovered = false, focused = false, suspended = false;
        const listeners = [];
        function on(target, name, callback) {
            target.addEventListener(name, callback);
            listeners.push(() => target.removeEventListener(name, callback));
        }
        function stop() {
            if (timer !== null) win.clearTimeout(timer);
            timer = null;
        }
        function schedule() {
            stop();
            if (!media.matches && !doc.hidden && !hovered && !focused && !suspended) {
                timer = win.setTimeout(() => show(index + 1), 8000);
            }
        }
        function show(target) {
            index = (target + slides.length) % slides.length;
            slides.forEach((slide, i) => slide.classList.toggle('is-active', i === index));
            schedule();
        }
        function dispose() {
            stop();
            listeners.forEach(remove => remove());
            slides.forEach((slide, i) => slide.classList.toggle('is-active', i === 0));
            instances.delete(root);
        }
        on(root, 'mouseenter', () => { hovered = true; schedule(); });
        on(root, 'mouseleave', () => { hovered = false; schedule(); });
        on(root, 'focusin', () => { focused = true; schedule(); });
        on(root, 'focusout', event => { focused = root.contains(event.relatedTarget); schedule(); });
        on(doc, 'visibilitychange', schedule);
        on(media, 'change', schedule);
        // Keep bfcache restores functional; fully remove handlers on final departure.
        on(win, 'pagehide', event => { if (event.persisted) { suspended = true; stop(); } else dispose(); });
        on(win, 'pageshow', () => { suspended = false; schedule(); });
        instances.set(root, dispose);
        show(0);
        return dispose;
    }
    if (typeof module !== 'undefined' && module.exports) module.exports = { init };
    if (typeof document !== 'undefined') {
        const root = document.querySelector('.explore-rubros__hero');
        if (root) init(root, { doc: document, win: window, media: window.matchMedia('(prefers-reduced-motion: reduce)') });
    }
}());
