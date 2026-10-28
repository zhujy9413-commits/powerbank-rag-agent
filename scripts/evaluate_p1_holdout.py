"""Frozen first run: summary/ownership assertions in addition to immutable record scoring."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));PACK=ROOT/'data/p1-holdout-v0.1'
from scripts.evaluate_review_holdout import RUNNER,score,sha,git,normalize

def score_p1(case,actual):
    r=score(case,actual);report=actual.get('report',{});audit=report.get('parse_audit',{})
    summary=report.get('summary',[]);expected=Counter((i,p,normalize(v)) for i,p,v in case['expected_summaries'])
    got=Counter((s['record_id'],s['port'],normalize(s['value'])) for s in summary)
    owners=Counter((u['evidence']['page'],normalize(u['evidence']['quote']),u['owner_type'],u['owner_id']) for u in audit.get('unit_ownership',[]))
    expected_owners=Counter((p,normalize(q),k,i) for p,q,k,i in case['expected_unit_owners'])
    by_id={s['record_id']:s for s in summary};conditions=[]
    for rid,dims in case['expected_summary_conditions'].items():
        for key,value in dims.items():
            present=rid in by_id and key in by_id[rid]['conditions']
            conditions.append(dict(record_id=rid,key=key,expected=value,passed=present and by_id[rid]['conditions'][key]==value))
    codes={d['code'] for d in audit.get('issues',[])}
    orphan_keys=sorted({k for d in audit.get('issues',[]) if d['code']=='orphan_unit' for k in d['affected_keys']})
    pages={p['source_id']:p for p in report.get('pages',[])}
    fragments=[f for s in summary for f in s.get('fragments',[])+s.get('condition_evidence',[])]+[u['evidence'] for u in audit.get('unit_ownership',[])]
    quotes_ok=all(f['source_id'] in pages and f['page']==pages[f['source_id']]['page'] and f['quote'] in pages[f['source_id']]['text'] for f in fragments)
    extra=dict(summary_values=expected==got,unit_owners=expected_owners==owners,
        summary_conditions=all(c['passed'] for c in conditions),required_diagnostics=set(case['required_issue_codes'])<=codes,
        orphan_scope=orphan_keys==sorted(case['expected_orphan_keys']),fragment_quotes=quotes_ok)
    r.update(p1_checks=extra,summary_expected=list(expected.elements()),summary_actual=list(got.elements()),
        unit_owners_expected=list(expected_owners.elements()),unit_owners_actual=list(owners.elements()),summary_condition_checks=conditions,
        orphan_keys_actual=orphan_keys,fragment_count=len(fragments),passed=r['passed'] and all(extra.values()))
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():ap.error('拒绝覆盖首次结果。')
    path=PACK/'freeze.json';protocol=json.loads(path.read_text());head=git('rev-parse','HEAD').decode().strip()
    assert git('show',head+':data/p1-holdout-v0.1/freeze.json')==path.read_bytes(),'必须先提交冻结协议'
    for p,h in protocol['asset_sha256'].items():assert sha((ROOT/p).read_bytes())==h,p
    cases=json.loads((PACK/'cases.json').read_text())['cases']
    for c in cases:assert sha((ROOT/c['path']).read_bytes())==c['sha256'],c['case_id']
    with tempfile.TemporaryDirectory(prefix='powerbank-p1-heldout-') as temp:
        frozen=Path(temp);archive=git('archive',protocol['engine_git_ref'],'app','data/bootstrap-v0.1')
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(frozen,filter='data')
        p=frozen/'inputs.json';p.write_text(json.dumps([dict(case_id=c['case_id'],path=str(ROOT/c['path'])) for c in cases]))
        raw=json.loads(subprocess.run([sys.executable,'-c',RUNNER,str(p)],cwd=frozen,check=True,capture_output=True,text=True).stdout)
    assert raw['corpus_sha256']==protocol['corpus_sha256'] and raw['engine_sha256']==protocol['engine_sha256']
    assert [c['case_id'] for c in cases]==[r['case_id'] for r in raw['cases']]
    rows=[score_p1(c,a) for c,a in zip(cases,raw['cases'],strict=True)];checks=[x for r in rows for x in r['checks']]
    result=dict(version='p1-new-holdout-first-run-v0.1',evaluated_at=datetime.now(timezone.utc).isoformat(),freeze_commit=head,
        freeze_protocol_sha256=sha(path.read_bytes()),engine_git_ref=protocol['engine_git_ref'],engine_sha256=raw['engine_sha256'],
        corpus_sha256=raw['corpus_sha256'],engine_version=raw['engine_version'],parser_version=raw['parser_version'],model_requests=0,
        external_independence=False,blind_test=False,professional_review='pending',
        summary=dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failed_ids=[r['case_id'] for r in rows if not r['passed']],
            text_records=sum(r['text_expected'] for r in rows),matched_text_records=sum(r['text_matched'] for r in rows),extra_text_records=sum(len(r['text_extra']) for r in rows),
            behavioral_checks=len(checks),behavioral_checks_passed=sum(x['passed'] for x in checks),
            required_block_checks=sum(x['expected'].get('blocked',False) for x in checks),required_block_checks_passed=sum(x['passed'] for x in checks if x['expected'].get('blocked')),
            p1_checks=sum(len(r['p1_checks']) for r in rows),p1_checks_passed=sum(sum(r['p1_checks'].values()) for r in rows),
            unit_only_lines=sum(len(r['unit_owners_actual']) for r in rows),summary_condition_assertions=sum(len(r['summary_condition_checks']) for r in rows),
            unexpected_no_issue_units=sum(x['expected'].get('blocked',False) and x['actual'].get('result')=='no_issue' for x in checks),
            evidence_refs=sum(r['evidence_count'] for r in rows),evidence_all_valid=all(r['evidence_valid'] for r in rows),
            fragment_refs=sum(r['fragment_count'] for r in rows),fragment_refs_all_valid=all(r['p1_checks']['fragment_quotes'] for r in rows)),cases=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
