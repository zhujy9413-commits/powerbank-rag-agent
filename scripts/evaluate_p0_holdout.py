"""Frozen post-fix first run; labels remain outside the archived runtime process."""
import argparse
from datetime import datetime,timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.evaluate_review_holdout import RUNNER,score,sha,git
PACK=ROOT/'data/p0-holdout-v0.1'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():ap.error('拒绝覆盖首次结果。')
    protocol_path=PACK/'freeze.json';protocol=json.loads(protocol_path.read_text());head=git('rev-parse','HEAD').decode().strip()
    assert git('show',head+':data/p0-holdout-v0.1/freeze.json')==protocol_path.read_bytes(),'必须先提交冻结协议'
    for p,h in protocol['asset_sha256'].items():assert sha((ROOT/p).read_bytes())==h,p
    cases=json.loads((PACK/'cases.json').read_text())['cases']
    for c in cases:assert sha((ROOT/c['path']).read_bytes())==c['sha256'],c['case_id']
    with tempfile.TemporaryDirectory(prefix='powerbank-p0-heldout-') as temp:
        frozen=Path(temp);archive=git('archive',protocol['engine_git_ref'],'app','data/bootstrap-v0.1')
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(frozen,filter='data')
        p=frozen/'inputs.json';p.write_text(json.dumps([dict(case_id=c['case_id'],path=str(ROOT/c['path'])) for c in cases]))
        run=subprocess.run([sys.executable,'-c',RUNNER,str(p)],cwd=frozen,check=True,capture_output=True,text=True);raw=json.loads(run.stdout)
    assert raw['corpus_sha256']==protocol['corpus_sha256']
    assert [c['case_id'] for c in cases]==[r['case_id'] for r in raw['cases']]
    rows=[]
    for c,a in zip(cases,raw['cases'],strict=True):
        r=score(c,a);visual=[p.get('visual_audit',{}) for p in a.get('report',{}).get('pages',[])]
        count=sum(v.get('image_draws') or 0 for v in visual)
        r['image_draws_expected']=c['image_draws_expected'];r['image_draws_actual']=count
        r['visual_operator_check']=a['parsed'] and len(visual)==2 and not any(v.get('status')=='inspection_failed' for v in visual) and count==c['image_draws_expected']
        r['passed']=r['passed'] and r['visual_operator_check'];rows.append(r)
    checks=[x for r in rows for x in r['checks']]
    result=dict(version='p0-new-holdout-first-run-v0.1',evaluated_at=datetime.now(timezone.utc).isoformat(),freeze_commit=head,
        freeze_protocol_sha256=sha(protocol_path.read_bytes()),engine_git_ref=protocol['engine_git_ref'],engine_sha256=raw['engine_sha256'],
        corpus_sha256=raw['corpus_sha256'],engine_version=raw['engine_version'],parser_version=raw['parser_version'],
        model_requests=0,external_independence=False,blind_test=False,professional_review='pending',
        summary=dict(cases=len(rows),passed=sum(r['passed'] for r in rows),failed_ids=[r['case_id'] for r in rows if not r['passed']],
            expected_text_records=sum(r['text_expected'] for r in rows),matched_text_records=sum(r['text_matched'] for r in rows),
            extra_text_records=sum(len(r['text_extra']) for r in rows),visual_records=sum(r['visual_records'] for r in rows),
            behavioral_checks=len(checks),behavioral_checks_passed=sum(x['passed'] for x in checks),
            required_block_checks=sum(x['expected'].get('blocked',False) for x in checks),
            required_block_checks_passed=sum(x['passed'] for x in checks if x['expected'].get('blocked')),
            unexpected_no_issue_units=sum(x['expected'].get('blocked',False) and x['actual'].get('result')=='no_issue' for x in checks),
            diagnostic_cases=sum(r['visible_issue_required'] for r in rows),diagnostic_cases_passed=sum(r['visible_issue'] for r in rows if r['visible_issue_required']),
            visual_operator_checks=sum(r['visual_operator_check'] for r in rows),evidence_refs=sum(r['evidence_count'] for r in rows),
            evidence_all_valid=all(r['evidence_valid'] for r in rows)),cases=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
