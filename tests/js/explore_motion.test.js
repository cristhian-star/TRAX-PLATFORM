'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { init } = require('../../app/static/js/explore-motion.js');
function target(extra = {}) {
    const events = new Map();
    return Object.assign({ events,
        addEventListener(name, fn) { if (!events.has(name)) events.set(name, new Set()); events.get(name).add(fn); },
        removeEventListener(name, fn) { events.get(name)?.delete(fn); },
        emit(name, event = {}) { [...(events.get(name) || [])].forEach(fn => fn(event)); }
    }, extra);
}
function fixture(reduced = false) {
    const slides = Array.from({ length: 7 }, () => ({ active: false, classList: { toggle(name, value) { this.owner.active = value; } } }));
    slides.forEach(s => s.classList.owner = s);
    const field = {}, jobs = new Map();
    const doc = target({ hidden: false }), media = target({ matches: reduced });
    let sequence = 0;
    const win = target({ setTimeout(fn, delay) { jobs.set(++sequence, { fn, delay }); return sequence; }, clearTimeout(id) { jobs.delete(id); } });
    const root = target({ querySelectorAll: () => slides,
        contains: node => node === field });
    return { root, field, slides, jobs, doc, media, win,
        start: () => init(root, { doc, media, win }),
        tick() { const [id, job] = jobs.entries().next().value; jobs.delete(id); job.fn(); },
        active: () => slides.map((s,i) => s.active ? i : -1).filter(i => i >= 0) };
}
test('one scene, 8 second automatic loop, no controls required', () => {
    const f = fixture(); f.start(); assert.deepEqual(f.active(), [0]);
    assert.equal([...f.jobs.values()][0].delay, 8000); f.tick(); assert.deepEqual(f.active(), [1]);
    for (let i=0;i<6;i++) f.tick();
    assert.deepEqual(f.active(), [0]); assert.equal(f.jobs.size, 1);
});
test('hover and focus pause together; internal focus transfer never restarts', () => {
    const f = fixture(); f.start(); f.root.emit('mouseenter'); assert.equal(f.jobs.size, 0);
    f.root.emit('focusin'); f.root.emit('mouseleave'); assert.equal(f.jobs.size, 0);
    f.root.emit('focusout', { relatedTarget: f.field }); assert.equal(f.jobs.size, 0);
    f.root.emit('focusout', { relatedTarget: null }); assert.equal(f.jobs.size, 1);
    assert.equal([...f.jobs.values()][0].delay, 8000);
});
test('visibility and reduced motion pause the decorative scenes', () => {
    const f = fixture(true); f.start(); assert.equal(f.jobs.size, 0);
    f.media.matches = false; f.media.emit('change'); assert.equal(f.jobs.size, 1);
    f.doc.hidden = true; f.doc.emit('visibilitychange'); assert.equal(f.jobs.size, 0);
    f.doc.hidden = false; f.doc.emit('visibilitychange'); assert.equal(f.jobs.size, 1);
    f.media.matches = true; f.media.emit('change'); assert.equal(f.jobs.size, 0);
});
test('idempotence, cleanup and reinitialization do not leak timers or listeners', () => {
    const f = fixture(); const dispose = f.start(); assert.equal(f.start(), dispose);
    assert.equal(f.jobs.size, 1); assert.equal(f.root.events.get('focusin').size, 1);
    dispose(); assert.equal(f.jobs.size, 0); assert.deepEqual(f.active(), [0]);
    for (const obj of [f.root,f.doc,f.win,f.media]) for (const listeners of obj.events.values()) assert.equal(listeners.size, 0);
    f.start(); assert.equal(f.jobs.size, 1); assert.equal(f.root.events.get('focusin').size, 1);
});
test('bfcache suspends/resumes and final pagehide disposes', () => {
    const f = fixture(); f.start(); f.win.emit('pagehide', { persisted: true }); assert.equal(f.jobs.size, 0);
    f.win.emit('pageshow'); assert.equal(f.jobs.size, 1);
    f.win.emit('pagehide', { persisted: false }); assert.equal(f.jobs.size, 0);
});
test('absent/incomplete root is harmless on unrelated pages', () => {
    assert.equal(init(null), undefined);
    assert.equal(init({ querySelectorAll: () => [], querySelector: () => null }), undefined);
});
