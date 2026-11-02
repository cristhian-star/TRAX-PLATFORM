const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
test('native mobile disclosure closes with Escape and outside, restores focus only when needed',()=>{
 const events={}; const inside={};
 const doc={activeElement:inside,addEventListener:(key,fn)=>events[key]=fn};
 const trigger={focus:()=>doc.activeElement=trigger};
 const menu={open:true,querySelector:()=>trigger,contains:e=>e===inside||e===trigger};
 doc.querySelector=()=>menu;
 vm.runInNewContext(fs.readFileSync('app/static/js/professional-navigation.js','utf8'),{document:doc});
 events.keydown({key:'Tab'}); assert.equal(menu.open,true);
 events.keydown({key:'Escape'});assert.equal(menu.open,false);assert.equal(doc.activeElement,trigger);
 menu.open=true;events.click({target:inside});assert.equal(menu.open,true);
 doc.activeElement=inside;events.click({target:{}});assert.equal(menu.open,false);assert.equal(doc.activeElement,trigger);
});
test('production profile controller activates only real hash targets',()=>{
 const selected={};const listeners={};
 const nodes=['general','media'].map(name=>({dataset:{profilePanel:name,profilePanelTrigger:name},classList:{toggle:(_,v)=>selected[name]=v},addEventListener:()=>{}}));
 const root={querySelectorAll:()=>nodes,querySelector:()=>null};
 const win={location:{hash:'#perfil-media'},addEventListener:(k,f)=>listeners[k]=f};
 vm.runInNewContext(fs.readFileSync('app/static/js/profile-private-ux-a.js','utf8'),{document:{addEventListener:(_,fn)=>fn(),querySelector:()=>root},window:win});
 assert.equal(selected.media,true);assert.equal(selected.general,false);
 win.location.hash='#invalid';listeners.hashchange();assert.equal(selected.media,true);
});
