document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector(".menu-toggle");

    if (menuToggle) {
        menuToggle.addEventListener("click", () => {
            const isOpen = document.body.classList.toggle("menu-open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
            menuToggle.setAttribute("aria-label", isOpen ? "Cerrar menu" : "Abrir menu");
        });
    }

    const navDropdowns = document.querySelectorAll(".nav-dropdown");

    navDropdowns.forEach((dropdown) => {
        const summary = dropdown.querySelector("summary");

        dropdown.addEventListener("keydown", (event) => {
            if (event.key !== "Escape" || !dropdown.open) {
                return;
            }

            dropdown.open = false;
            summary?.focus();
        });
    });

    document.addEventListener("click", (event) => {
        navDropdowns.forEach((dropdown) => {
            if (!dropdown.contains(event.target)) {
                dropdown.open = false;
            }
        });
    });

    const segmentButtons = document.querySelectorAll(".segment-btn");

    segmentButtons.forEach((button) => {
        button.addEventListener("click", () => {
            segmentButtons.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
        });
    });

    const saveButtons = document.querySelectorAll(".save-btn");

    saveButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.toggle("is-active");
            button.textContent = button.classList.contains("is-active") ? "♥" : "♡";
        });
    });

    const evidenceToggles = document.querySelectorAll("[data-evidence-toggle]");

    evidenceToggles.forEach((toggle) => {
        const target = document.querySelector(`[data-evidence-detail="${toggle.dataset.evidenceToggle}"]`);

        if (!target) {
            return;
        }

        const syncEvidenceDetail = () => {
            target.hidden = !toggle.checked;
        };

        syncEvidenceDetail();
        toggle.addEventListener("change", syncEvidenceDetail);
    });

    const smartFilters = document.querySelector(".smart-filters");

    if (smartFilters) {
        const updateFiltersState = () => {
            smartFilters.classList.toggle("is-stuck", window.scrollY > 110);
        };

        updateFiltersState();
        window.addEventListener("scroll", updateFiltersState, { passive: true });
    }

    const servicioSelect = document.getElementById("servicio");
    const nuevoRubroBox = document.getElementById("nuevo-rubro-box");

    if (servicioSelect && nuevoRubroBox) {
        nuevoRubroBox.style.display = "none";

        servicioSelect.addEventListener("change", () => {
            nuevoRubroBox.style.display = servicioSelect.value === "otro" ? "flex" : "none";
        });
    }
});
