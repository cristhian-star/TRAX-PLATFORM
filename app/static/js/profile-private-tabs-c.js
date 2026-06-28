document.addEventListener("DOMContentLoaded", () => {
    const root = document.querySelector("[data-private-tabs-profile]");

    if (!root) {
        return;
    }

    const triggers = root.querySelectorAll("[data-private-tab-trigger]");
    const panels = root.querySelectorAll("[data-private-tab-panel]");

    const activateTab = (tabName) => {
        triggers.forEach((trigger) => {
            trigger.classList.toggle(
                "is-active",
                trigger.dataset.privateTabTrigger === tabName
            );
        });

        panels.forEach((panel) => {
            panel.classList.toggle(
                "is-active",
                panel.dataset.privateTabPanel === tabName
            );
        });
    };

    triggers.forEach((trigger) => {
        trigger.addEventListener("click", () => {
            activateTab(trigger.dataset.privateTabTrigger);
        });
    });
});
