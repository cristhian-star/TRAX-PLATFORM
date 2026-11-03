const test=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
test('production preview switches modes, distinguishes blank/free, escapes text and syncs radius',()=>{
  const element=(value='')=>({value,hidden:false,checked:false,textContent:'',children:[],listeners:{},addEventListener(e,f){this.listeners[e]=f;},dispatchEvent(e){this.listeners[e.type]?.(e);},replaceChildren(){this.children=[];},append(n){this.children.push(n);}});
  const form=element();form.elements={};
  for(const name of ['mode','package_amount','visit_amount','diagnosis_amount','package_amount_free','visit_amount_free','diagnosis_amount_free','coverage_location','coverage_city','coverage_province','notes','discount_repair'])form.elements[name]=element();
  form.elements.mode.value='PACKAGE';form.elements.notes.value='<img src=x onerror=bad()>';
  const nodes={};for(const key of ['preview-prices','preview-zone','preview-notes','preview-discount','coverage-radius','radius-slider','radius-slider-label'])nodes[`[data-${key}]`]=element();
  const groups=['PACKAGE','SEPARATE'].map(priceGroup=>({...element(),dataset:{priceGroup}}));
  const root={querySelector:s=>s==='form'?form:nodes[s],querySelectorAll:()=>groups};
  const document={querySelector:()=>root,createElement:()=>element()};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../app/static/js/emergency-configuration.js'),'utf8'),{document,Event:class{constructor(type){this.type=type;}}});
  assert.match(nodes['[data-preview-prices]'].children[0].textContent,/Sin configurar/);
  assert.equal(nodes['[data-preview-notes]'].textContent,'<img src=x onerror=bad()>');
  form.elements.mode.value='SEPARATE';form.elements.visit_amount_free.checked=true;form.elements.diagnosis_amount.value='NaN';form.listeners.change();
  assert.equal(groups[0].hidden,true);assert.equal(groups[1].hidden,false);
  assert.match(nodes['[data-preview-prices]'].children[0].textContent,/Sin cargo/);
  assert.match(nodes['[data-preview-prices]'].children[1].textContent,/Revisá/);
  nodes['[data-radius-slider]'].value='35';nodes['[data-radius-slider]'].listeners.input();assert.equal(nodes['[data-coverage-radius]'].value,'35');
});
