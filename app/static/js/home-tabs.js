document.addEventListener("DOMContentLoaded", () => {
    const tablist = document.querySelector("[role='tablist'][aria-label='Elegir una operacion']");

    if (!tablist) {
        return;
    }

    const tabs = Array.from(tablist.querySelectorAll("[role='tab']"));
    const panels = tabs
        .map((tab) => document.getElementById(tab.getAttribute("aria-controls")))
        .filter(Boolean);

    const activateTab = (nextTab, moveFocus = true) => {
        tabs.forEach((tab) => {
            const isActive = tab === nextTab;
            tab.classList.toggle("is-active", isActive);
            tab.setAttribute("aria-selected", String(isActive));
            tab.tabIndex = isActive ? 0 : -1;
        });

        panels.forEach((panel) => {
            panel.hidden = panel.id !== nextTab.getAttribute("aria-controls");
        });

        if (moveFocus) {
            nextTab.focus();
        }
    };

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => activateTab(tab, false));
    });

    tablist.addEventListener("keydown", (event) => {
        const currentIndex = tabs.indexOf(document.activeElement);

        if (currentIndex === -1) {
            return;
        }

        let nextIndex = currentIndex;

        if (event.key === "ArrowRight") {
            nextIndex = (currentIndex + 1) % tabs.length;
        } else if (event.key === "ArrowLeft") {
            nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        } else if (event.key === "Home") {
            nextIndex = 0;
        } else if (event.key === "End") {
            nextIndex = tabs.length - 1;
        } else {
            return;
        }

        event.preventDefault();
        activateTab(tabs[nextIndex]);
    });
});
