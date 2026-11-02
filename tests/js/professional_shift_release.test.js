const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/static/js/professional-shift-release.js', 'utf8');
let elapsed = 0, scheduled;
const events = {};
const button = {disabled:false}, help = {textContent:''};
const form = {dataset:{serverNow:'2030-12-30T21:59:59Z', releaseDeadline:'2030-12-30T22:00:00Z'},
  querySelector:s => s === 'button[type="submit"]' ? button : help,
  addEventListener:(name, fn) => { events[name] = fn; }};
vm.runInNewContext(source, {document:{querySelectorAll:() => [form], addEventListener:() => {}},
  performance:{now:() => elapsed}, window:{setTimeout:fn => {scheduled=fn;}}});
assert.equal(button.disabled, false);
elapsed=1000; scheduled();
assert.equal(button.disabled, true);
assert.match(help.textContent, /12 horas/);
let prevented=false; events.submit({preventDefault(){prevented=true;}});
assert.equal(prevented, true);
console.log('PASS release controller: enabled before deadline, disabled at equality, stale submit prevented');
