const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../../app/static/js/home-hero-carousel.js"), "utf8");
const events = () => {
    const handlers = {};
    return {
        handlers,
        addEventListener(name, callback) { handlers[name] = callback; },
    };
};
const classes = (...initial) => {
    const values = new Set(initial);
    return {
        add(name) { values.add(name); },
        remove(name) { values.delete(name); },
        contains(name) { return values.has(name); },
    };
};

const previous = events();
const next = events();
const status = { textContent: "" };
const title = { textContent: "El trabajo correcto empieza con una conexión confiable." };
const subtitle = { textContent: "Encontrá profesionales, compará presupuestos, resolvé una urgencia o accedé a nuevas oportunidades desde un solo lugar." };
const messageContent = {
    classList: classes(),
    querySelector(selector) { return selector === "h1" ? title : subtitle; },
};
const variants = [
    ["Tu oficio merece más oportunidades.", "Mostrá tu experiencia, recibí nuevas solicitudes y organizá cada trabajo desde MANDOBRA."],
    ["Formá parte de nuestra comunidad técnica.", "Clientes, profesionales y empresas conectados para resolver necesidades, crear oportunidades y hacer crecer cada oficio."],
].map(([heading, lead]) => ({
    querySelector(selector) { return { textContent: selector === ".trax-home__message-title" ? heading : lead }; },
}));
const slides = Array.from({ length: 8 }, (_, index) => ({
    classList: classes(...(index === 0 ? ["is-active"] : [])),
    complete: true,
    naturalWidth: 1600,
    dataset: {},
}));
const controls = {
    hidden: true,
    querySelector(selector) {
        return ({ "[data-hero-previous]": previous, "[data-hero-next]": next,
            "[data-hero-status]": status })[selector];
    },
};
const hero = {
    ...events(),
    contains() { return false; },
    querySelector(selector) {
        return ({ "[data-hero-carousel]": carousel, "[data-hero-controls]": controls,
            "[data-hero-message-content]": messageContent })[selector];
    },
    querySelectorAll() { return variants; },
};
const carousel = { querySelectorAll() { return slides; } };
const document = {
    ...events(),
    hidden: false,
    querySelector() { return hero; },
};
const media = { ...events(), matches: false };
let now = 0;
let nextId = 0;
const tasks = new Map();
const window = {
    matchMedia() { return media; },
    setTimeout(callback, delay) {
        const id = ++nextId;
        tasks.set(id, { callback, at: now + delay });
        return id;
    },
    clearTimeout(id) { tasks.delete(id); },
};
async function tick(duration) {
    const until = now + duration;
    while (true) {
        const due = [...tasks.entries()].sort((a, b) => a[1].at - b[1].at)[0];
        if (!due || due[1].at > until) break;
        now = due[1].at;
        tasks.delete(due[0]);
        due[1].callback();
        await Promise.resolve();
        await Promise.resolve();
    }
    now = until;
}
const delays = () => [...tasks.values()].map(task => task.at - now).sort((a, b) => a - b);
const active = () => slides.findIndex(slide => slide.classList.contains("is-active"));

async function main() {
    vm.runInNewContext(source, { document, window, Promise });
    document.handlers.DOMContentLoaded();
    assert.equal(controls.hidden, false);
    assert.deepEqual(delays(), [5000, 10000]);

    await tick(5000);
    assert.equal(active(), 1);
    assert.deepEqual(delays(), [5000, 5000]);
    await tick(1000);
    next.handlers.click();
    await new Promise(setImmediate);
    assert.equal(active(), 2);
    assert.deepEqual(delays(), [4000, 5000]); // Manual image navigation does not reset text.
    previous.handlers.click();
    await new Promise(setImmediate);
    assert.equal(active(), 1);
    next.handlers.click();
    await new Promise(setImmediate);
    assert.equal(active(), 2);

    hero.handlers.pointerenter({ pointerType: "mouse" });
    assert.deepEqual(delays(), []);
    await tick(20000);
    assert.equal(active(), 2);
    assert.equal(title.textContent, "El trabajo correcto empieza con una conexión confiable.");
    hero.handlers.pointerleave({ pointerType: "mouse" });
    assert.deepEqual(delays(), [5000, 10000]);

    hero.handlers.touchstart();
    assert.deepEqual(delays(), []);
    hero.handlers.touchend();
    assert.deepEqual(delays(), [5000, 10000]);
    hero.handlers.focusin();
    assert.deepEqual(delays(), []);
    hero.handlers.focusout({ relatedTarget: null });
    assert.deepEqual(delays(), [5000, 10000]);

    document.hidden = true;
    document.handlers.visibilitychange();
    assert.deepEqual(delays(), []);
    document.hidden = false;
    document.handlers.visibilitychange();
    assert.deepEqual(delays(), [5000, 10000]);

    media.matches = true;
    media.handlers.change();
    assert.deepEqual(delays(), []);
    await tick(20000);
    assert.equal(active(), 2);
    media.matches = false;
    media.handlers.change();
    assert.deepEqual(delays(), [5000, 10000]);
    await tick(10180);
    assert.equal(title.textContent, "Tu oficio merece más oportunidades.");
    assert.equal(subtitle.textContent, "Mostrá tu experiencia, recibí nuevas solicitudes y organizá cada trabajo desde MANDOBRA.");
    assert.deepEqual(delays(), [4820, 10000]);
}

main().then(() => process.stdout.write("home hero timers OK\n"), (error) => {
    process.stderr.write(`${error.stack}\n`);
    process.exitCode = 1;
});
