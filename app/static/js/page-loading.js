(function () {
    "use strict";
    function init(doc, win) {
        const overlay = doc.querySelector("[data-page-loading]");
        if (!overlay || overlay.hasAttribute("data-loading-ready")) return;
        overlay.setAttribute("data-loading-ready", "");
        const status = overlay.querySelector("[data-loading-status]");
        const main = doc.querySelector("main, [role='main']") || doc.body;
        let timers = [], busy = false, previousBusy = null, generation = 0;
        function reset() {
            generation += 1;
            timers.forEach(id => win.clearTimeout(id));
            timers = [];
            overlay.hidden = true;
            status.textContent = "";
            if (busy) {
                if (previousBusy === null) main.removeAttribute("aria-busy");
                else main.setAttribute("aria-busy", previousBusy);
            }
            busy = false;
        }
        function start(event, previewDuration = 0) {
            reset();
            const token = generation;
            // Allow subsequent bubbling listeners to cancel the native action.
            win.queueMicrotask(() => {
                if (event.defaultPrevented || generation !== token) return;
                timers.push(win.setTimeout(() => {
                    previousBusy = main.getAttribute("aria-busy");
                    main.setAttribute("aria-busy", "true");
                    busy = true;
                    overlay.hidden = false;
                    status.textContent = "Cargando contenido";
                }, 300));
                timers.push(win.setTimeout(() => {
                    status.textContent = "Esto está tardando un poco más. Seguimos trabajando.";
                }, 8000));
                timers.push(win.setTimeout(reset, 30000));
                if (previewDuration) timers.push(win.setTimeout(reset, previewDuration));
            });
        }
        function internal(href, target) {
            if (target && target.toLowerCase() !== "_self") return false;
            try {
                const url = new URL(href, doc.baseURI);
                return /^(https?:)$/.test(url.protocol) && url.origin === win.location.origin;
            } catch (_) { return false; }
        }
        function defaultTarget() {
            const base = doc.querySelector("base[target]");
            return base ? base.getAttribute("target") : "";
        }
        doc.addEventListener("click", event => {
            if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) return;
            const link = event.target.closest && event.target.closest("a[href]");
            if (!link || link.closest("[data-no-loading]") || link.hasAttribute("download")) return;
            if (!internal(link.href, link.getAttribute("target") || defaultTarget())) return;
            const url = new URL(link.href, doc.baseURI);
            const current = new URL(win.location.href);
            if (url.pathname === current.pathname && url.search === current.search && (url.hash || link.getAttribute("href").includes("#"))) return;
            start(event);
        });
        doc.addEventListener("submit", event => {
            const form = event.target, button = event.submitter;
            if (event.defaultPrevented || form.closest("[data-no-loading]") || (button && button.closest("[data-no-loading]"))) return;
            const attr = name => button && button.hasAttribute("form" + name) ? button.getAttribute("form" + name) : form.getAttribute(name);
            if ((attr("method") || "get").toLowerCase() === "dialog") return;
            if (!internal(attr("action") || win.location.href, attr("target") || defaultTarget())) return;
            if (!form.noValidate && !(button && button.formNoValidate) && !form.checkValidity()) return;
            start(event);
        });
        doc.addEventListener("keydown", event => { if (event.key === "Escape") reset(); });
        doc.addEventListener("invalid", reset, true);
        win.addEventListener("pageshow", reset);
        win.addEventListener("pagehide", reset);
        // This marker is rendered only by the guarded /dev/qa/estados template.
        const preview = doc.querySelector("[data-loading-preview]");
        if (preview) preview.addEventListener("click", event => start(event, 12000));
        // Observe cancellation without intercepting navigation or sacrificing bfcache.
        if (win.navigation) {
            win.navigation.addEventListener("navigateerror", reset);
            win.navigation.addEventListener("navigatesuccess", reset);
            win.navigation.addEventListener("navigate", event => {
                const token = generation;
                if (event.signal) event.signal.addEventListener("abort", () => {
                    if (generation === token) reset();
                }, { once: true });
            });
        }
        return { reset };
    }
    if (typeof module === "object" && module.exports) module.exports = { init };
    if (typeof document !== "undefined") init(document, window);
})();
