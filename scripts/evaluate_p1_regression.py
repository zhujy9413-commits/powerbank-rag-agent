"""Consumed P0 dataset and explicitly separate HO-17 adjudication; never relabel old data."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ai_work.review import parse_pdf,evaluate,basis_catalog,ENGINE_SHA256,stamp
from app.knowledge_assistant.core import Corpus,Principal
from scripts.evaluate_review_holdout import score,sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():ap.error('拒绝覆盖历史结果。')
    basis=basis_catalog(Corpus(),Principal('consumed-p1-regression','engineer',('DEMO-TASK-001',)))
    def run(c):
        p=ROOT/c['path'];assert sha(p.read_bytes())==c['sha256'];r=parse_pdf(p.read_bytes(),p.name)
        return dict(case_id=c['case_id'],parsed=True,report=r,review=evaluate(dict(report=r,corrections={}),basis))
    rows=[score(c,run(c)) for c in json.loads((ROOT/'data/p0-holdout-v0.1/cases.json').read_text())['cases']]
    c=json.loads((ROOT/'data/review-holdout-v0.1/cases.json').read_text())['cases'][16];actual=run(c)
    r=actual['report'];by={i['item_id']:i for i in actual['review']['items']}
    checks=dict(summary_value=r['summary'][0]['value']=='0.137 s',summary_consistent=by['SUMMARY-A1']['result']=='no_issue',
        method_not_falsely_blocked=by['A1-05']['result']=='no_issue' and by['A1-05']['execution']=='completed',
        no_orphan_diagnostic=not any(i['code']=='orphan_unit' for i in r['parse_audit']['issues']),
        unit_belongs_to_summary=any(u['owner_type']=='summary' and u['owner_id']=='S41' for u in r['parse_audit']['unit_ownership']))
    allchecks=[ch for row in rows for ch in row['checks']]
    result=dict(version='p1-consumed-regression-v0.1',evaluated_at=stamp(),dataset_status='consumed_development_regression',
        independent_test=False,engine_sha256=ENGINE_SHA256,model_requests=0,
        summary=dict(p0_cases=len(rows),p0_passed=sum(r['passed'] for r in rows),p0_behavior_checks=len(allchecks),
            p0_behavior_passed=sum(ch['passed'] for ch in allchecks),ho17_corrected_checks=len(checks),ho17_corrected_passed=sum(checks.values())),
        ho17_adjudication=dict(reason='原标签要求SUMMARY-MISSING过窄；不改旧标签和首次12/20。修复以正确提取及不误绑单位单列核验。',
            checks=checks,old_frozen_score=score(c,actual),actual=actual),p0_cases=rows)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
