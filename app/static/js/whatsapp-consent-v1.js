document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("[data-whatsapp-contact-form]");

    if (!forms.length || typeof HTMLDialogElement === "undefined") {
        return;
    }

    const dialog = document.querySelector("[data-whatsapp-consent-modal]");
    const checkbox = dialog?.querySelector("[data-whatsapp-consent-checkbox]");
    const confirmButton = dialog?.querySelector("[data-whatsapp-consent-confirm]");
    const cancelButton = dialog?.querySelector("[data-whatsapp-consent-cancel]");
    let pendingForm = null;

    if (!dialog || !checkbox || !confirmButton || !cancelButton) {
        return;
    }

    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (form.dataset.whatsappConsentConfirmed === "true") {
                return;
            }

            event.preventDefault();
            pendingForm = form;
            checkbox.checked = false;
            confirmButton.disabled = true;
            dialog.showModal();
        });
    });

    checkbox.addEventListener("change", () => {
        confirmButton.disabled = !checkbox.checked;
    });

    cancelButton.addEventListener("click", () => {
        pendingForm = null;
        dialog.close();
    });

    confirmButton.addEventListener("click", () => {
        if (!pendingForm || !checkbox.checked) {
            return;
        }

        const consentInput = pendingForm.querySelector("input[name='whatsapp_consent']");
        if (consentInput) {
            consentInput.value = "on";
        }

        pendingForm.dataset.whatsappConsentConfirmed = "true";
        dialog.close();
        pendingForm.submit();
    });
});
