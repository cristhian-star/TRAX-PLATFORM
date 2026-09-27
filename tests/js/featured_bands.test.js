'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { init } = require('../../app/static/js/featured-bands.js');
function target(extra = {}) {
    const events = new Map();
    return Object.assign({ events,
        addEventListener(n, f) { if (!events.has(n)) events.set(n, new Set()); events.get(n).add(f); },
        removeEventListener(n, f) { events.get(n)?.delete(f); },
        emit(n, e = {}) { [...(events.get(n) || [])].forEach(f => f(e)); }
    }, extra);
}
function fixture(reduced = false) {
    const attrs = new Map(), labels = new Map(), icon = {};
    const button = target({ hidden: true, setAttribute: (k,v) => labels.set(k,v), querySelector: () => icon });
    const root = target({ contains: node => node === button, querySelectorAll: () => [], querySelector: () => button, setAttribute: (k,v) => attrs.set(k,v), removeAttribute: k => attrs.delete(k), toggleAttribute: (k,v) => v ? attrs.set(k,'') : attrs.delete(k) });
    const doc = target({ hidden: false }), media = target({ matches: reduced }), win = target();
    return { root, button, attrs, labels, doc, media, win, start: () => init(root, { doc, media, win }) };
}
test('pause/resume accessible state and ready enhancement', () => {
    const f = fixture(); f.start(); assert(f.attrs.has('data-bands-ready')); assert(!f.button.hidden);
    f.button.emit('click'); assert(f.attrs.has('data-bands-paused')); assert.equal(f.labels.get('aria-pressed'),'true');
    assert.match(f.labels.get('aria-label'), /^Reanudar/);
    f.button.emit('click'); assert(!f.attrs.has('data-bands-paused')); assert.match(f.labels.get('aria-label'), /^Pausar/);
});
test('reduced motion and hidden tab never discard explicit user pause', () => {
    const f = fixture(true); f.start(); assert(f.button.hidden); assert(f.attrs.has('data-bands-paused'));
    f.media.matches = false; f.media.emit('change'); assert(!f.button.hidden); assert(!f.attrs.has('data-bands-paused'));
    f.doc.hidden = true; f.doc.emit('visibilitychange'); assert(f.attrs.has('data-bands-paused'));
    f.doc.hidden = false; f.doc.emit('visibilitychange'); f.button.emit('click');
    f.media.matches = true; f.media.emit('change'); f.media.matches = false; f.media.emit('change');
    assert(f.attrs.has('data-bands-paused')); assert.equal(f.labels.get('aria-pressed'),'true');
});
test('idempotence, bfcache and cleanup preserve static fallback', () => {
    const f = fixture(); const dispose = f.start(); assert.equal(f.start(),dispose);
    assert.equal(f.button.events.get('click').size,1);
    f.win.emit('pagehide',{persisted:true}); assert(f.attrs.has('data-bands-paused'));
    f.win.emit('pageshow'); assert(!f.attrs.has('data-bands-paused'));
    f.win.emit('pagehide',{persisted:false}); assert(!f.attrs.has('data-bands-ready')); assert(f.button.hidden);
    for (const obj of [f.root,f.button,f.doc,f.media,f.win]) for (const listeners of obj.events.values()) assert.equal(listeners.size,0);
    f.start(); assert.equal(f.button.events.get('click').size,1);
});
test('absent or incomplete root on another page is harmless', () => { assert.equal(init(null),undefined); assert.equal(init({querySelector:()=>null}),undefined); });

test('hover and focus pause; keyboard exposes scrollable originals until focus leaves', () => {
    const f=fixture(); f.start(); f.root.emit('mouseenter'); assert(f.attrs.has('data-bands-paused'));
    let scrolled=false;
    f.root.emit('focusin',{target:{matches:()=>true,scrollIntoView:()=>{scrolled=true;}}});
    assert(scrolled); assert(f.attrs.has('data-bands-browse'));
    f.root.emit('mouseleave'); assert(f.attrs.has('data-bands-paused'));
    f.root.emit('focusout',{relatedTarget:f.button}); assert(f.attrs.has('data-bands-browse'));
    f.root.emit('focusout',{relatedTarget:null}); assert(!f.attrs.has('data-bands-browse')); assert(!f.attrs.has('data-bands-paused'));
    f.media.matches=true; f.media.emit('change'); assert(f.attrs.has('data-bands-static'));
});
