(() => {
    const faq = document.querySelector("[data-home-faq]");
    if (!faq) return;

    const search = faq.querySelector("[data-home-faq-search]");
    const items = Array.from(faq.querySelectorAll("[data-home-faq-item]"));
    const empty = faq.querySelector("[data-home-faq-empty]");
    const status = faq.querySelector("[data-home-faq-status]");
    const normalize = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es").trim();

    search.addEventListener("input", () => {
        const query = normalize(search.value);
        let visible = 0;
        for (const item of items) {
            item.hidden = !normalize(item.textContent).includes(query);
            if (!item.hidden) visible += 1;
        }
        empty.hidden = visible !== 0;
        status.textContent = query ? `${visible} ${visible === 1 ? "respuesta disponible" : "respuestas disponibles"}.` : "";
    });
})();
