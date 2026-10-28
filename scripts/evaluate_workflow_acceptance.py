"""Full HTTP workflow regression on consumed PDFs, no model requests or private config reads."""
import argparse
import base64
from copy import deepcopy
import hashlib
import http.client
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import threading
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.knowledge_assistant.core import Principal
from app.knowledge_assistant.server import LocalServer
from app.ai_work.review import ENGINE_SHA256,stamp

CASES=[dict(case_id='FLOW-01',path='output/pdf/review-holdout-v0.1/HO-17-summary-wrap.pdf',
    counts={'no_issue':12},report_basis='RevB'),
    dict(case_id='FLOW-02',path='output/pdf/p1-holdout-v0.1/HP-08.pdf',counts={'no_issue':11,'conflict':1},report_basis='RevB'),
    dict(case_id='FLOW-03',path='output/pdf/SYN-TR-001-R1.pdf',
    counts={'no_issue':5,'nonconformity':2,'evidence_insufficient':3,'conflict':2},report_basis='RevA')]
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RESULT_NAMES={'no_issue':'未发现问题','nonconformity':'按记录比较不符合','evidence_insufficient':'证据不足','conflict':'冲突'}
REVIEW_NAMES={'confirmed':'确认系统结果','excluded':'排除系统结果','unresolved':'暂无法确认'}

def sha(b):return hashlib.sha256(b).hexdigest()
def start(local_dir):
    server=LocalServer(('127.0.0.1',0),Principal('workflow-acceptance-agent','engineer',('DEMO-TASK-001',)),local_dir)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();return server,thread
def stop(server,thread):
    server.shutdown();server.server_close();thread.join();server.store.db.close();server.review_service.db.close()

class Client:
    def __init__(self,server):
        self.port=server.server_address[1];self.headers={}
        status,value,h=self.call('GET','/api/config');assert status==200
        self.headers={'Cookie':h['Set-Cookie'].split(';')[0],'X-Local-Token':value['csrf_token'],'Content-Type':'application/json'}
    def call(self,method,path,body=None,raw=False):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=10)
        try:
            conn.request(method,path,json.dumps(body,ensure_ascii=False).encode() if body is not None else None,self.headers)
            response=conn.getresponse();blob=response.read();headers=dict(response.getheaders())
            return response.status,blob if raw else json.loads(blob),headers
        finally:conn.close()
    def ok(self,method,path,body=None,raw=False):
        status,value,_=self.call(method,path,body,raw);assert status==200,(path,status);return value

def read_xlsx(blob):
    with ZipFile(BytesIO(blob)) as z:
        names=[s.attrib['name'] for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS)]
        rows={}
        for index,name in enumerate(names,1):
            tree=ET.fromstring(z.read(f'xl/worksheets/sheet{index}.xml'));assert not tree.findall('.//m:f',NS)
            rows[name]=[[ ''.join(c.itertext()) if c.attrib.get('t')=='inlineStr' else c.findtext('m:v',default='',namespaces=NS) for c in row.findall('m:c',NS)] for row in tree.findall('m:sheetData/m:row',NS)]
        return rows

def verify_export(blob,run):
    rows=read_xlsx(blob);items={i['item_id']:i for i in run['items']};details=rows['逐项检查'][1:]
    exact=len(details)==len(items) and all(r[0] in items and r[4]==RESULT_NAMES[items[r[0]]['result']] and
        r[7]==('是' if items[r[0]]['conditional'] else '否') and r[8]==REVIEW_NAMES[items[r[0]]['review']['disposition']] and r[9]==items[r[0]]['review']['reason'] for r in details)
    history=rows['复核记录'][1:];expected=run['review_history']
    history_ok=len(history)==len(expected) and all(r[:5]==[e['item_id'],str(e['version']),REVIEW_NAMES[e['disposition']],e['reason'],e['actor']] for r,e in zip(history,expected,strict=True))
    evidence=rows['依据与原文'][1:];refs=[f for i in run['items'] for f in i['report_evidence']]
    quotes_ok=all(any(r[1]=='报告提取原文' and r[4]==f['quote'] and r[5]==f['sha256'] and r[3]==f"PDF第{f['page']}页" for r in evidence) for f in refs)
    scope=dict(rows['任务与范围'][1:])
    return dict(four_named_sheets=list(rows)==['任务与范围','逐项检查','依据与原文','复核记录'],
        item_results_and_dispositions=exact,history_append_only=history_ok,all_report_refs_present=quotes_ok,
        scope_and_pending=scope['待复核项目']=='0' and scope['任务状态']=='复核完成' and scope['报告SHA-256']==run['report_sha256'],
        sheet_rows={k:len(v) for k,v in rows.items()})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--exports',type=Path,required=True);args=ap.parse_args()
    if args.output.exists() or args.exports.exists():ap.error('结果路径已存在，拒绝覆盖。')
    args.exports.mkdir(parents=True);result=dict(version='workflow-acceptance-v0.1',started_at=stamp(),dataset_status='consumed_workflow_regression',
        human_business_trial=False,professional_review='pending',model_requests=0,engine_sha256=ENGINE_SHA256,cases=[])
    with tempfile.TemporaryDirectory(prefix='powerbank-workflow-') as temp:
        server,thread=start(temp);client=Client(server)
        try:
            for case in CASES:
                checks=[]
                def check(name,passed,**evidence):
                    checks.append(dict(name=name,passed=bool(passed),**evidence))
                blob=(ROOT/case['path']).read_bytes();task=client.ok('POST','/api/ai-work/tasks',dict(filename=case['case_id']+'.pdf',pdf_base64=base64.b64encode(blob).decode()))
                tid=task['task_id'];base='/api/ai-work/tasks/'+tid
                check('uploaded_pdf_identity',sha(client.ok('GET',base+'/pdf',raw=True))==sha(blob) and task['snapshots'][0]['report']['report_basis']==case['report_basis'])
                key=case['case_id']+'-stable-key';request=dict(revision=1,idempotency_key=key)
                check('unconfirmed_run_rejected',client.call('POST',base+'/run',request)[0]==409)
                check('missing_ack_rejected',client.call('POST',base+'/confirm',dict(revision=1,acknowledged=False,corrections={}))[0]==400)
                task=client.ok('POST',base+'/confirm',dict(revision=1,acknowledged=True,corrections={}));snapshot=task['snapshots'][-1]
                check('confirmed_basis_snapshot',snapshot['revision']==2 and snapshot['confirmed'] and snapshot['basis']['SYN-SPEC-PB01-RevB-REC']['version']=='B')
                request['revision']=2;run=client.ok('POST',base+'/run',request);rid=run['run_id'];route='/api/ai-work/runs/'+rid;original=deepcopy(run)
                check('expected_initial_results',run['counts']==case['counts'] and run['pending_reviews']==12,counts=run['counts'])
                again=client.ok('POST',base+'/run',request);check('same_request_idempotent',again['run_id']==rid and len(client.ok('GET',base)['runs'])==1)
                source_cards={b['chunk_id']:b for i in run['items'] for b in i['basis']};sources_ok=True
                for cid,b in source_cards.items():
                    source=client.ok('GET','/api/source/'+cid);sources_ok &= source['excerpt']==b['text'] and source['version']==b['version'] and source['publication_status']=='active' and source['excerpt_kind'] in {'verbatim','index_summary'} and bool(source['original_excerpt']) and source['original_excerpt'] in source['original_text'] and b['section'].split()[0] in source['original_excerpt']
                check('knowledge_basis_source_lookup',sources_ok,basis_sources=len(source_cards))
                pages={p['source_id']:p for p in snapshot['report']['pages']};refs=[f for i in run['items'] for f in i['report_evidence']]
                check('report_refs_page_quote_hash',all(f['source_id'] in pages and f['quote'] in pages[f['source_id']]['text'] and f['page']==pages[f['source_id']]['page'] and f['sha256']==sha(blob) for f in refs),refs=len(refs))
                byid={i['item_id']:i for i in run['items']}
                if case['case_id']=='FLOW-02':
                    check('conditional_conflict_both_values',byid['A1-01']['conditional'] and byid['A1-01']['result']=='no_issue' and byid['SUMMARY-A1']['result']=='conflict' and any('0.683' in f['quote'] for f in byid['SUMMARY-A1']['report_evidence']) and any('283 ms' in f['quote'] for f in byid['SUMMARY-A1']['report_evidence']))
                if case['case_id']=='FLOW-03':
                    check('missing_not_claimed_untested',all(byid[i]['result']=='evidence_insufficient' and byid[i]['calculation'] is None and '不能据此推定未测试' in byid[i]['explanation'] for i in ['C1-04','C1-05']))
                first=run['items'][0]['item_id'];review=dict(item_id=first,version=0,disposition='confirmed',reason='')
                check('empty_review_reason_rejected',client.call('POST',route+'/review',review)[0]==400)
                review['reason']='流程验收模拟：验证确认保存，专业结论待人工核对。';client.ok('POST',route+'/review',review)
                check('stale_review_version_rejected',client.call('POST',route+'/review',review)[0]==409)
                review.update(version=1,disposition='excluded',reason='流程验收模拟：验证排除记录；原系统结果保持，专业结论待人工核对。');client.ok('POST',route+'/review',review)
                for item in run['items'][1:]:client.ok('POST',route+'/review',dict(item_id=item['item_id'],version=0,disposition='unresolved',reason='流程验收模拟：仅验证未决处置保存，专业结论待人工核对。'))
                run=client.ok('GET',route)
                check('all_reviewed_with_explicit_unresolved',run['pending_reviews']==0 and run['state']=='review_complete' and sum(i['review']['disposition']=='unresolved' for i in run['items'])==11)
                check('system_findings_unchanged_by_review',all({k:i.get(k) for k in ['item_id','result','calculation','conditional','report_evidence']}=={k:o.get(k) for k in ['item_id','result','calculation','conditional','report_evidence']} for i,o in zip(run['items'],original['items'],strict=True)))
                check('review_history_preserved',len(run['review_history'])==13 and [r['version'] for r in run['review_history'] if r['item_id']==first]==[1,2])
                exported=client.ok('GET',route+'/export',raw=True);verified=verify_export(exported,run)
                check('xlsx_matches_actual_run',all(v for k,v in verified.items() if k!='sheet_rows'),**verified)
                target=args.exports/(case['case_id']+'.xlsx');target.write_bytes(exported)
                result['cases'].append(dict(case_id=case['case_id'],path=case['path'],pdf_sha256=sha(blob),checks=checks,task_id=tid,run_id=rid,original=original,reviewed=run,
                    export=dict(path=str(target),sha256=sha(exported),validation=verified)))
            for case in result['cases']:
                task=client.ok('GET','/api/ai-work/tasks/'+case['task_id']);old=case['reviewed']
                case['checks'].append(dict(name='task_restore_run_mapping',passed=task['runs'][0]['run_id']==case['run_id']))
            first=result['cases'][0];base='/api/ai-work/tasks/'+first['task_id'];client.ok('POST',base+'/confirm',dict(revision=2,acknowledged=True,corrections={'A1:response':dict(value='0.137 s',reason='流程验收模拟：137 ms等价换算，验证原文与修正留存。')}))
            new=client.ok('POST',base+'/run',dict(revision=3,idempotency_key='FLOW-01-revision3-key'));old=client.ok('GET','/api/ai-work/runs/'+first['run_id'])
            first['checks'].append(dict(name='new_revision_preserves_old_run',passed=old['historical'] and old['pending_reviews']==0 and new['run_id']!=old['run_id'] and new['revision']==3 and new['pending_reviews']==12 and new['snapshot']['report']['fields']['A1:response'][0]['value']=='137 ms' and new['snapshot']['corrections']['A1:response']['value']=='0.137 s'))
            first['revision3_run']=new
        finally:stop(server,thread)
        server,thread=start(temp);client=Client(server)
        try:
            for case in result['cases']:
                loaded=client.ok('GET','/api/ai-work/runs/'+case['run_id']);case['checks'].append(dict(name='service_restart_persistence',passed=loaded['review_history']==case['reviewed']['review_history'] and loaded['counts']==case['reviewed']['counts'] and loaded['pending_reviews']==0))
        finally:stop(server,thread)
    checks=[c for r in result['cases'] for c in r['checks']];result['summary']=dict(cases=len(result['cases']),passed_cases=sum(all(c['passed'] for c in r['checks']) for r in result['cases']),checks=len(checks),passed_checks=sum(c['passed'] for c in checks),failed=[r['case_id']+':'+c['name'] for r in result['cases'] for c in r['checks'] if not c['passed']])
    result['source_sha256']={p:sha((ROOT/p).read_bytes()) for p in ['scripts/evaluate_workflow_acceptance.py','app/knowledge_assistant/static/work.js','app/knowledge_assistant/static/index.html','app/ai_work/review.py','app/ai_work/parsing.py','app/ai_work/export.py','app/knowledge_assistant/server.py']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['summary'],ensure_ascii=False));return not all(c['passed'] for c in checks)

if __name__=='__main__':sys.exit(main())
