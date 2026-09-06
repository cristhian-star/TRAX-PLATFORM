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

    const coverageMap = root.querySelector("[data-coverage-map]");
    const radiusSelect = root.querySelector("[data-coverage-radius]");
    const radiusCustom = root.querySelector("[data-coverage-radius-custom]");

    const normalizeRadius = () => {
        if (!radiusSelect) {
            return 10;
        }

        const rawValue = radiusSelect.value === "PERSONALIZADO"
            ? radiusCustom?.value
            : radiusSelect.value;
        const radius = Number.parseInt(rawValue, 10);

        if (Number.isNaN(radius) || radius < 0) {
            return 10;
        }

        return Math.min(radius, 200);
    };

    const updateCoveragePreview = () => {
        if (!coverageMap) {
            return;
        }

        const radius = normalizeRadius();
        const scale = Math.min(Math.max(radius / 200, 0.08), 1);
        coverageMap.style.setProperty("--coverage-scale", scale.toString());

        if (radiusCustom && radiusSelect) {
            radiusCustom.disabled = radiusSelect.value !== "PERSONALIZADO";
        }
    };

    radiusSelect?.addEventListener("change", updateCoveragePreview);
    radiusCustom?.addEventListener("input", updateCoveragePreview);
    updateCoveragePreview();
});
