const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../../app/static/js/professional-coverage-map.js'), 'utf8');

function fixture({explicit=true, key=true, api=true}={}) {
  const handlers={}, timers=[];
  const field=value=>({value, addEventListener(event,fn){this[event]=fn;}});
  const lat=field(''), lng=field(''), action=field('keep'), radius=field('10');
  const canvas={hidden:true}, text={textContent:''}, fallback={hidden:false,querySelector:()=>text};
  const classes=new Set();
  const root={dataset:{mapMode:'private',explicitCenter:String(explicit),hasApiKey:String(key),defaultLat:'-34.6',defaultLng:'-58.4'},
    classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x)},
    closest:()=>null, querySelector:s=>s.includes('canvas')?canvas:fallback};
  const fields={'[data-coverage-latitude]':lat,'[data-coverage-longitude]':lng,'[data-coordinate-action]':action,'[data-coverage-radius]':radius};
  const document={querySelector:s=>fields[s] || (s.includes('data-has-api-key') && key ? root : null),querySelectorAll:()=>[root],addEventListener:(e,fn)=>{handlers[e]=fn;}};
  let marker,circle;
  const maps={Map:class {fitBounds(){}}, Marker:class {constructor(o){marker=this;this.p=o.position;}getPosition(){return {lat:()=>this.p.lat,lng:()=>this.p.lng};}addListener(e,f){this[e]=f;}},
    Circle:class {constructor(o){circle=this;this.radius=o.radius;}getBounds(){return {};}setRadius(r){this.radius=r;}setCenter(p){this.center=p;}}};
  const window={setTimeout:fn=>timers.push(fn)};
  if(api)window.google={maps};
  vm.runInNewContext(source,{window,document,google:window.google,WeakSet,WeakMap});
  handlers.DOMContentLoaded();
  return {lat,lng,action,radius,canvas,fallback,text,window,timers,get marker(){return marker;},get circle(){return circle;}};
}

test('explicit center is not saved by initialization; drag selects center without consent',()=>{
  const f=fixture();assert.equal(f.lat.value,'');assert.equal(f.action.value,'keep');
  f.marker.p={lat:-34.7,lng:-58.5};f.marker.dragend();
  assert.equal(f.lat.value,'-34.700000');assert.equal(f.lng.value,'-58.500000');assert.equal(f.action.value,'update');
  f.radius.value='25';f.radius.change();assert.equal(f.circle.radius,25000);
});
test('existing profile initialization remains compatible',()=>{
  const f=fixture({explicit:false});assert.equal(f.lat.value,'-34.600000');assert.equal(f.action.value,'keep');
});
test('missing key, timeout and API authorization failure retain native fields',()=>{
  for(const options of [{key:false},{api:false},{}]){
    const f=fixture(options);if(options.api===false)f.timers.forEach(fn=>fn());else if(options.key!==false)f.window.gm_authFailure();
    assert.equal(f.fallback.hidden,false);assert.equal(f.canvas.hidden,true);assert.equal(f.lat.value,'');assert.equal(f.action.value,'keep');
  }
});
