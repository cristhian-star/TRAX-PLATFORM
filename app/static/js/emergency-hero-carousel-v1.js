(function () {
    'use strict';
    const instances = new WeakMap();
    function init(root, { doc, win, media }) {
        if (!root || instances.has(root)) return;
        const slides = Array.from(root.querySelectorAll('template[data-src]'), el => el.dataset);
        const layers = Array.from(root.querySelectorAll('img'));
        if (slides.length < 2 || layers.length !== 2) return;
        const INTERVAL = 6500, DURATION = 900;
        let current = 0, front = 0, timer = null, epoch = 0, suspended = false;
        let animations = [];
        const cache = new Map();
        const allowed = () => !media.matches && !doc.hidden && !suspended;
        const load = index => {
            if (!cache.has(index)) cache.set(index, new Promise(resolve => {
                const image = new win.Image();
                image.onload = async () => {
                    try { if (image.decode) await image.decode(); resolve(true); }
                    catch (_) { resolve(false); }
                };
                image.onerror = () => resolve(false);
                image.src = slides[index].src;
            }));
            return cache.get(index);
        };
        function stop() {
            epoch += 1;
            if (timer !== null) win.clearTimeout(timer);
            timer = null;
            animations.forEach(animation => animation.cancel());
            animations = [];
            layers[front].hidden = false;
            layers[1 - front].hidden = true;
        }
        function schedule() {
            if (timer !== null) win.clearTimeout(timer);
            timer = null;
            if (allowed()) {
                void load((current + 1) % slides.length);
                timer = win.setTimeout(advance, INTERVAL);
            }
        }
        async function advance() {
            timer = null;
            const version = epoch;
            if (!allowed()) return;
            for (let offset = 1; offset < slides.length; offset += 1) {
                const next = (current + offset) % slides.length;
                const valid = await load(next);
                if (version !== epoch || !allowed()) return;
                if (!valid) continue;
                const outgoing = layers[front], incoming = layers[1 - front];
                incoming.src = slides[next].src;
                incoming.style.objectPosition = slides[next].position;
                incoming.hidden = false;
                animations = [
                    outgoing.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-100%)' }], { duration: DURATION, easing: 'ease-in-out', fill: 'forwards' }),
                    incoming.animate([{ transform: 'translateX(100%)' }, { transform: 'translateX(0)' }], { duration: DURATION, easing: 'ease-in-out', fill: 'forwards' }),
                ];
                // Schedule from the start of a slide, not 900 ms after its completion.
                schedule();
                try { await Promise.all(animations.map(animation => animation.finished)); }
                catch (_) { return; } // Lifecycle cancellation is expected, not an error.
                if (version !== epoch) return;
                outgoing.hidden = true;
                front = 1 - front;
                current = next;
                animations.forEach(animation => animation.cancel());
                animations = [];
                void load((current + 1) % slides.length);
                return;
            }
            schedule(); // All candidates failed: retain the current photograph.
        }
        function reconcile() {
            stop();
            if (media.matches) {
                current = 0;
                layers[front].src = slides[0].src;
                layers[front].style.objectPosition = slides[0].position;
            }
            schedule();
        }
        doc.addEventListener('visibilitychange', reconcile);
        media.addEventListener('change', reconcile);
        win.addEventListener('pagehide', () => { suspended = true; stop(); });
        win.addEventListener('pageshow', () => { suspended = false; reconcile(); });
        instances.set(root, true);
        schedule();
    }
    if (typeof module !== 'undefined' && module.exports) module.exports = { init };
    if (typeof document !== 'undefined') init(document.querySelector('[data-emergency-carousel]'), {
        doc: document, win: window, media: window.matchMedia('(prefers-reduced-motion: reduce)'),
    });
}());
