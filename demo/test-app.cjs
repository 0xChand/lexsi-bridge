// Exercise the static viewer's data loading and filters without a network or browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

class Node {
  constructor(tag) { this.tag = tag; this.children = []; this.value = ''; this.className = ''; this.textContent = ''; this.events = {}; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  addEventListener(name, callback) { this.events[name] = callback; }
}
const ids = Object.fromEntries(['language','intent','cases','detail','count'].map(id => [id,new Node(id)]));
ids.language.value = ids.intent.value = 'all';
const context = {
  document: {querySelector: s => ids[s.slice(1)], createElement: tag => new Node(tag)},
  fetch: async filename => ({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(__dirname,filename),'utf8'))}),
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'app.js'),'utf8'),context);
setImmediate(() => {
  assert.equal(ids.count.textContent,36);
  assert.equal(ids.cases.children.length,36);
  assert.equal(ids.detail.children[1].tag,'h3');
  ids.language.value='ur'; ids.language.events.change();
  assert.equal(ids.count.textContent,12);
  ids.intent.value='answer'; ids.intent.events.change();
  assert.equal(ids.count.textContent,6);
  ids.cases.children[2].events.click();
  assert.equal(ids.detail.children[0].children[0].textContent,'Urdu');
  assert.equal(ids.detail.children[2].children.length,2);
  console.log('Viewer data loading, filters and comparison passed');
});
