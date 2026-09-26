document.addEventListener("DOMContentLoaded", () => {
    const hero = document.querySelector(".market-guide__hero");
    const carousel = hero?.querySelector("[data-market-carousel]");
    const toggle = hero?.querySelector("[data-market-carousel-toggle]");
    if (!carousel || !toggle) return;

    const slides = Array.from(carousel.querySelectorAll(".market-guide__visual-slide"));
    if (slides.length < 2) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let current = 0;
    let timer = null;
    let pausedByUser = false;
    let pausedByInteraction = false;

    const loadImages = (slide) => Promise.all(
        Array.from(slide.querySelectorAll("img"), (image) => {
            if (image.dataset.src) {
                image.src = image.dataset.src;
                delete image.dataset.src;
            }
            if (image.complete && image.naturalWidth > 0) return Promise.resolve(true);
            return new Promise((resolve) => {
                image.addEventListener("load", () => resolve(true), { once: true });
                image.addEventListener("error", () => resolve(false), { once: true });
            });
        })
    ).then((results) => results.every(Boolean));

    const canAdvance = () => (
        !reducedMotion.matches
        && !pausedByUser
        && !pausedByInteraction
        && !document.hidden
    );

    const schedule = () => {
        if (timer !== null) window.clearTimeout(timer);
        timer = null;
        if (canAdvance()) timer = window.setTimeout(advance, 3000);
    };

    const preloadNext = () => {
        void loadImages(slides[(current + 1) % slides.length]);
    };

    const advance = async () => {
        timer = null;
        if (!canAdvance()) return;
        const next = (current + 1) % slides.length;
        if (!(await loadImages(slides[next])) || !canAdvance()) {
            schedule();
            return;
        }
        const previous = slides[current];
        slides[next].classList.add("is-active");
        previous.classList.add("is-leaving");
        previous.classList.remove("is-active");
        window.setTimeout(() => previous.classList.remove("is-leaving"), 650);
        current = next;
        preloadNext();
        schedule();
    };

    const updateToggle = () => {
        toggle.setAttribute("aria-pressed", String(pausedByUser));
        toggle.textContent = pausedByUser ? "Reanudar imágenes" : "Pausar imágenes";
    };

    toggle.addEventListener("click", () => {
        pausedByUser = !pausedByUser;
        updateToggle();
        schedule();
    });
    hero.addEventListener("pointerenter", (event) => {
        if (event.pointerType === "mouse") {
            pausedByInteraction = true;
            schedule();
        }
    });
    hero.addEventListener("pointerleave", (event) => {
        if (event.pointerType === "mouse") {
            pausedByInteraction = false;
            schedule();
        }
    });
    hero.addEventListener("focusin", () => {
        pausedByInteraction = true;
        schedule();
    });
    hero.addEventListener("focusout", (event) => {
        pausedByInteraction = hero.contains(event.relatedTarget);
        schedule();
    });
    document.addEventListener("visibilitychange", schedule);
    reducedMotion.addEventListener("change", schedule);

    toggle.hidden = false;
    updateToggle();
    preloadNext();
    schedule();
});
