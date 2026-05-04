document.addEventListener("DOMContentLoaded", () => {
    const segmentButtons = document.querySelectorAll(".segment-btn");

    segmentButtons.forEach((button) => {
        button.addEventListener("click", () => {
            segmentButtons.forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");
        });
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const servicioSelect = document.getElementById("servicio");
    const nuevoRubroBox = document.getElementById("nuevo-rubro-box");

    if (servicioSelect && nuevoRubroBox) {
        nuevoRubroBox.style.display = "none";

        servicioSelect.addEventListener("change", () => {
            if (servicioSelect.value === "otro") {
                nuevoRubroBox.style.display = "flex";
            } else {
                nuevoRubroBox.style.display = "none";
            }
        });
    }
});