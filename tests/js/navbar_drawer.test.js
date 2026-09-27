// Dependency-free controller tests. Geometry/native modal semantics are verified
// separately in Chrome; this DOM double exercises events and state restoration.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../app/static/js/navbar-drawer.js'), 'utf8');

function harness(width = 1400, supported = true) {
    let doc, minimum = 1301;
    const frames = [];
    class Element {
        constructor(tag, cls = '') {
            this.tag = tag; this.className = cls; this.children = []; this.attrs = {};
            this.dataset = {}; this.style = { overflow: '', paddingRight: '' };
            this.events = {}; this.hidden = false; this.open = false; this.textContent = '';
        }
        set id(v) { this.attrs.id = v; }
        get id() { return this.attrs.id; }
        setAttribute(k, v) { this.attrs[k] = String(v); }
        getAttribute(k) { return this.attrs[k] ?? null; }
        hasAttribute(k) { return k in this.attrs; }
        removeAttribute(k) { delete this.attrs[k]; }
        append(...items) { items.forEach(el => { el.remove(); this.children.push(el); el.parent = this; }); }
        insertBefore(el, next) { el.remove(); this.children.splice(this.children.indexOf(next), 0, el); el.parent = this; }
        after(el) { this.parent.insertBefore(el, this.parent.children[this.parent.children.indexOf(this) + 1]); }
        remove() { if (this.parent) { this.parent.children = this.parent.children.filter(x => x !== this); this.parent = null; } }
        contains(el) { return this === el || this.children.some(x => x.contains(el)); }
        matches(selector) {
            if (selector === 'button:not(:disabled)') return this.tag === 'button' && !this.disabled;
            if (selector === '[hidden]') return this.hidden;
            if (selector.startsWith('.')) return this.className.split(' ').includes(selector.slice(1));
            const match = selector.match(/^(\w+)?\[([\w-]+)(?:=['"]?([^'"\]]+)['"]?)?\]$/);
            if (match) return (!match[1] || this.tag === match[1]) && this.hasAttribute(match[2]) && (!match[3] || this.getAttribute(match[2]) === match[3]);
            return this.tag === selector;
        }
        querySelectorAll(selector) {
            const selectors = selector.split(',').map(x => x.trim());
            return this.children.flatMap(el => [...(selectors.some(s => el.matches(s)) ? [el] : []), ...el.querySelectorAll(selector)]);
        }
        querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
        closest(selector) { return this.matches(selector) ? this : this.parent?.closest(selector) || null; }
        cloneNode() {
            const el = new Element(this.tag, this.className);
            el.attrs = { ...this.attrs }; el.hidden = this.hidden; el.open = this.open; el.textContent = this.textContent;
            el.append(...this.children.map(x => x.cloneNode(true))); return el;
        }
        getBoundingClientRect() {
            const w = this.className.includes('nav-measure') ? minimum : this === header ? width : 384;
            return { width: w, left: 900, right: 1284, top: 0, bottom: 800 };
        }
        getClientRects() {
            let el = this;
            while (el) {
                if (el.hidden || (el.tag === 'dialog' && !el.open)) return [];
                if (el.parent?.tag === 'details' && !el.parent.open && el.tag !== 'summary') return [];
                el = el.parent;
            }
            return [{}];
        }
        focus() { doc.activeElement = this; }
        addEventListener(type, fn) { (this.events[type] ||= []).push(fn); }
        fire(type, args = {}) {
            const event = { target: this, preventDefault() { this.prevented = true; }, ...args };
            (this.events[type] || []).forEach(fn => fn(event)); return event;
        }
    }
    const root = new Element('html'), body = new Element('body'); root.clientWidth = width - 15; root.append(body);
    const header = new Element('header', 'site-header site-header--visitor'); body.append(header);
    const brand = new Element('a', 'brand'), toggle = new Element('button', 'menu-toggle');
    const content = new Element('div', 'navigation-content'); content.setAttribute('data-navigation-content', '');
    const nav = new Element('nav'), link = new Element('a'); link.setAttribute('href', '/mercados'); link.href = 'http://localhost/mercados';
    const group = new Element('details', 'nav-dropdown'), summary = new Element('summary'), panel = new Element('div', 'nav-dropdown__menu');
    summary.textContent = 'Operaciones'; group.append(summary, panel);
    const nested = new Element('a'); nested.setAttribute('href', '/presupuestos/nuevo'); nested.href = 'http://localhost/presupuestos/nuevo'; panel.append(nested);
    const theme = new Element('button');
    nav.append(link, group); content.append(nav, theme);
    const dialog = new Element('dialog', 'nav-drawer'), close = new Element('button', 'nav-drawer__close'), inner = new Element('div', 'nav-drawer__body'); dialog.append(close, inner);
    if (supported) dialog.showModal = () => { dialog.open = true; close.focus(); };
    dialog.close = () => { dialog.open = false; };
    header.append(brand, toggle, content, dialog);
    doc = { documentElement: root, body, activeElement: body, querySelector: s => body.querySelector(s), createElement: t => new Element(t), events: {}, addEventListener: Element.prototype.addEventListener };
    const win = { innerWidth: width, location: { href: 'http://localhost/mercados', pathname: '/mercados', search: '' }, requestAnimationFrame: fn => frames.push(fn), events: {}, addEventListener: Element.prototype.addEventListener };
    const context = vm.createContext({ document: doc, window: win, URL, getComputedStyle: () => ({ visibility: 'visible', paddingRight: '3px' }) });
    const initialize = () => vm.runInContext(source, context);
    const flush = () => { while (frames.length) frames.shift()(); };
    const resize = (w, needed = minimum) => { width = w; minimum = needed; win.innerWidth = w; root.clientWidth = w - 15; win.events.resize.forEach(fn => fn()); flush(); };
    initialize();
    return { root, body, header, brand, toggle, content, dialog, close, inner, group, summary, panel, link, nested, theme, doc, win, initialize, resize, flush, button: group.querySelector('.nav-accordion') };
}

test('horizontal row at exact measured minimum, drawer one pixel below', () => {
    const h = harness(1301); assert.equal(h.header.dataset.navMode, 'horizontal');
    h.resize(1300); assert.equal(h.header.dataset.navMode, 'drawer'); assert.equal(h.content.parent, h.inner);
    h.resize(1301); assert.equal(h.content.parent, h.header); assert.equal(h.toggle.hidden, true);
});
test('required width is remeasured, not tied to device width', () => {
    const h = harness(1280); h.resize(1280, 1200); assert.equal(h.header.dataset.navMode, 'horizontal');
    h.resize(1280, 1330); assert.equal(h.header.dataset.navMode, 'drawer');
});
test('idempotent initialization never duplicates controls/listeners', () => {
    const h = harness(1000); h.initialize();
    assert.equal(h.toggle.events.click.length, 1); assert.equal(h.group.querySelectorAll('.nav-accordion').length, 1);
});
test('unsupported dialog leaves native links/details and fallback untouched', () => {
    const h = harness(320, false); assert.equal(h.header.hasAttribute('data-nav-ready'), false);
    assert.equal(h.content.parent, h.header); assert.equal(h.group.querySelector('.nav-accordion'), null);
});
test('open focuses close control, sets expanded and compensates scrollbar', () => {
    const h = harness(1000); h.toggle.fire('click');
    assert.equal(h.dialog.open, true); assert.equal(h.doc.activeElement, h.close);
    assert.equal(h.toggle.getAttribute('aria-expanded'), 'true'); assert.equal(h.root.style.overflow, 'hidden');
    assert.equal(h.body.style.paddingRight, '18px');
});
test('close button restores original inline styles and opener focus', () => {
    const h = harness(1000); h.root.style.overflow = 'auto'; h.body.style.paddingRight = '3px';
    h.toggle.fire('click'); h.close.fire('click'); assert.equal(h.dialog.open, false);
    assert.equal(h.root.style.overflow, 'auto'); assert.equal(h.body.style.paddingRight, '3px');
    assert.equal(h.doc.activeElement, h.toggle); assert.equal(h.toggle.getAttribute('aria-expanded'), 'false');
});
test('Escape native cancel closes and restores focus', () => {
    const h = harness(1000); h.toggle.fire('click'); const e = h.dialog.fire('cancel');
    assert.equal(e.prevented, true); assert.equal(h.dialog.open, false); assert.equal(h.doc.activeElement, h.toggle);
});
test('backdrop click closes, inside blank space does not', () => {
    const h = harness(1000); h.toggle.fire('click');
    h.dialog.fire('pointerdown', { clientX: 1000, clientY: 20 }); h.dialog.fire('click', { clientX: 1000, clientY: 20 });
    assert.equal(h.dialog.open, true);
    h.dialog.fire('pointerdown', { clientX: 100, clientY: 20 }); h.dialog.fire('click', { clientX: 100, clientY: 20 });
    assert.equal(h.dialog.open, false);
});
test('link selection closes without cancelling navigation', () => {
    const h = harness(1000); h.toggle.fire('click'); const e = h.dialog.fire('click', { target: h.link });
    assert.equal(h.dialog.open, false); assert.equal(e.prevented, undefined);
});
test('accordion is a real button with controlled hidden panel', () => {
    const h = harness(1000); assert.equal(h.button.tag, 'button'); assert.equal(h.summary.hidden, true);
    assert.equal(h.button.getAttribute('aria-controls'), h.panel.id); assert.equal(h.nested.getClientRects().length, 0);
    h.toggle.fire('click'); h.button.fire('click'); assert.equal(h.panel.hidden, false);
    assert.equal(h.button.getAttribute('aria-expanded'), 'true'); h.button.fire('click'); assert.equal(h.panel.hidden, true);
});
test('Tab and Shift+Tab wrap only visible controls', () => {
    const h = harness(1000); h.toggle.fire('click'); h.theme.focus();
    assert.equal(h.dialog.fire('keydown', { key: 'Tab' }).prevented, true); assert.equal(h.doc.activeElement, h.close);
    assert.equal(h.dialog.fire('keydown', { key: 'Tab', shiftKey: true }).prevented, true); assert.equal(h.doc.activeElement, h.theme);
});
test('resize while open releases scroll and modal, restores desktop controls', () => {
    const h = harness(1000); h.toggle.fire('click'); h.button.fire('click'); h.resize(1440);
    assert.equal(h.dialog.open, false); assert.equal(h.root.style.overflow, ''); assert.equal(h.body.style.paddingRight, '');
    assert.equal(h.summary.hidden, false); assert.equal(h.button.hidden, true); assert.equal(h.group.open, false);
    assert.equal(h.doc.activeElement, h.brand); assert.equal(h.toggle.getAttribute('aria-expanded'), 'false');
});
test('resize to drawer moves focused navigation to visible opener', () => {
    const h = harness(); h.link.focus(); h.resize(390); assert.equal(h.doc.activeElement, h.toggle);
    assert.equal(h.link.getClientRects().length, 0);
});
test('native desktop details Escape/outside click survive', () => {
    const h = harness(); h.group.open = true; h.header.fire('keydown', { key: 'Escape' });
    assert.equal(h.group.open, false); assert.equal(h.doc.activeElement, h.summary);
    h.group.open = true; h.doc.events.click.forEach(fn => fn({ target: h.brand })); assert.equal(h.group.open, false);
});
test('measurement leaves no clone and route active survives relocation', () => {
    const h = harness(1000); assert.equal(h.body.querySelector('.nav-measure'), null);
    assert.equal(h.link.getAttribute('aria-current'), 'page'); h.resize(1440);
    assert.equal(h.link.getAttribute('aria-current'), 'page'); assert.equal(h.body.querySelectorAll('nav').length, 1);
});
test('late close event cannot unlock a newly reopened drawer', () => {
    const h = harness(1000); h.toggle.fire('click'); h.close.fire('click'); h.toggle.fire('click'); h.dialog.fire('close');
    assert.equal(h.root.style.overflow, 'hidden'); assert.equal(h.toggle.getAttribute('aria-expanded'), 'true');
});
