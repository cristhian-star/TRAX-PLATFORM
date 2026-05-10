document.addEventListener("DOMContentLoaded", () => {
    const segmentButtons = document.querySelectorAll(".segment-btn");

    segmentButtons.forEach((button) => {
        button.addEventListener("click", () => {
            segmentButtons.forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");
        });
    });

    const favoriteButtons = document.querySelectorAll(".favorite-btn");

    favoriteButtons.forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.toggle("is-active");
            button.textContent = button.classList.contains("is-active") ? "♥" : "♡";
        });
    });

    const filtersBar = document.querySelector(".filters-bar");

    if (filtersBar) {
        const updateFilterShadow = () => {
            filtersBar.classList.toggle("is-stuck", window.scrollY > 110);
        };

        updateFilterShadow();
        window.addEventListener("scroll", updateFilterShadow, { passive: true });
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
