"""Re-score consumed holdout v0.1 as development regression; never call it independent."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ai_work.review import parse_pdf,evaluate,basis_catalog,ENGINE_SHA256,stamp
from app.knowledge_assistant.core import Corpus,Principal
from scripts.evaluate_review_holdout import score

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists():ap.error('拒绝覆盖历史结果。')
    cases=json.loads((ROOT/'data/review-holdout-v0.1/cases.json').read_text())['cases']
    basis=basis_catalog(Corpus(),Principal('consumed-p0-regression','engineer',('DEMO-TASK-001',)));out=[]
    for case in cases:
        path=ROOT/case['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==case['sha256']
        actual=dict(case_id=case['case_id'])
        try:
            report=parse_pdf(path.read_bytes(),path.name)
            actual.update(parsed=True,report=report,review=evaluate(dict(report=report,corrections={}),basis))
        except Exception as exc:actual.update(parsed=False,error_type=type(exc).__name__,error=str(exc))
        out.append(score(case,actual))
    target=[c for c in out if c['case_id'] in {'HO-04','HO-05','HO-07','HO-08','HO-09'}]
    result=dict(version='p0-consumed-development-regression-v0.1',evaluated_at=stamp(),dataset_status='consumed_development_regression',
        independent_test=False,model_requests=0,engine_sha256=ENGINE_SHA256,
        original_first_result_sha256=hashlib.sha256((ROOT/'eval-results/review-holdout-first-run-v0.1.json').read_bytes()).hexdigest(),
        summary=dict(cases=len(out),passed=sum(c['passed'] for c in out),failed_ids=[c['case_id'] for c in out if not c['passed']],
            p0_target_cases=len(target),p0_target_passed=sum(c['passed'] for c in target),
            expected_text_records=sum(c['text_expected'] for c in out),matched_text_records=sum(c['text_matched'] for c in out),
            unexpected_no_issue_units=sum(1 for c in out for x in c['checks'] if x['expected'].get('blocked') and x['actual'].get('result')=='no_issue')),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['app/ai_work/review.py','app/ai_work/parsing.py','scripts/evaluate_p0_regression.py']},cases=out)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
