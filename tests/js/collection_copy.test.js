const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/static/js/collection-copy.js', 'utf8');
function fixture(clipboard) {
 const input = {value:'https://checkout.example.test/payment-orders/abc',focus(){this.focused=true;},select(){this.selected=true;}};
 const status = {textContent:''}; const listeners = {};
 const button = {hidden:true,addEventListener(name,fn){listeners[name]=fn;}};
 const root = {querySelector(selector){return {'input':input,'[data-copy-button]':button,'[data-copy-status]':status}[selector];}};
 vm.runInNewContext(source,{document:{querySelectorAll(){return [root];}},navigator:{clipboard},window:{isSecureContext:true}});
 return {input,status,button,listeners};
}
test('production copy controller reveals and copies exact displayed URL only on click',async()=>{
 const writes=[];const f=fixture({writeText:async value=>writes.push(value)});
 assert.equal(f.button.hidden,false);assert.equal(writes.length,0);
 await f.listeners.click();assert.deepEqual(writes,[f.input.value]);assert.match(f.status.textContent,/copiado/);
});
test('denied or absent clipboard selects the real input for manual copy',async()=>{
 for(const clipboard of [undefined,{writeText:async()=>{throw Error('denied');}}]){
  const f=fixture(clipboard);await f.listeners.click();assert.equal(f.input.focused,true);assert.equal(f.input.selected,true);assert.match(f.status.textContent,/Ctrl\+C/);
 }
});
