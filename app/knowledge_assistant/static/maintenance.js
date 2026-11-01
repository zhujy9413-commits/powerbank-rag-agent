'use strict';
const knowledgeStateNames={unverified:'待核验',pending_publish:'待发布',published:'已发布',retired:'已停用'};
async function maintenanceAction(action){try{await action();await loadMaintenance();await refreshConfig();if(typeof loadQueryOptions==='function')await loadQueryOptions();}catch(e){$('maintenanceStatus').textContent=e.message;}}
function knowledgeRecord(entry){
 const box=node('article',undefined,'work-item');box.append(node('h3',entry.title+' · '+entry.version),node('p',knowledgeStateNames[entry.state]+' · '+entry.document_id,'work-meta'));
 box.append(node('p','来源：'+entry.source_origin+'；使用范围：'+entry.usage_rights),node('p','适用范围：'+entry.applicability));
 if(entry.conflict)box.append(node('p',entry.conflict,'limitation'));
 const detail=node('details');detail.append(node('summary','核对完整原文与维护记录'),node('pre',entry.original_text,'original-text'),node('pre',JSON.stringify({核验意见:entry.review_note,操作者:entry.reviewer,记录:entry.events},null,2),'original-text'));box.append(detail);
 const reason=node('input');reason.placeholder='填写核验意见或操作理由';reason.maxLength=1000;reason.setAttribute('aria-label',entry.id+' 操作理由');box.append(reason);
 if(entry.state==='unverified'&&!entry.conflict){
  const checks=[];for(const text of ['已核对来源与使用范围','已核对版本与原文定位','已由对应专业人员确认适用性']){const label=node('label',undefined,'work-ack'),check=node('input');check.type='checkbox';label.append(check,document.createTextNode(text));checks.push(check);box.append(label);}
  const verify=node('button','提交核验并转待发布');verify.addEventListener('click',()=>maintenanceAction(async()=>{await api('/api/knowledge/'+entry.id,{action:'verify',note:reason.value,source_verified:checks[0].checked,version_verified:checks[1].checked,applicability_verified:checks[2].checked});$('maintenanceStatus').textContent='核验记录已保存，资料尚未发布。';}));box.append(verify);
 }
 if(['pending_publish','published'].includes(entry.state)){
  const action=entry.state==='pending_publish'?'publish':'retire',button=node('button',action==='publish'?'构建索引并发布':'停用此版本');button.addEventListener('click',()=>maintenanceAction(async()=>{await api('/api/knowledge/'+entry.id,{action,note:reason.value});$('maintenanceStatus').textContent=action==='publish'?'已发布；新查询按新快照处理，历史引用保留。':'已停用；默认新查询排除，授权历史仍可查看。';}));box.append(button);
 }
 return box;
}
async function loadMaintenance(){
 const entries=await api('/api/knowledge');$('knowledgeRecords').replaceChildren(...entries.reverse().map(knowledgeRecord));
 const feedback=await api('/api/maintenance-feedback');$('maintenanceFeedback').replaceChildren();
 for(const record of feedback){const box=node('article',undefined,'work-item');box.append(node('h3',record.query),node('p',record.kind+' · '+record.note),node('p','请求 '+record.request_id+' · 知识快照 '+record.snapshot,'work-meta'));const state=node('select');for(const [value,text] of Object.entries({pending:'待处理',handled:'已处理',deferred:'暂不处理'}))state.append(new Option(text,value));state.value=record.state;const note=node('input');note.value=record.handling_note;note.placeholder='处理说明与理由';const save=node('button','保存反馈处理');save.addEventListener('click',()=>maintenanceAction(async()=>{await api('/api/maintenance-feedback/'+record.id,{state:state.value,note:note.value});$('maintenanceStatus').textContent='反馈处理已保存，知识内容未自动发布。';}));box.append(state,note,save);$('maintenanceFeedback').append(box);}
 if(!feedback.length)$('maintenanceFeedback').append(node('p','当前没有可处理的反馈。'));
}
$('navMaintenance').addEventListener('click',async()=>{for(const id of ['askPage','libraryPage','workPage'])$(id).hidden=true;$('maintenancePage').hidden=false;for(const id of ['navAsk','navLibrary','navWork'])$(id).classList.remove('active');$('navMaintenance').classList.add('active');document.querySelector('.breadcrumb').textContent='共用知识底座 / 知识维护';try{await loadMaintenance();}catch(e){$('maintenanceStatus').textContent=e.message;}});
$('knowledgeForm').addEventListener('submit',e=>{e.preventDefault();maintenanceAction(async()=>{const data={document_id:$('knowledgeDocument').value,version:$('knowledgeVersion').value,title:$('knowledgeTitle').value,source_origin:$('knowledgeOrigin').value,usage_rights:$('knowledgeRights').value,applicability:$('knowledgeApplicability').value,material_type:$('knowledgeType').value,source_role:$('knowledgeRole').value,allowed_roles:$('knowledgeAccess').value==='all'?['engineer','employee']:['engineer'],original_text:$('knowledgeText').value};await api('/api/knowledge',data);$('knowledgeFormStatus').textContent='已登记为待核验，原文保留；未进入检索。';});});
