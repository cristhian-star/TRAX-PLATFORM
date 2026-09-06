document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("[data-whatsapp-contact-form]");

    if (!forms.length) {
        return;
    }

    const dialog = document.querySelector("[data-whatsapp-consent-modal]");
    const checkbox = dialog?.querySelector("[data-whatsapp-consent-checkbox]");
    const confirmButton = dialog?.querySelector("[data-whatsapp-consent-confirm]");
    const cancelButton = dialog?.querySelector("[data-whatsapp-consent-cancel]");
    const supportsDialog = Boolean(dialog && typeof dialog.showModal === "function");
    const fallbackMessage = [
        "Estas por comunicarte directamente con un profesional mediante WhatsApp.",
        "La conversacion se realizara fuera de MANDOBRA.",
        "No compartas datos bancarios sensibles.",
        "",
        "Aceptas continuar?"
    ].join("\n");
    let pendingForm = null;
    let previousFocus = null;

    const setConsent = (form) => {
        const consentInput = form.querySelector("input[name='whatsapp_consent']");
        if (consentInput) {
            consentInput.value = "on";
        }
    };

    const submitAuthorizedRequest = async (form) => {
        if (form.dataset.whatsappSubmitting === "true") {
            return;
        }

        form.dataset.whatsappSubmitting = "true";
        const reservedWindow = window.open("", "_blank", "noopener");

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const payload = await response.json().catch(() => ({}));

            if (!response.ok || !payload.whatsapp_url) {
                if (reservedWindow) {
                    reservedWindow.close();
                }
                throw new Error(payload.error || "No se pudo iniciar WhatsApp desde MANDOBRA.");
            }

            if (reservedWindow) {
                reservedWindow.location = payload.whatsapp_url;
            } else {
                window.location.assign(payload.whatsapp_url);
            }
        } catch (error) {
            form.dataset.whatsappConsentConfirmed = "false";
            window.alert(error.message || "No se pudo iniciar WhatsApp desde MANDOBRA.");
        } finally {
            form.dataset.whatsappSubmitting = "false";
        }
    };

    const confirmAndSubmit = (form) => {
        setConsent(form);
        form.dataset.whatsappConsentConfirmed = "true";
        submitAuthorizedRequest(form);
    };

    const openFallbackConsent = (form) => {
        if (window.confirm(fallbackMessage)) {
            confirmAndSubmit(form);
        }
    };

    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();

            if (form.dataset.whatsappConsentConfirmed === "true") {
                submitAuthorizedRequest(form);
                return;
            }

            if (!supportsDialog || !checkbox || !confirmButton || !cancelButton) {
                openFallbackConsent(form);
                return;
            }

            pendingForm = form;
            previousFocus = document.activeElement;
            checkbox.checked = false;
            confirmButton.disabled = true;
            dialog.showModal();
            checkbox.focus();
        });
    });

    if (!supportsDialog || !checkbox || !confirmButton || !cancelButton) {
        return;
    }

    checkbox.addEventListener("change", () => {
        confirmButton.disabled = !checkbox.checked;
    });

    cancelButton.addEventListener("click", () => {
        pendingForm = null;
        dialog.close();
        previousFocus?.focus();
    });

    confirmButton.addEventListener("click", () => {
        if (!pendingForm || !checkbox.checked) {
            return;
        }

        const form = pendingForm;
        pendingForm = null;
        dialog.close();
        previousFocus?.focus();
        confirmAndSubmit(form);
    });
});
