"""First-run held-out scoring. Execute only archived production code in a child process."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'data/review-holdout-v0.1'

def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True).stdout
def normalize(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def key(row):return tuple(row[:3])+ (normalize(row[3]),)

# This child receives file paths and IDs only, never expectations or labels.
RUNNER=r'''
import json,sys
from pathlib import Path
from app.ai_work.review import parse_pdf,evaluate,basis_catalog,ENGINE_SHA256,VERSION
from app.ai_work.parsing import PARSER_VERSION
from app.knowledge_assistant.core import Corpus,Principal
c=Corpus();b=basis_catalog(c,Principal('frozen-holdout','engineer',('DEMO-TASK-001',)))
out=[]
for entry in json.loads(Path(sys.argv[1]).read_text()):
    p=Path(entry['path']);row={'case_id':entry['case_id']}
    try:
        r=parse_pdf(p.read_bytes(),p.name);raw=evaluate({'report':r,'corrections':{}},b)
        row.update(parsed=True,report=r,review=raw)
    except Exception as e:row.update(parsed=False,error_type=type(e).__name__,error=str(e))
    out.append(row)
print(json.dumps({'engine_sha256':ENGINE_SHA256,'engine_version':VERSION,'parser_version':PARSER_VERSION,
    'corpus_sha256':c.digest,'cases':out},ensure_ascii=False))
'''

def score(case,actual):
    expected=Counter(key(r) for r in case['expected_text_records']) if case.get('records_for_metric',True) else Counter()
    extracted=[(r['record_id'],r['port'],r['kind'],r['value']) for rows in actual.get('report',{}).get('fields',{}).values() for r in rows]
    got=Counter(key(r) for r in extracted);matched=expected&got
    checks=[];byid={i['item_id']:i for i in actual.get('review',{}).get('items',[])}
    for e in case['checks']:
        item=byid.get(e['item_id'],{});ok=bool(item)
        for prop in ['result','execution','conditional']:
            if prop in e:ok=ok and item.get(prop)==e[prop]
        if e.get('blocked'):ok=ok and item.get('result') not in {None,'no_issue','nonconformity','conflict'} and item.get('calculation') is None
        checks.append(dict(expected=e,passed=ok,actual={k:item.get(k) for k in ['result','execution','conditional','calculation','record_ids']}))
    audit=actual.get('report',{}).get('parse_audit',{})
    visible=bool(audit.get('issues')) and audit.get('coverage_status')=='needs_review'
    # No dropping failed files from denominators; no accepting arbitrary exceptions as valid rejection.
    rejection_ok=not actual['parsed'] and actual.get('error_type')=='ValueError' and '加密' in actual.get('error','')
    extraction_ok=not (expected-got) and not (got-expected)
    passed=rejection_ok if case['expected_reject'] else actual['parsed'] and all(c['passed'] for c in checks) and (visible or not case['visible_issue_required']) and (extraction_ok or not case['capture_required'])
    # Verify reference bytes/page/hash against the *same* actual PDF, independent of verdict labels.
    pages={p['source_id']:p for p in actual.get('report',{}).get('pages',[])}
    refs=[ref for i in byid.values() for ref in i.get('report_evidence',[])]
    evidence_ok=all(ref['source_id'] in pages and ref['quote'] in pages[ref['source_id']]['text'] and ref['page']==pages[ref['source_id']]['page'] and ref['sha256']==case['sha256'] for ref in refs)
    return dict(case_id=case['case_id'],title=case['title'],passed=bool(passed and evidence_ok),parsed=actual['parsed'],
        text_expected=sum(expected.values()),text_matched=sum(matched.values()),text_missing=list((expected-got).elements()),
        text_extra=list((got-expected).elements()),visual_records=sum(1 for _ in case['expected_visual_records']),
        capture_required=case['capture_required'],visible_issue_required=case['visible_issue_required'],visible_issue=visible,
        checks=checks,evidence_count=len(refs),evidence_valid=evidence_ok,actual=actual)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():ap.error('拒绝覆盖首次结果。')
    protocol_path=PACK/'freeze.json';protocol=json.loads(protocol_path.read_text())
    head=git('rev-parse','HEAD').decode().strip()
    if git('show',head+':data/review-holdout-v0.1/freeze.json')!=protocol_path.read_bytes():raise SystemExit('先提交冻结协议，再运行评测。')
    for p,h in protocol['asset_sha256'].items():
        if sha((ROOT/p).read_bytes())!=h:raise SystemExit('冻结资产发生改变：'+p)
    cases=json.loads((PACK/'cases.json').read_text())['cases']
    for c in cases:
        if sha((ROOT/c['path']).read_bytes())!=c['sha256']:raise SystemExit('PDF摘要不符：'+c['case_id'])
    with tempfile.TemporaryDirectory(prefix='powerbank-frozen-holdout-') as temp:
        frozen=Path(temp)
        archive=git('archive',protocol['engine_git_ref'],'app','data/bootstrap-v0.1')
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(frozen,filter='data')
        inputs=frozen/'inputs.json';inputs.write_text(json.dumps([dict(case_id=c['case_id'],path=str(ROOT/c['path'])) for c in cases]))
        process=subprocess.run([sys.executable,'-c',RUNNER,str(inputs)],cwd=frozen,check=True,capture_output=True,text=True)
        raw=json.loads(process.stdout)
    if raw['corpus_sha256']!=protocol['corpus_sha256']:raise SystemExit('冻结语料摘要不符。')
    if [c['case_id'] for c in cases]!=[a['case_id'] for a in raw['cases']]:raise SystemExit('冻结引擎输出顺序或覆盖不符。')
    rows=[score(c,a) for c,a in zip(cases,raw['cases'],strict=True)]
    checks=[x for r in rows for x in r['checks']]
    output=dict(version='review-holdout-first-run-v0.1',evaluated_at=datetime.now(timezone.utc).isoformat(),freeze_commit=head,
        freeze_protocol_sha256=sha(protocol_path.read_bytes()),engine_git_ref=protocol['engine_git_ref'],
        engine_sha256=raw['engine_sha256'],engine_version=raw['engine_version'],parser_version=raw['parser_version'],
        corpus_sha256=raw['corpus_sha256'],model_requests=0,external_independence=False,blind_test=False,professional_review='pending',
        summary=dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failed_ids=[r['case_id'] for r in rows if not r['passed']],
            text_records=sum(r['text_expected'] for r in rows),matched_text_records=sum(r['text_matched'] for r in rows),
            extra_records=sum(len(r['text_extra']) for r in rows),visual_records=sum(r['visual_records'] for r in rows),
            behavioral_checks=len(checks),behavioral_checks_passed=sum(c['passed'] for c in checks),
            required_block_checks=sum(c['expected'].get('blocked',False) for c in checks),
            required_block_checks_passed=sum(c['passed'] for c in checks if c['expected'].get('blocked')),
            required_visible_issues=sum(r['visible_issue_required'] for r in rows),
            required_visible_issues_found=sum(r['visible_issue'] for r in rows if r['visible_issue_required']),
            evidence_refs=sum(r['evidence_count'] for r in rows),evidence_all_valid=all(r['evidence_valid'] for r in rows)),cases=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(output['summary'],ensure_ascii=False))

if __name__=='__main__':main()
