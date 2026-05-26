document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector(".menu-toggle");

    if (menuToggle) {
        menuToggle.addEventListener("click", () => {
            const isOpen = document.body.classList.toggle("menu-open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
        });
    }

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
