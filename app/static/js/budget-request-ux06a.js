(function () {
    "use strict";
    function init(doc, win) {
        const errors = doc.querySelector("[data-budget-errors]");
        if (errors) errors.focus();
        const form = doc.querySelector("[data-budget-form]");
        if (!form || form.dataset.ready) return;
        const fields = form.querySelector("[data-budget-fields]");
        const review = form.querySelector("[data-budget-review]");
        const submit = form.querySelector("[data-budget-submit]");
        const edit = form.querySelector("[data-budget-edit]");
        if (!fields || !review || !submit || !edit) return;
        form.dataset.ready = "true";
        let reviewing = false, sending = false;
        submit.textContent = "Revisar solicitud";
        function resetSending() {
            sending = false;
            submit.disabled = false;
            submit.textContent = reviewing ? "Publicar solicitud" : "Revisar solicitud";
        }
        edit.addEventListener("click", () => {
            if (sending) return;
            reviewing = false;
            fields.hidden = false;
            review.hidden = true;
            submit.textContent = "Revisar solicitud";
            form.elements.namedItem("titulo").focus();
        });
        form.addEventListener("submit", event => {
            if (sending) { event.preventDefault(); return; }
            if (!form.checkValidity()) {
                event.preventDefault();
                fields.hidden = false;
                review.hidden = true;
                reviewing = false;
                submit.textContent = "Revisar solicitud";
                form.reportValidity();
                return;
            }
            if (!reviewing) {
                event.preventDefault();
                review.querySelectorAll("[data-budget-value]").forEach(target => {
                    const name = target.dataset.budgetValue;
                    const control = form.elements.namedItem(name);
                    let value = control.value.trim();
                    if (name === "urgencia") value = { BAJA: "Baja", NORMAL: "Normal", ALTA: "Alta" }[value] || value;
                    if (name === "fecha_estimada") value = value ? value.split("-").reverse().join("/") : "A coordinar";
                    target.textContent = value;
                });
                fields.hidden = true;
                review.hidden = false;
                reviewing = true;
                submit.textContent = "Publicar solicitud";
                review.querySelector("h2").focus();
                return;
            }
            sending = true;
            // Keep the native submit and CSRF; never issue a second request via fetch.
            win.queueMicrotask(() => {
                if (event.defaultPrevented) { resetSending(); return; }
                submit.disabled = true;
                submit.textContent = "Publicando…";
            });
        });
        win.addEventListener("pageshow", resetSending);
    }
    if (typeof module !== "undefined" && module.exports) module.exports = { init };
    if (typeof document !== "undefined") init(document, window);
}());
