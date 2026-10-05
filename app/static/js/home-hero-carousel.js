document.addEventListener("DOMContentLoaded", () => {
    const hero = document.querySelector(".trax-home__hero");
    const carousel = hero?.querySelector("[data-hero-carousel]");
    const controls = hero?.querySelector("[data-hero-controls]");
    if (!carousel || !controls) return;

    const slides = Array.from(carousel.querySelectorAll(".trax-home__slide"));
    if (slides.length < 2) return;

    const previous = controls.querySelector("[data-hero-previous]");
    const next = controls.querySelector("[data-hero-next]");
    const status = controls.querySelector("[data-hero-status]");
    const messageContent = hero.querySelector("[data-hero-message-content]");
    const title = messageContent?.querySelector("h1");
    const subtitle = messageContent?.querySelector(".trax-home__lead");
    if (!title || !subtitle) return;
    const messages = [
        { title: title.textContent.trim(), subtitle: subtitle.textContent.trim() },
        ...Array.from(hero.querySelectorAll("[data-hero-message]"), (element) => ({
            title: element.querySelector(".trax-home__message-title").textContent.trim(),
            subtitle: element.querySelector(".trax-home__lead").textContent.trim(),
        })),
    ];
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let current = 0;
    let messageIndex = 0;
    let imageTimer = null;
    let messageTimer = null;
    let messageFadeTimer = null;
    let hovered = false;
    let focused = false;
    let touching = false;
    let advanceId = 0;

    const canAdvance = () => !reducedMotion.matches && !hovered && !focused && !touching && !document.hidden;

    const scheduleImages = () => {
        if (imageTimer !== null) window.clearTimeout(imageTimer);
        imageTimer = null;
        if (canAdvance()) imageTimer = window.setTimeout(() => void advance(1, false), 5000);
    };

    const scheduleMessages = () => {
        if (messageTimer !== null) window.clearTimeout(messageTimer);
        if (messageFadeTimer !== null) window.clearTimeout(messageFadeTimer);
        messageTimer = null;
        messageFadeTimer = null;
        messageContent.classList.remove("is-fading");
        if (canAdvance()) messageTimer = window.setTimeout(advanceMessage, 10000);
    };

    const scheduleBoth = () => {
        scheduleImages();
        scheduleMessages();
    };

    const advanceMessage = () => {
        messageTimer = null;
        if (!canAdvance()) return;
        messageContent.classList.add("is-fading");
        messageFadeTimer = window.setTimeout(() => {
            messageFadeTimer = null;
            if (!canAdvance()) return;
            messageIndex = (messageIndex + 1) % messages.length;
            title.textContent = messages[messageIndex].title;
            subtitle.textContent = messages[messageIndex].subtitle;
            messageContent.classList.remove("is-fading");
            scheduleMessages();
        }, 180);
    };

    const load = (slide) => {
        if (slide.dataset.heroFailed) return Promise.resolve(false);
        if (slide.complete && slide.naturalWidth > 0) return Promise.resolve(true);
        return new Promise((resolve) => {
            slide.onload = () => resolve(true);
            slide.onerror = () => {
                slide.dataset.heroFailed = "true";
                resolve(false);
            };
            if (slide.dataset.src) {
                slide.src = slide.dataset.src;
                delete slide.dataset.src;
            }
        });
    };

    const preloadNext = () => {
        const candidate = slides[(current + 1) % slides.length];
        void load(candidate);
    };

    const advance = async (direction, manual) => {
        if (imageTimer !== null) window.clearTimeout(imageTimer);
        imageTimer = null;
        const requestId = ++advanceId;
        for (let offset = 1; offset < slides.length; offset += 1) {
            const index = (current + direction * offset + slides.length * offset) % slides.length;
            if (!(await load(slides[index]))) continue;
            if (requestId !== advanceId) return;
            if (!manual && !canAdvance()) return;
            slides[current].classList.remove("is-active");
            slides[index].classList.add("is-active");
            current = index;
            if (manual) status.textContent = `Imagen ${current + 1} de ${slides.length}`;
            preloadNext();
            scheduleImages();
            return;
        }
        scheduleImages();
    };

    previous.addEventListener("click", () => void advance(-1, true));
    next.addEventListener("click", () => void advance(1, true));
    hero.addEventListener("pointerenter", (event) => {
        if (event.pointerType === "mouse") { hovered = true; scheduleBoth(); }
    });
    hero.addEventListener("pointerleave", (event) => {
        if (event.pointerType === "mouse") { hovered = false; scheduleBoth(); }
    });
    hero.addEventListener("touchstart", () => { touching = true; scheduleBoth(); }, { passive: true });
    hero.addEventListener("touchend", () => { touching = false; scheduleBoth(); });
    hero.addEventListener("touchcancel", () => { touching = false; scheduleBoth(); });
    hero.addEventListener("focusin", () => { focused = true; scheduleBoth(); });
    hero.addEventListener("focusout", (event) => {
        focused = hero.contains(event.relatedTarget);
        scheduleBoth();
    });
    document.addEventListener("visibilitychange", scheduleBoth);
    reducedMotion.addEventListener("change", scheduleBoth);

    controls.hidden = false;
    scheduleBoth();
    preloadNext();
});
