const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function setup(width=320) {
 const events={}, winEvents={}, rootEvents={}, buttonEvents={}, attrs={};
 const doc={documentElement:{clientWidth:width},activeElement:null, addEventListener:(n,fn)=>events[n]=fn};
 const inside={};
 const button={hidden:true,setAttribute:(k,v)=>attrs[k]=v,focus:()=>doc.activeElement=button,
  getBoundingClientRect:()=>({right:260,bottom:70}),addEventListener:(n,fn)=>buttonEvents[n]=fn};
 const panel={hidden:true,style:{},contains:n=>n===inside};
 const root={contains:n=>[root,button,panel,inside].includes(n),querySelector:s=>s==='[data-notification-toggle]'?button:panel,addEventListener:(n,fn)=>rootEvents[n]=fn};
 doc.querySelector=()=>root;
 vm.runInNewContext(fs.readFileSync('app/static/js/professional-notifications.js','utf8'),{document:doc,window:{innerWidth:width,innerHeight:640,addEventListener:(n,fn)=>winEvents[n]=fn}});
 return {doc,button,panel,inside,attrs,events,rootEvents,winEvents,click:buttonEvents.click};
}
test('disclosure toggles without requests, restores focus on Escape, contains mobile geometry',()=>{
 const u=setup(); assert.equal(u.button.hidden,false); u.click();
 assert.equal(u.panel.hidden,false); assert.equal(u.attrs['aria-expanded'],'true');
 assert.equal(u.panel.style.width,'296px'); assert.equal(u.panel.style.left,'12px');
 u.events.click({target:u.inside}); assert.equal(u.panel.hidden,false);
 u.click(); assert.equal(u.panel.hidden,true); u.click();
 let prevented=false; u.events.keydown({key:'Escape',preventDefault:()=>prevented=true});
 assert.ok(prevented); assert.equal(u.doc.activeElement,u.button); assert.equal(u.attrs['aria-expanded'],'false');
});
test('outside click and tab departure close without focus trap; lifecycle closes',()=>{
 const u=setup(1440); u.click();u.events.click({target:{}});assert.ok(u.panel.hidden);
 u.click();u.rootEvents.focusout({relatedTarget:{}});assert.ok(u.panel.hidden);
 u.click();u.winEvents.pagehide();assert.ok(u.panel.hidden);
 assert.equal(u.panel.style.width,'380px');
});
