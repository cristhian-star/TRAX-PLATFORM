const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../../app/static/js/home-faq.js"), "utf8");
const entries = [
    "¿Cómo encuentro y contacto a un profesional? Buscá por servicio y zona.",
    "¿Puedo pedir y comparar presupuestos? Revisá las propuestas recibidas.",
    "¿Cómo verifica MANDOBRA a los profesionales? Revisá su reputación.",
    "¿Cómo funcionan los pagos dentro de la plataforma? Abrir un QR no confirma el pago.",
    "¿Qué hago si surge un problema con el trabajo? Consultá el seguimiento.",
    "¿Cómo puedo registrarme como profesional? Creá una cuenta.",
].map((textContent) => ({ textContent, hidden: false }));
const search = { value: "", addEventListener(type, listener) {
    assert.equal(type, "input");
    this.input = listener;
} };
const empty = { hidden: true };
const status = { textContent: "" };
const faq = {
    querySelector(selector) {
        return ({ "[data-home-faq-search]": search, "[data-home-faq-empty]": empty,
            "[data-home-faq-status]": status })[selector];
    },
    querySelectorAll(selector) {
        assert.equal(selector, "[data-home-faq-item]");
        return entries;
    },
};
const document = { querySelector(selector) {
    assert.equal(selector, "[data-home-faq]");
    return faq;
} };
vm.runInNewContext(source, { document });

function input(value) {
    search.value = value;
    search.input();
    return entries.filter((entry) => !entry.hidden).length;
}
assert.equal(input("  PROFESIONALES  "), 1);
assert.equal(entries[2].hidden, false);
assert.equal(status.textContent, "1 respuesta disponible.");
assert.equal(input("reputacion"), 1); // Matches answer with accent.
assert.equal(input("PRESUPUESTOS"), 1);
assert.equal(input("sin coincidencia"), 0);
assert.equal(empty.hidden, false);
assert.equal(status.textContent, "0 respuestas disponibles.");
assert.equal(input("   "), 6);
assert.equal(empty.hidden, true);
assert.equal(status.textContent, "");
assert.equal(entries.every((entry) => !entry.hidden), true);
assert.equal(/fetch\s*\(|XMLHttpRequest|sendBeacon|localStorage|sessionStorage|history\.|location\./.test(source), false);
console.log("home FAQ local filter OK");
