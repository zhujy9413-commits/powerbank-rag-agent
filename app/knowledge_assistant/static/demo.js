'use strict';
let demoCatalogue=null;

async function loadDemoCases(){
  try{
    demoCatalogue=await api('/api/demo-cases');
    $('demoCaseSelect').replaceChildren(...demoCatalogue.cases.map(c=>new Option(`${c.id} · ${c.title}`,c.id)));
    $('demoCaseSelect').disabled=!demoCatalogue.cases.length;
    $('useDemoCase').disabled=!demoCatalogue.cases.length;
    $('demoCount').textContent=`${demoCatalogue.cases.length}个可用场景`;
    if(!demoCatalogue.cases.length)$('demoPrepareStatus').textContent='当前身份或资料版本没有可用的固定演示场景。';
    renderDemoData();
  }catch(e){$('demoPrepareStatus').textContent=e.message;$('demoCount').textContent='样本读取未完成';}
}

function renderDemoData(){
  const example=demoCatalogue?.cases.find(c=>c.id===$('demoCaseSelect').value);
  $('demoCaseData').replaceChildren();
  if(!example)return;
  const table=node('table',undefined,'demo-data-table');
  const head=node('tr');
  for(const label of ['数据项','原始数值或记录','核对位置'])head.append(node('th',label));
  const thead=node('thead');thead.append(head);table.append(thead);
  const body=node('tbody');
  for(const fact of example.facts){
    const row=node('tr');row.append(node('td',fact.label),node('td',fact.value));
    const cell=node('td');const ref=example.references[fact.chunk_id];
    const button=node('button',`${ref.title} · ${ref.page?'第'+ref.page+'页':ref.section}`);
    button.type='button';button.addEventListener('click',()=>openSource(fact.chunk_id));cell.append(button);row.append(cell);body.append(row);
  }
  table.append(body);
  const wrapper=node('div',undefined,'demo-table-wrap');wrapper.append(table);
  $('demoCaseData').append(wrapper,node('p','要核对什么：'+example.expectation,'demo-expectation'));
  $('demoPrepareStatus').textContent=example.request.task_id?'此例会显式选择演示任务报告；点击填入后，再提交搜索。':'点击填入后，再提交搜索；不会自动发起模型回答。';
}

function requestForForm(){
  return {query:$('query').value.trim(),mode:document.querySelector('[name=mode]:checked').value,
    include_archived:$('archived').checked,task_id:$('taskScope').value||null,
    version_ids:[...$('queryDocuments').selectedOptions].map(o=>o.value),model:$('queryModel').value.trim()||null};
}

function matchingDemoCase(request){
  const sameList=(a,b)=>JSON.stringify([...(a||[])].sort())===JSON.stringify([...(b||[])].sort());
  return demoCatalogue?.cases.find(c=>c.request.query===request.query&&c.request.model===request.model&&
    c.request.task_id===request.task_id&&c.request.include_archived===request.include_archived&&
    sameList(c.request.version_ids,request.version_ids))||null;
}

function renderDemoVerification(result,example){
  const panel=$('demoVerification');panel.replaceChildren();panel.hidden=!example;
  if(!example)return;
  panel.append(node('strong',`${example.id} · 本次检索对照`));
  if(result.corpus_digest!==demoCatalogue?.corpus_digest){
    panel.append(node('p','知识快照已改变，请刷新演示数据后重新搜索。'));return;
  }
  if(result.status==='retrieval_failed'){
    panel.append(node('p','检索未完成，暂不能判定是否找到。'));return;
  }
  const found=new Set(result.sources.map(s=>s.chunk_id));
  const covered=example.groups.filter(g=>g.chunk_ids.some(id=>found.has(id)));
  panel.append(node('p',`预期证据已找到 ${covered.length} / ${example.groups.length} 组`));
  const list=node('ul');
  for(const group of example.groups){const hit=group.chunk_ids.some(id=>found.has(id));list.append(node('li',`${hit?'已找到':'未找到'} · ${group.label}`,hit?'demo-hit':'demo-miss'));}
  panel.append(list);
  if(example.expected_status)panel.append(node('p',result.status===example.expected_status?'已提示条款与限值依据不足。':'请核对结果状态：本例应明确提示条款与限值依据不足。'));
  panel.append(node('p','核对要点：'+example.expectation),node('p','此处核对检索证据覆盖；回答含义仍需结合原文复核。预期内容未发送给检索或生成模型。','field-help'));
}

function clearDemoAccess(){demoCatalogue=null;$('demoVerification').replaceChildren();$('demoVerification').hidden=true;$('demoCaseData').replaceChildren();$('demoCaseSelect').replaceChildren();$('demoCaseSelect').disabled=true;$('useDemoCase').disabled=true;$('demoCount').textContent='请刷新后重新核验访问范围';}

$('demoCaseSelect').addEventListener('change',renderDemoData);
$('useDemoCase').addEventListener('click',()=>{
  const example=demoCatalogue?.cases.find(c=>c.id===$('demoCaseSelect').value);if(!example)return;
  const options=new Set([...$('queryDocuments').options].map(o=>o.value));
  if(example.request.version_ids.some(id=>!options.has(id))||example.request.task_id&&![...$('taskScope').options].some(o=>o.value===example.request.task_id)){
    $('demoPrepareStatus').textContent='演示资料或任务范围已变化，请刷新后重新选择。';return;
  }
  $('query').value=example.request.query;$('queryModel').value=example.request.model||'';
  $('taskScope').value=example.request.task_id||'';$('archived').checked=example.request.include_archived;
  for(const option of $('queryDocuments').options)option.selected=example.request.version_ids.includes(option.value);
  const search=document.querySelector('[name=mode][value=search]');search.checked=true;search.dispatchEvent(new Event('change'));
  $('query').dispatchEvent(new Event('input'));$('query').focus();
  $('queryForm').scrollIntoView({block:'start',behavior:'smooth'});
  $('demoPrepareStatus').textContent='已填入问题、资料版本和任务范围。点击「搜索资料」查看实际命中。';
});
