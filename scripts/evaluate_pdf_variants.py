"""Score real PDF extraction and conservative condition gates; labels are scoring-only."""
from collections import Counter
import argparse
import hashlib
import json
import importlib.util
from pathlib import Path
import sys
import re
import subprocess
import tempfile
import unicodedata

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ai_work.review import parse_pdf,evaluate,basis_catalog,stamp,digest
from app.knowledge_assistant.core import Corpus,Principal

def normalize(s):return ''.join(unicodedata.normalize('NFKC',s).split())
FIELDS={'保护响应':'response','恢复电压':'recovery','壳温起值/末值':'temperature','外观观察':'appearance','恢复方式':'method'}

def run_cases(engine=None):
    manifest=ROOT/'data/pdf-variants-v0.1/cases.json'
    cases=json.loads(manifest.read_text())['cases'];corpus=Corpus();principal=Principal('variant-eval','engineer',('DEMO-TASK-001',))
    basis=basis_catalog(corpus,principal);output=[]
    parse=engine.parse_pdf if engine else parse_pdf
    compare=engine.evaluate if engine else evaluate
    for case in cases:
        path=ROOT/case['path'];blob=path.read_bytes();assert digest(blob)==case['sha256'],str(path)
        result=dict(case_id=case['case_id'],title=case['title'],path=case['path'],pdf_sha256=digest(blob),expected_reject=case['expected_reject'])
        try:
            report=parse(blob,path.name)
            raw=compare(dict(report=report,corrections={}),basis)
            by_id={i['item_id']:i for i in raw['items']}
            expected=Counter((r[0],r[1],FIELDS[r[2]],normalize(r[3])) for r in case['expected_records'])
            actual=Counter((r['record_id'],r['port'],r['kind'],normalize(r['value'])) for rows in report['fields'].values() for r in rows)
            matched=sum((expected&actual).values());missing=list((expected-actual).elements());extra=list((actual-expected).elements())
            checks={key:by_id.get(key,{}).get('result')==value for key,value in case['item_expectations'].items()}
            blocked={key:(by_id.get(key,{}).get('result') not in {None,'no_issue','nonconformity'} and by_id.get(key,{}).get('calculation') is None) for key in case['expected_blocked']}
            issue_ok=not case['expected_issue'] or bool(report.get('parse_audit',{}).get('issues'))
            result.update(parsed=True,record_expected=sum(expected.values()),record_matched=matched,missing_records=missing,extra_records=extra,
                item_checks=checks,condition_block_checks=blocked,issue_visible=issue_ok,report=report,raw_review=raw,
                passed=not case['expected_reject'] and not missing and not extra and all(checks.values()) and all(blocked.values()) and issue_ok)
        except Exception as exc:
            result.update(parsed=False,error_type=type(exc).__name__,error=str(exc),passed=case['expected_reject'])
        output.append(result)
    source_paths=['app/knowledge_assistant/core.py','scripts/evaluate_pdf_variants.py']
    if not engine:source_paths+=['app/ai_work/review.py','app/ai_work/parsing.py','app/ai_work/export.py','app/knowledge_assistant/static/work.js','tests/test_pdf_variants.py']
    source_hashes={p:digest((ROOT/p).read_bytes()) for p in source_paths}
    if engine:source_hashes['baseline_review.py']=digest(Path(engine.__file__).read_bytes())
    return dict(version='pdf-variants-evaluation-v0.1',evaluated_at=stamp(),source_sha256=source_hashes,
        manifest_sha256=digest(manifest.read_bytes()),professional_review='pending',independent_test=False,model_requests=0,
        summary=dict(cases=len(output),passed=sum(c['passed'] for c in output),failed_ids=[c['case_id'] for c in output if not c['passed']],
            parsed=sum(c['parsed'] for c in output),expected_records=sum(c.get('record_expected',0) for c in output),
            fixed_expected_text_records=sum(len(c['expected_records']) for c in cases if not c['expected_reject']),
            fixed_expected_block_checks=sum(len(c['expected_blocked']) for c in cases),
            matched_records=sum(c.get('record_matched',0) for c in output),
            expected_block_checks=sum(len(c.get('condition_block_checks',{})) for c in output),
            correct_block_checks=sum(sum(c.get('condition_block_checks',{}).values()) for c in output)),cases=output)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--baseline-ref');args=parser.parse_args()
    if args.output.exists():parser.error('拒绝覆盖历史结果。')
    if args.baseline_ref:
        if not re.fullmatch(r'[a-f0-9]{7,40}',args.baseline_ref):parser.error('基线必须使用明确提交SHA。')
        source=subprocess.run(['git','show',args.baseline_ref+':app/ai_work/review.py'],cwd=ROOT,check=True,capture_output=True).stdout
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'baseline_review.py';path.write_bytes(source)
            spec=importlib.util.spec_from_file_location('baseline_review',path);engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
            result=run_cases(engine);result['baseline_ref']=args.baseline_ref
    else:result=run_cases()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['summary'],ensure_ascii=False))

if __name__=='__main__':main()
