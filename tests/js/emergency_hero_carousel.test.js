const assert = require('node:assert/strict');
const { init } = require('../../app/static/js/emergency-hero-carousel-v1.js');
const events = () => ({ listeners: {}, addEventListener(n, f) { this.listeners[n] = f; }, emit(n) { this.listeners[n]?.(); } });
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function setup({ reduced = false, failed = [] } = {}) {
    const timers = new Map(), requests = [], motions = [];
    let id = 0;
    const doc = { ...events(), hidden: false }, media = { ...events(), matches: reduced };
    const win = { ...events(), setTimeout(fn, ms) { timers.set(++id, { fn, ms }); return id; }, clearTimeout(n) { timers.delete(n); },
        Image: class { set src(value) { requests.push(value); Promise.resolve().then(() => failed.includes(value) ? this.onerror() : this.onload()); } async decode() {} },
    };
    const layers = [0, 1].map(i => ({ src: i ? '' : '0', hidden: Boolean(i), style: {}, animate(frames, options) {
        let resolve, reject;
        const animation = { finished: new Promise((r, j) => { resolve = r; reject = j; }), finish: () => resolve(), cancel: () => reject(new Error('cancelled')) };
        motions.push({ frames, options, animation }); return animation;
    } }));
    const root = { querySelectorAll(s) { return s === 'img' ? layers : Array.from({ length: 6 }, (_, i) => ({ dataset: { src: String(i), position: '62% center' } })); } };
    init(root, { doc, win, media });
    return { root, doc, win, media, timers, requests, motions, layers, async tick() {
        assert.equal(timers.size, 1); const [key, task] = [...timers][0]; assert.equal(task.ms, 6500);
        timers.delete(key); task.fn(); await flush();
    }, async finish() { motions.slice(-2).forEach(m => m.animation.finish()); await flush(); } };
}
(async () => {
    const reduced = setup({ reduced: true }); await flush();
    assert.equal(reduced.timers.size, 0); assert.equal(reduced.requests.length, 0); assert.equal(reduced.layers[0].src, '0');
    const a = setup(); await flush();
    init(a.root, { doc: a.doc, win: a.win, media: a.media }); assert.equal(a.timers.size, 1);
    for (let i = 1; i <= 6; i++) {
        await a.tick(); assert.equal(a.motions.at(-2).frames[1].transform, 'translateX(-100%)');
        assert.equal(a.motions.at(-1).frames[0].transform, 'translateX(100%)');
        assert.equal(a.motions.at(-1).options.duration, 900);
        assert.equal(a.layers.filter(l => !l.hidden).length, 2);
        await a.finish(); assert.equal(a.layers.find(l => !l.hidden).src, String(i % 6));
    }
    assert.equal(new Set(a.requests).size, a.requests.length);
    a.doc.hidden = true; a.doc.emit('visibilitychange'); assert.equal(a.timers.size, 0);
    a.doc.hidden = false; a.doc.emit('visibilitychange'); assert.equal(a.timers.size, 1);
    a.win.emit('pagehide'); assert.equal(a.timers.size, 0);
    a.win.emit('pageshow'); a.win.emit('pageshow'); assert.equal(a.timers.size, 1);
    await a.tick(); a.media.matches = true; a.media.emit('change'); await flush();
    assert.equal(a.timers.size, 0); assert.equal(a.layers.filter(l => !l.hidden).length, 1);
    assert.equal(a.layers.find(l => !l.hidden).src, '0');
    const broken = setup({ failed: ['1', '2'] }); await broken.tick(); await broken.finish();
    assert.equal(broken.layers.find(l => !l.hidden).src, '3');
    const allBroken = setup({ failed: ['1', '2', '3', '4', '5'] }); await allBroken.tick();
    assert.equal(allBroken.layers[0].hidden, false); assert.equal(allBroken.layers[0].src, '0');
    assert.equal(allBroken.motions.length, 0);
    console.log('E3: order/loop, 6500/900, direction, cache, reduced motion, visibility, BFCache, cancellation and failed images OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
