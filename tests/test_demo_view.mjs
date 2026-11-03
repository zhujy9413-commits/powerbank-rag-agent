import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Exercise the coverage renderer without a browser, network, or model.
class Element {
  constructor(text=''){this.text=text;this.children=[];this.hidden=false;}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  addEventListener(){}
  get textContent(){return this.text+this.children.map(c=>c.textContent).join(' ');}
}
const elements=new Map();
const context=vm.createContext({
  $:id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},
  node:(tag,text='')=>new Element(text),
});
vm.runInContext(fs.readFileSync(new URL('../app/knowledge_assistant/static/demo.js',import.meta.url),'utf8'),context);
context.example={id:'CHECK',groups:[{label:'条款',chunk_ids:['requirement']},{label:'报告',chunk_ids:['report']}],expectation:'核对双方'};
context.result={corpus_digest:'same',status:'search_results',sources:[{chunk_id:'requirement'}]};
vm.runInContext("demoCatalogue={corpus_digest:'same'};renderDemoVerification(result,example)",context);
assert.match(elements.get('demoVerification').textContent,/已找到 1 \/ 2 组/);
assert.match(elements.get('demoVerification').textContent,/未找到 · 报告/);
context.result.status='retrieval_failed';
vm.runInContext('renderDemoVerification(result,example)',context);
assert.match(elements.get('demoVerification').textContent,/检索未完成/);
assert.doesNotMatch(elements.get('demoVerification').textContent,/已找到/);
context.result={corpus_digest:'changed',status:'search_results',sources:[{chunk_id:'requirement'},{chunk_id:'report'}]};
vm.runInContext('renderDemoVerification(result,example)',context);
assert.match(elements.get('demoVerification').textContent,/知识快照已改变/);
assert.doesNotMatch(elements.get('demoVerification').textContent,/2 \/ 2/);
console.log('Demo view: missing evidence, failed retrieval, and changed snapshot checks passed.');
