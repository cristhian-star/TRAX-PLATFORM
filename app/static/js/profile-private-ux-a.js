document.addEventListener("DOMContentLoaded", () => {
    const root = document.querySelector("[data-private-profile]");

    if (!root) {
        return;
    }

    const triggers = root.querySelectorAll("[data-profile-panel-trigger]");
    const panels = root.querySelectorAll("[data-profile-panel]");

    const activatePanel = (panelName) => {
        triggers.forEach((trigger) => {
            trigger.classList.toggle(
                "is-active",
                trigger.dataset.profilePanelTrigger === panelName
            );
        });

        panels.forEach((panel) => {
            panel.classList.toggle(
                "is-active",
                panel.dataset.profilePanel === panelName
            );
        });
    };

    triggers.forEach((trigger) => {
        trigger.addEventListener("click", () => {
            activatePanel(trigger.dataset.profilePanelTrigger);
        });
    });

    const shareButton = root.querySelector("[data-share-private-profile]");
    const shareStatus = root.querySelector("[data-share-private-status]");
    const publicProfileLink = root.querySelector(".private-profile__actions a");

    const setShareStatus = (message) => {
        if (shareStatus) {
            shareStatus.textContent = message;
        }
    };

    if (shareButton) {
        shareButton.addEventListener("click", async () => {
            const profileUrl = publicProfileLink?.href || window.location.href;
            const shareData = {
                title: document.title,
                text: root.querySelector("h1")?.textContent.trim(),
                url: profileUrl,
            };

            try {
                if (navigator.share) {
                    await navigator.share(shareData);
                    setShareStatus("Perfil compartido.");
                    return;
                }

                await navigator.clipboard.writeText(profileUrl);
                setShareStatus("Enlace copiado.");
            } catch (error) {
                if (error.name !== "AbortError") {
                    setShareStatus("No se pudo compartir el perfil.");
                }
            }
        });
    }
});
