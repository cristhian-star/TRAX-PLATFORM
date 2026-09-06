document.addEventListener("DOMContentLoaded", () => {
    const shareButton = document.querySelector("[data-share-profile]");
    const shareStatus = document.querySelector("[data-share-status]");

    if (!shareButton) {
        return;
    }

    const setStatus = (message) => {
        if (shareStatus) {
            shareStatus.textContent = message;
        }
    };

    shareButton.addEventListener("click", async () => {
        const shareData = {
            title: document.title,
            text: document.querySelector(".professional-profile__headline h1")?.textContent.trim(),
            url: window.location.href,
        };

        try {
            if (navigator.share) {
                await navigator.share(shareData);
                setStatus("Perfil compartido.");
                return;
            }

            await navigator.clipboard.writeText(window.location.href);
            setStatus("Enlace copiado.");
        } catch (error) {
            if (error.name !== "AbortError") {
                setStatus("No se pudo compartir el perfil.");
            }
        }
    });
});
