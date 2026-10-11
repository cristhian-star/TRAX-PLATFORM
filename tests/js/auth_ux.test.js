const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('app/static/js/auth-ux-v1.js', 'utf8');
const themeSource = fs.readFileSync('app/static/js/theme-switch-v1.js', 'utf8');
function setup(expanded = false, storage = new Map()) {
    const handlers = {}, lifecycle = {};
    let focused = false;
    const email = { value: '', valid: false, reportValidity() { return this.valid; } };
    const password = { value: '', required: true, focus() { focused = true; } };
    const panel = { hidden: false }, label = {}, classes = new Set();
    const button = { disabled: false, classList: { add: v => classes.add(v), remove: v => classes.delete(v) } };
    const nodes = { '[data-auth-submit]': button, '[name="email"]': email, '[data-login-password]': panel, '[name="password"]': password, '[data-submit-label]': label };
    const form = { dataset: { expanded: String(expanded) }, hasAttribute: () => true, querySelector: s => nodes[s], addEventListener: (e, cb) => handlers[e] = cb, reportValidity: () => email.valid && Boolean(password.value) };
    const themeClasses = new Set(), themeHandlers = {}, attrs = {}, themeLabel = {};
    const themeButton = { hidden: true, setAttribute: (k, v) => attrs[k] = v,
        querySelector: s => s === '.theme-switch__label' ? themeLabel : null,
        addEventListener: (e, cb) => themeHandlers[e] = cb };
    const context = vm.createContext({ document: {
        documentElement: { classList: { add: v => themeClasses.add(v), remove: (...vs) => vs.forEach(v => themeClasses.delete(v)), contains: v => themeClasses.has(v) } },
        addEventListener() {}, querySelector: s => s === '[data-theme-switch]' ? themeButton : null,
        querySelectorAll: s => s === '[data-auth-form]' ? [form] : [] },
        localStorage: { getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v) },
        window: { addEventListener: (e, cb) => lifecycle[e] = cb } });
    // Actual AUTH script runs before the deferred, unchanged platform controller.
    vm.runInContext(source, context);
    vm.runInContext(themeSource, context);
    function submit() { let prevented = false; handlers.submit({ preventDefault() { prevented = true; } }); return prevented; }
    return { email, password, panel, label, button, submit, lifecycle, focused: () => focused,
        themeButton, attrs, themeLabel, themeClasses, storage, toggle: () => themeHandlers.click() };
}
const ui = setup();
assert.equal(ui.panel.hidden, true);
assert.equal(ui.label.textContent, 'Continuar');
assert.equal(ui.submit(), true);
assert.equal(ui.panel.hidden, true);
ui.email.valid = true;
assert.equal(ui.submit(), true);
assert.equal(ui.panel.hidden, false);
assert.equal(ui.focused(), true);
assert.equal(ui.label.textContent, 'Ingresar');
assert.equal(ui.password.required, true);
ui.password.value = 'synthetic';
assert.equal(ui.submit(), false);
assert.equal(ui.button.disabled, true);
ui.lifecycle.pageshow();
assert.equal(ui.button.disabled, false);
assert.equal(setup(true).panel.hidden, false);
const themed = setup();
assert.equal(themed.themeButton.hidden, false);
assert.equal(themed.attrs['aria-pressed'], 'false');
themed.email.value = 'synthetic@trax.test';
themed.email.valid = true;
themed.submit();
themed.password.value = 'synthetic';
themed.toggle();
assert.equal(themed.themeClasses.has('theme-dark'), true);
assert.equal(themed.attrs['aria-pressed'], 'true');
assert.equal(themed.attrs['aria-label'], 'Cambiar a tema claro');
assert.equal(themed.themeLabel.textContent, 'Oscuro');
assert.equal(themed.storage.get('trax-theme'), 'dark');
assert.equal(themed.email.value, 'synthetic@trax.test');
assert.equal(themed.password.value, 'synthetic');
assert.equal(themed.panel.hidden, false);
assert.equal(themed.button.disabled, false);
const restored = setup(false, themed.storage);
assert.equal(restored.themeClasses.has('theme-dark'), true);
restored.toggle();
assert.equal(restored.attrs['aria-pressed'], 'false');
assert.equal(restored.themeLabel.textContent, 'Claro');
assert.equal(restored.storage.get('trax-theme'), 'light');
console.log('AUTH theme: real controller, progressive reveal, accessible state, persistence and form preservation OK.');
console.log('AUTH-UX-001: format-only step, focus, submit and pageshow OK (no network API supplied).');
