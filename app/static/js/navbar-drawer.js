(function () {
    "use strict";
    const header = document.querySelector(".site-header--visitor");
    if (!header || header.hasAttribute("data-nav-ready")) return;
    const dialog = header.querySelector(".nav-drawer");
    if (!dialog || typeof dialog.showModal !== "function") return;
    const content = header.querySelector("[data-navigation-content]");
    const toggle = header.querySelector(".menu-toggle");
    const closeButton = dialog.querySelector(".nav-drawer__close");
    const drawerBody = dialog.querySelector(".nav-drawer__body");
    const brand = header.querySelector(".brand");
    const groups = [...content.querySelectorAll(".nav-dropdown")].map((details, index) => {
        const summary = details.querySelector("summary");
        const panel = details.querySelector(".nav-dropdown__menu");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "nav-accordion";
        button.textContent = summary.getAttribute("aria-label") || summary.textContent.trim().replace(/\s+/g, " ");
        button.hidden = true;
        panel.id = `nav-group-${index}`;
        button.setAttribute("aria-controls", panel.id);
        button.setAttribute("aria-expanded", "false");
        summary.after(button);
        button.addEventListener("click", () => {
            panel.hidden = !panel.hidden;
            button.setAttribute("aria-expanded", String(!panel.hidden));
        });
        return { details, summary, panel, button };
    });
    // Preserve route contracts; annotate only an exact pathname + query match.
    content.querySelectorAll("a[href]").forEach((link) => {
        const url = new URL(link.href, window.location.href);
        if (url.pathname !== "/" && url.pathname === window.location.pathname && url.search === window.location.search) {
            link.setAttribute("aria-current", "page");
        }
    });
    let mode;
    let scheduled = false;
    let scrollState = null;
    const root = document.documentElement;

    function unlockScroll() {
        if (!scrollState) return;
        root.style.overflow = scrollState.overflow;
        document.body.style.paddingRight = scrollState.paddingRight;
        scrollState = null;
    }
    function resetGroups(drawer) {
        groups.forEach(({ details, summary, panel, button }) => {
            summary.hidden = drawer;
            button.hidden = !drawer;
            details.open = drawer;
            panel.hidden = drawer;
            button.setAttribute("aria-expanded", "false");
        });
    }
    function closeDrawer(restoreFocus = true) {
        if (!dialog.open) return;
        dialog.close();
        toggle.setAttribute("aria-expanded", "false");
        unlockScroll();
        resetGroups(true);
        if (restoreFocus) toggle.focus({ preventScroll: true });
    }
    function openDrawer() {
        if (mode !== "drawer" || dialog.open) return;
        const scrollbar = window.innerWidth - root.clientWidth;
        scrollState = { overflow: root.style.overflow, paddingRight: document.body.style.paddingRight };
        const padding = parseFloat(getComputedStyle(document.body).paddingRight) || 0;
        root.style.overflow = "hidden";
        document.body.style.paddingRight = `${padding + scrollbar}px`;
        dialog.showModal();
        toggle.setAttribute("aria-expanded", "true");
        drawerBody.scrollTop = 0;
        closeButton.focus({ preventScroll: true });
    }
    function horizontalWidth() {
        // Clone only for synchronous measurement, then remove it before painting.
        // Inert + aria-hidden + no IDs/names prevent a second accessible navigation.
        const measure = document.createElement("div");
        measure.className = "site-header site-header--visitor nav-measure";
        measure.inert = true;
        measure.setAttribute("aria-hidden", "true");
        measure.append(brand.cloneNode(true), content.cloneNode(true));
        measure.querySelectorAll(".nav-accordion").forEach((el) => el.remove());
        measure.querySelectorAll("[id], [name]").forEach((el) => { el.removeAttribute("id"); el.removeAttribute("name"); });
        measure.querySelectorAll("[hidden]").forEach((el) => { el.hidden = false; });
        measure.querySelectorAll("details").forEach((el) => { el.open = false; });
        document.body.append(measure);
        const width = Math.ceil(measure.getBoundingClientRect().width);
        measure.remove();
        return width;
    }
    function syncLayout() {
        scheduled = false;
        const minimum = horizontalWidth();
        // Compare to the actual header box (excludes scrollbar, includes gutters).
        const next = header.getBoundingClientRect().width >= minimum ? "horizontal" : "drawer";
        header.dataset.navMinimum = String(minimum);
        if (next === mode) return;
        const focused = document.activeElement;
        const hadFocus = content.contains(focused) || dialog.contains(focused) || focused === toggle;
        closeDrawer(false);
        mode = next;
        header.dataset.navMode = next;
        resetGroups(next === "drawer");
        if (next === "drawer") drawerBody.append(content);
        else header.insertBefore(content, dialog);
        toggle.hidden = next !== "drawer";
        if (hadFocus) {
            if (next === "drawer") toggle.focus({ preventScroll: true });
            else if (content.contains(focused) && focused.getClientRects().length) focused.focus({ preventScroll: true });
            else brand.focus({ preventScroll: true });
        }
    }
    function scheduleLayout() {
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(syncLayout);
    }
    toggle.addEventListener("click", openDrawer);
    closeButton.addEventListener("click", () => closeDrawer());
    dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDrawer(); });
    dialog.addEventListener("close", () => {
        if (!dialog.open) { unlockScroll(); toggle.setAttribute("aria-expanded", "false"); }
    });
    let backdropStart = false;
    const outside = (event) => {
        const rect = dialog.getBoundingClientRect();
        return event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
    };
    dialog.addEventListener("pointerdown", (event) => { backdropStart = event.target === dialog && outside(event); });
    dialog.addEventListener("click", (event) => {
        if (backdropStart && event.target === dialog && outside(event)) closeDrawer();
        backdropStart = false;
        if (event.target.closest("a[href]")) closeDrawer();
    });
    dialog.addEventListener("keydown", (event) => {
        if (event.key !== "Tab") return;
        const items = [...dialog.querySelectorAll("a[href], button:not(:disabled), summary, [tabindex='0']")]
            .filter((el) => el.getClientRects().length && getComputedStyle(el).visibility !== "hidden");
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    // Keep native desktop details, outside-click dismissal and Escape behavior.
    header.addEventListener("keydown", (event) => {
        if (mode !== "horizontal" || event.key !== "Escape") return;
        groups.forEach(({ details, summary }) => { if (details.open) { details.open = false; summary.focus(); } });
    });
    document.addEventListener("click", (event) => {
        if (mode !== "horizontal") return;
        groups.forEach(({ details }) => { if (!details.contains(event.target)) details.open = false; });
    });
    header.setAttribute("data-nav-ready", "");
    syncLayout();
    window.addEventListener("resize", scheduleLayout, { passive: true });
    if (typeof ResizeObserver === "function") new ResizeObserver(scheduleLayout).observe(header);
    if (typeof MutationObserver === "function") new MutationObserver(scheduleLayout).observe(content, { childList: true, subtree: true, characterData: true });
    if (document.fonts) {
        document.fonts.ready.then(scheduleLayout);
        document.fonts.addEventListener("loadingdone", scheduleLayout);
    }
})();
