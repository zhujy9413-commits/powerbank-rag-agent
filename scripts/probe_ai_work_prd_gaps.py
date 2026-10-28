"""Observe current PRD gaps in an isolated synthetic service without private settings."""
from pathlib import Path
import argparse,sys,json,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
ap=argparse.ArgumentParser(description='Read-only gap observations against a temporary synthetic review service, no model requests.')
ap.add_argument('--output',required=True,type=Path)
args=ap.parse_args()
if args.output.exists():ap.error('结果路径已存在，拒绝覆盖。')
from app.ai_work.review import ReviewService,ConflictError,ENGINE_SHA256,stamp
from app.knowledge_assistant.core import Corpus,Principal
p=Principal('prd-audit-agent','engineer',('DEMO-TASK-001',))
result=dict(version='prd-implementation-audit-probes-v0.1',recorded_at=stamp(),scope='Temporary synthetic service; no live tasks or model settings read or changed',model_requests=0,engine_sha256=ENGINE_SHA256,observations=[])
with tempfile.TemporaryDirectory(prefix='powerbank-prd-audit-') as d:
 s=ReviewService(Path(d)/'audit.sqlite3',Corpus())
 try:
  t=s.create(p,{'sample':True});tid=t['task_id'];s.confirm(p,tid,dict(revision=1,acknowledged=True,corrections={}))
  r=s.run(p,tid,dict(revision=2,idempotency_key='prd-audit-baseline'));rid=r['run_id']
  result['observations'].append(dict(id='PROBE-01',finding='fixed_scope_catalog',actual=s.catalog(p),implication='Current basis and checklist are fixed; API supplies no user-selected basis or applicability fields.'))
  for oid,data in [('PROBE-02',dict(revision=2,acknowledged=True,corrections={},selected_basis='RevA')),('PROBE-03',dict(revision=2,acknowledged=True,corrections={},excluded_items=['A1-01']))]:
   try:s.confirm(p,tid,data);observed=dict(accepted=True)
   except Exception as e:observed=dict(accepted=False,error_type=type(e).__name__,message=str(e))
   assert not observed['accepted']
   result['observations'].append(dict(id=oid,finding='unsupported_confirmation_fields',**observed))
  assert s.result(p,rid)['report_sha256']==r['report_sha256']
  c=s.corpus.by_id['SYN-NORM-RESPONSE'];c['publication_status']='disabled'
  historical={}
  for name,fn in [('task',lambda:s.task(p,tid)),('run',lambda:s.result(p,rid)),('pdf',lambda:s.pdf(p,tid)),('run_again',lambda:s.run(p,tid,dict(revision=2,idempotency_key='prd-audit-stopped')))]:
   try:fn();historical[name]={'accessible':True}
   except Exception as e:historical[name]={'accessible':False,'error_type':type(e).__name__,'message':str(e)}
  assert not any(v['accessible'] for v in historical.values())
  result['observations'].append(dict(id='PROBE-04',finding='disabled_basis_blocks_historical_task_run_and_pdf',actual=historical,implication='Current _task calls basis_catalog, so disabling one required basis blocks both new evaluation and existing records even when user access is unchanged. PRD 13 historical source-state workflow incomplete.'))
  c['publication_status']='active'
  assert s.result(p,rid)['report_sha256']==r['report_sha256']
  before=s.list_tasks(p)
  try:s.create(p,{'filename':'broken.pdf','pdf_base64':'JVBERi1icm9rZW4='});bad=False
  except Exception as e:bad=True;err={'error_type':type(e).__name__,'message':str(e)}
  assert bad and s.list_tasks(p)==before
  result['observations'].append(dict(id='PROBE-05',finding='parse_rejection_has_no_failed_task_record',actual=err,task_count_before=len(before),task_count_after=len(s.list_tasks(p)),implication='Input rejected with message; no persisted parsing/failed-upload task event.'))
  for q,data in [('PROBE-06',{'sample':True,'name':'自定义任务'}),('PROBE-07',{'sample':True,'basis_pdf_base64':'fixture'})]:
   try:s.create(p,data);accepted=True
   except Exception as e:accepted=False;err={'error_type':type(e).__name__,'message':str(e)}
   assert not accepted
   result['observations'].append(dict(id=q,finding='task_name_or_task_basis_attachment_not_supported',accepted=accepted,actual=err))
 finally:s.db.close()
result['observation_count']=len(result['observations'])
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(observations=[{'id':v['id'],'finding':v['finding']} for v in result['observations']],model_requests=0),ensure_ascii=False))
