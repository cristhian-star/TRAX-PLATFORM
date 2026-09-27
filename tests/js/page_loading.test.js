'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { init } = require('../../app/static/js/page-loading.js');
function target(extra = {}) {
    const listeners = {};
    return Object.assign({ listeners,
        addEventListener(name, fn) { (listeners[name] ||= []).push(fn); },
        emit(name, event = {}) { (listeners[name] || []).forEach(fn => fn(event)); }
    }, extra);
}
function node(attrs = {}) {
    return { getAttribute: name => Object.hasOwn(attrs, name) ? attrs[name] : null,
        setAttribute: (name, value) => { attrs[name] = value; },
        removeAttribute: name => { delete attrs[name]; },
        hasAttribute: name => Object.hasOwn(attrs, name),
        closest: () => null };
}
function fixture(qa = false) {
    const status = { textContent: '' }, main = node();
    const overlay = Object.assign(node(), { hidden: true, querySelector: () => status });
    const tasks = new Map(), microtasks = [];
    let clock = 0, sequence = 0;
    const win = target({ location: new URL('https://mandobra.test/explorar'), navigation: target(),
        queueMicrotask: fn => microtasks.push(fn),
        setTimeout(fn, delay) { tasks.set(++sequence, { fn, at: clock + delay }); return sequence; },
        clearTimeout: id => tasks.delete(id) });
    const preview = target();
    const doc = target({ baseURI: win.location.href, body: main,
        querySelector: selector => selector === '[data-page-loading]' ? overlay : selector.startsWith('main') ? main : selector === '[data-loading-preview]' && qa ? preview : null });
    const f = { win, doc, overlay, main, tasks, status, preview,
        flush() { while (microtasks.length) microtasks.shift()(); },
        advance(ms) { f.flush(); const end = clock + ms; while (true) {
            const next = [...tasks].filter(([, job]) => job.at <= end).sort((a,b) => a[1].at - b[1].at)[0];
            if (!next) break;
            clock = next[1].at; tasks.delete(next[0]); next[1].fn();
        } clock = end; },
        click(attrs = {}, extra = {}) {
            const link = Object.assign(node({ href: '/mercados', ...attrs }), { href: new URL(attrs.href || '/mercados', doc.baseURI).href });
            if (attrs['data-no-loading'] !== undefined) link.closest = () => link;
            const event = { target: { closest: () => link }, button: 0, ...extra };
            doc.emit('click', event); return event;
        },
        submit(attrs = {}, valid = true, button = null) {
            const form = Object.assign(node(attrs), { checkValidity: () => valid, noValidate: false });
            if (attrs['data-no-loading'] !== undefined) form.closest = () => form;
            const event = { target: form, submitter: button }; doc.emit('submit', event); return event;
        }
    };
    init(doc, win); return f;
}
test('300ms delay, live message, main busy and long wait at 8s', () => {
    const f = fixture(); f.click(); f.advance(299); assert.equal(f.overlay.hidden, true);
    f.advance(1); assert.equal(f.overlay.hidden, false); assert.equal(f.main.getAttribute('aria-busy'), 'true');
    assert.equal(f.status.textContent, 'Cargando contenido');
    f.advance(7700); assert.match(f.status.textContent, /Esto está tardando/);
    f.advance(22000); assert.equal(f.overlay.hidden, true); assert.equal(f.tasks.size, 0);
    assert.equal(f.main.getAttribute('aria-busy'), null);
});
test('fast navigation and bfcache pageshow cancel timers without a flash', () => {
    const f = fixture(); f.click(); f.advance(100); f.win.emit('pagehide'); f.advance(1000);
    assert.equal(f.overlay.hidden, true); assert.equal(f.tasks.size, 0);
    f.click(); f.advance(300); f.win.emit('pageshow', { persisted: true });
    assert.equal(f.overlay.hidden, true); assert.equal(f.main.getAttribute('aria-busy'), null);
});
test('external, protocols, download, targets, hashes, opt out and modifiers excluded', () => {
    for (const attrs of [{ href: 'https://other.test' }, { href: 'mailto:x@example.test' }, { href: 'tel:123' },
        { href: 'https://wa.me/123' }, { download: '' }, { target: '_blank' }, { target: 'frame' },
        { href: '#section' }, { href: '/explorar#' }, { 'data-no-loading': '' }]) {
        const f = fixture(); f.click(attrs); f.advance(9000); assert.equal(f.overlay.hidden, true, JSON.stringify(attrs));
        assert.equal(f.tasks.size, 0);
    }
    for (const key of ['ctrlKey', 'shiftKey', 'altKey', 'metaKey', 'defaultPrevented']) {
        const f = fixture(); f.click({}, { [key]: true }); f.advance(500); assert.equal(f.overlay.hidden, true);
    }
    const f = fixture(); f.click({}, { button: 1 }); f.advance(500); assert.equal(f.overlay.hidden, true);
});
test('cancellation by a later listener before the microtask never paints', () => {
    const f = fixture(), e = f.click(); e.defaultPrevented = true; f.advance(9000);
    assert.equal(f.tasks.size, 0); assert.equal(f.overlay.hidden, true);
});
test('valid native forms preserve method/action and invalid forms do not show loading', () => {
    const f = fixture(), event = f.submit({ method: 'post', action: '/registro' });
    f.advance(300); assert.equal(f.overlay.hidden, false);
    assert.equal(event.target.getAttribute('method'), 'post'); assert.equal(event.target.getAttribute('action'), '/registro');
    for (const [attrs, valid] of [[{}, false], [{ target: '_blank' }, true], [{ method: 'dialog' }, true],
        [{ action: 'https://other.test' }, true], [{ 'data-no-loading': '' }, true]]) {
        const f = fixture(); f.submit(attrs, valid); f.advance(500); assert.equal(f.overlay.hidden, true);
    }
});
test('submitter overrides, novalidate and canceled submit respected', () => {
    const f = fixture(); f.submit({}, true, node({ formtarget: '_blank' })); f.advance(500); assert.equal(f.overlay.hidden, true);
    const e = f.submit(); e.defaultPrevented = true; f.advance(500); assert.equal(f.overlay.hidden, true);
    f.submit({}, false, Object.assign(node(), { formNoValidate: true })); f.advance(300); assert.equal(f.overlay.hidden, false);
});
test('Escape, invalid, navigation abort and navigation error restore previous busy state', () => {
    for (const kind of ['escape', 'invalid', 'abort', 'navigateerror', 'navigatesuccess']) {
        const f = fixture(); f.main.setAttribute('aria-busy', 'false'); f.click(); f.advance(300);
        if (kind === 'escape') f.doc.emit('keydown', { key: 'Escape' });
        else if (kind === 'invalid') f.doc.emit('invalid');
        else if (kind === 'abort') { const signal = target(); f.win.navigation.emit('navigate', { signal }); signal.emit('abort'); }
        else f.win.navigation.emit(kind);
        assert.equal(f.overlay.hidden, true); assert.equal(f.tasks.size, 0); assert.equal(f.main.getAttribute('aria-busy'), 'false');
    }
});
test('idempotent, missing markup safe, local UI ignored, no prevention or focus calls', () => {
    const f = fixture(); init(f.doc, f.win); assert.equal(f.doc.listeners.click.length, 1);
    f.doc.emit('click', { button: 0, target: { closest: () => null } }); f.advance(500); assert.equal(f.tasks.size, 0);
    assert.equal(init({ querySelector: () => null }, f.win), undefined);
    f.click({}, { preventDefault() { assert.fail('native navigation intercepted'); } }); f.advance(300);
    assert.equal(f.overlay.hidden, false);
});
test('repeated navigation replaces timers and pageshow cancels queued work', () => {
    const f = fixture(); f.click(); f.advance(200); f.click(); f.advance(299); assert.equal(f.overlay.hidden, true);
    f.advance(1); assert.equal(f.overlay.hidden, false); assert.equal(f.tasks.size, 2);
    f.click(); f.win.emit('pageshow'); f.advance(9000); assert.equal(f.overlay.hidden, true); assert.equal(f.tasks.size, 0);
});
test('QA-only marker uses the same controller and cleans itself after 12s', () => {
    const f = fixture(true); f.preview.emit('click', {}); f.advance(300);
    assert.equal(f.overlay.hidden, false); f.advance(7700); assert.match(f.status.textContent, /Esto está tardando/);
    f.advance(4000); assert.equal(f.overlay.hidden, true); assert.equal(f.tasks.size, 0);
    assert.equal(f.main.getAttribute('aria-busy'), null);
    assert.equal(fixture().preview.listeners.click, undefined);
});
test('abort of an older navigation cannot cancel the newest loading state', () => {
    const f = fixture(), oldSignal = target();
    f.click(); f.flush(); f.win.navigation.emit('navigate', { signal: oldSignal });
    f.click(); oldSignal.emit('abort'); f.advance(300);
    assert.equal(f.overlay.hidden, false);
});
