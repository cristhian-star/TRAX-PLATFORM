'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { init } = require('../../app/static/js/budget-request-ux06a.js');
const loading = require('../../app/static/js/page-loading.js');
function node(extra = {}) {
    const listeners = {}, attrs = {};
    return Object.assign({ dataset: {}, hidden: false, textContent: '',
        addEventListener(n, fn) { (listeners[n] ||= []).push(fn); },
        emit(n, e = {}) { (listeners[n] || []).forEach(fn => fn(e)); },
        focus() { this.focused = true; },
        getAttribute(n) { return attrs[n] ?? null; },
        hasAttribute(n) { return Object.hasOwn(attrs, n); },
        setAttribute(n, v) { attrs[n] = v; },
        removeAttribute(n) { delete attrs[n]; }, closest() { return null; }
    }, extra);
}
function fixture(valid = true) {
    const fields = node(), title = node(), button = node(), edit = node(), error = node();
    const values = Object.fromEntries(Object.entries({ titulo: '<b>Trabajo</b>', categoria: 'Plomería', zona: 'CABA', descripcion: 'Canilla', fecha_estimada: '', urgencia: 'NORMAL' }).map(([name, value]) => [name, node({ value })]));
    const targets = Object.keys(values).map(name => node({ dataset: { budgetValue: name } }));
    const review = node({ hidden: true, querySelectorAll: () => targets, querySelector: () => title });
    const form = node({ checkValidity: () => valid, reportValidity() { this.reported = true; }, elements: { namedItem: name => values[name] }, querySelector: selector => ({ '[data-budget-fields]': fields, '[data-budget-review]': review, '[data-budget-submit]': button, '[data-budget-edit]': edit })[selector] });
    form.setAttribute('method', 'post'); form.setAttribute('action', '/presupuestos/nuevo');
    const status = node(), overlay = node({ hidden: true, querySelector: () => status }), main = node();
    const microtasks = [], timers = new Map(); let id = 0;
    const win = node({ location: new URL('http://localhost/presupuestos/nuevo'), queueMicrotask: fn => microtasks.push(fn), setTimeout(fn, ms) { timers.set(++id, { fn, ms }); return id; }, clearTimeout(i) { timers.delete(i); } });
    const doc = node({ baseURI: win.location.href, querySelector: selector => ({ '[data-budget-form]': form, '[data-budget-errors]': error, '[data-page-loading]': overlay, "main, [role='main']": main })[selector] || null });
    init(doc, win); loading.init(doc, win);
    const f = { fields, title, button, edit, error, targets, review, form, win, overlay,
        flush() { while (microtasks.length) microtasks.shift()(); },
        advance() { f.flush(); for (const job of timers.values()) if (job.ms === 300) job.fn(); },
        submit() { const event = { target: form, submitter: button, defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } }; form.emit('submit', event); doc.emit('submit', event); f.flush(); return event; }
    }; return f;
}
test('first submit reviews locally, escapes via textContent and never starts skeleton', () => {
    const f = fixture(); const e = f.submit(); f.advance();
    assert.equal(e.defaultPrevented, true); assert.equal(f.review.hidden, false);
    assert.equal(f.title.focused, true); assert.equal(f.overlay.hidden, true);
    assert.equal(f.targets[0].textContent, '<b>Trabajo</b>');
    assert.equal(f.button.textContent, 'Publicar solicitud');
});
test('edit returns to essential data and next submit reviews again', () => {
    const f = fixture(); f.submit(); f.edit.emit('click');
    assert.equal(f.fields.hidden, false); assert.equal(f.review.hidden, true);
    assert.equal(f.form.elements.namedItem('titulo').focused, true);
    assert.equal(f.submit().defaultPrevented, true);
});
test('only final native submit proceeds once and can start skeleton', () => {
    const f = fixture(); f.submit();
    assert.equal(f.submit().defaultPrevented, false); f.advance();
    assert.equal(f.button.disabled, true); assert.equal(f.overlay.hidden, false);
    assert.equal(f.submit().defaultPrevented, true);
});
test('invalid input never sends or starts skeleton', () => {
    const f = fixture(false); assert.equal(f.submit().defaultPrevented, true); f.advance();
    assert.equal(f.form.reported, true); assert.equal(f.fields.hidden, false);
    assert.equal(f.overlay.hidden, true);
});
test('bfcache restores final control and validation summary receives focus', () => {
    const f = fixture(); assert.equal(f.error.focused, true);
    f.submit(); f.submit(); f.win.emit('pageshow');
    assert.equal(f.button.disabled, false); assert.equal(f.button.textContent, 'Publicar solicitud');
});
