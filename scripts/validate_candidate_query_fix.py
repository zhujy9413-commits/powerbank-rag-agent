"""Audit the two-query repair against the preserved v0.4 development execution."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ai_work.candidate import digest
from scripts.rag_gain_scoring_v0_2 import score_r02

BASELINE="18e9833f71328ba682fefd62a9f4bfae89505354"
RESULT="eval-results/candidate-query-fix-dev-v0.5.json"


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True,type=Path);args=p.parse_args()
    if args.output.exists():p.error("拒绝覆盖已有核验记录。")
    def load(path):return json.loads((ROOT/path).read_text())
    def h(path):return sha256((ROOT/path).read_bytes()).hexdigest()
    checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    before=load("eval-results/candidate-dev-final-v0.4.json");after=load(RESULT)
    protocol=load("data/ai-work-rag-gain-v0.2/protocol.json")
    for path,value in protocol["baseline"]["source_sha256"].items():check("locked_baseline:"+path,h(path)==value)
    material=load("data/ai-work-rag-gain-dev-v0.1/material-manifest.json")
    for path,value in material["asset_sha256"].items():check("dev_asset:"+path,h(path)==value)
    for group in ["review-holdout-v0.1","p0-holdout-v0.1","p1-holdout-v0.1"]:
        for path,value in load("data/"+group+"/freeze.json")["asset_sha256"].items():check("prior_frozen:"+path,h(path)==value)
    immutable=["data/ai-work-rag-gain-v0.2/protocol.json","data/ai-work-rag-gain-v0.2/cases.json","data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json","scripts/rag_gain_scoring_v0_2.py","output/packages/ai-work-rag-gain-dev-v0.1.zip"]
    previous=subprocess.check_output(["git","ls-tree","-r","--name-only",BASELINE,"eval-results"],cwd=ROOT).decode().splitlines()
    for path in immutable+previous:
        saved=subprocess.check_output(["git","show",BASELINE+":"+path],cwd=ROOT)
        check("unchanged_history:"+path,h(path)==sha256(saved).hexdigest())
    for path,value in after["source_sha256"].items():check("executed_source:"+path,h(path)==value)
    for log,count in [("eval-results/candidate-query-fix-regression-v0.5.txt",212),("eval-results/candidate-query-fix-tests-v0.5.txt",45)]:
        check("test_log:"+log,bool(re.search(r"Ran "+str(count)+r" tests.*\n\nOK",(ROOT/log).read_text(),re.S)))
    check("12_actual_pdf_4_offline",len(after["raw_application_runs"])==12 and len(after["offline"])==4 and all(f["passed"] for f in after["offline"]))
    check("gold_denied_producer",after["application_phase"]=="gold_denied_subprocess")
    check("no_external_or_real_model_runs",after["summary"]["external_requests"]==after["summary"]["real_embedding_runs"]==after["summary"]["model_generation_runs"]==0)
    old_scores={(r["row_id"],r["arm"]):r for r in before["scored_queries"]}
    new_scores={(r["row_id"],r["arm"]):r for r in after["scored_queries"]}
    check("fixed_496_rows",len(new_scores)==496 and new_scores.keys()==old_scores.keys())
    gaps={r["row_id"] for r in before["scored_queries"] if r["arm"]=="A1" and r["recall"] is not None and r["recall"]<1}
    check("exactly_two_original_gaps",len(gaps)==2)
    for ident in sorted(gaps):
        for arm in ["A1","A2"]:
            r=new_scores[(ident,arm)]
            check("gap_closed:"+ident+":"+arm,r["groups_covered"]==r["necessary_groups_total"]==2 and r["r02"]["score"]==1)
    gold={(q["report_id"],q["query_id"],q["namespace"]):q for q in load("data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json")["rows"]}
    old_cases={c["report_id"]:c for c in before["raw_application_runs"]}
    business=("items","counts","configured_units","unconfigured","parse_audit","retrieval_trace")
    for case in after["raw_application_runs"]:
        old_case=old_cases[case["report_id"]]
        check("original_preserved:"+case["report_id"],case["original_payload_preserved"] and digest(case["baseline"])==case["original_payload_sha256"])
        check("same_a0_business_payload:"+case["report_id"],all(case["baseline"].get(k)==old_case["baseline"].get(k) for k in business))
        corpus={c["chunk_id"]:c for c in [json.loads(l) for l in (ROOT/"data/ai-work-rag-gain-dev-v0.1/application-inputs"/case["report_id"]/"chunks.jsonl").read_text().splitlines()]}
        old_queries={q["query_id"]:q for q in old_case["queries"]}
        check("same_query_list:"+case["report_id"],set(old_queries)=={q["query_id"] for q in case["queries"]})
        for q in case["queries"]:
            for arm,outputs in q["methods"].items():
                for ns,r in outputs.items():
                    g=gold[(case["report_id"],q["query_id"],ns)];key=g["row_id"]+":"+arm
                    recalculated=score_r02(g,r["raw_seeds"],corpus,arm=arm,negative_outcome=r["outcome"] if g["query_state"]=="no_available_evidence" else None)
                    check("r02_recomputed:"+key,recalculated==new_scores[(g["row_id"],arm)]["r02"] and not recalculated.get("violations"))
                    check("original_source_and_no_embedding:"+key,r["trace"]["source_validation_rejections"]==r["trace"]["embedder_calls"]==0)
                    if g["row_id"] not in gaps:
                        old_r=old_queries[q["query_id"]]["methods"][arm][ns]
                        check("unaffected_output_identical:"+key,all(r[k]==old_r[k] for k in ["raw_seeds","context_expansions","accepted","rejected","outcome"]))
                    if arm=="A2":check("a2_explicit_keyword_degradation:"+key,r["effective_method"]=="bm25" and r["degradation"]=="embedding_not_configured")
    check("all_positive_groups_covered",all(r["recall"]==1 for r in after["scored_queries"] if r["recall"] is not None))
    check("three_negative_queries_preserved",all(after["r02"][a]["report"]["negative_correct"]==3 for a in ["A1","A2"]))
    check("no_case_ids_in_application",not any(x in (ROOT/"app/ai_work/candidate.py").read_text() for x in ["RG-GAP-DEV-02","RG-NOISE-DEV-02","SPEC-VERSION","BACKGROUND-CONSISTENCY"]))
    for fixture in after["offline"]:
        for name,value in fixture["checks"].items():check("offline:"+fixture["case_id"]+":"+name,value)
    result=dict(kind="query_fix_development_regression_integrity_not_holdout",checks=checks,total=len(checks),passed=sum(x["passed"] for x in checks),failed=[x["name"] for x in checks if not x["passed"]],
        previous_commit=BASELINE,previous_result_files_preserved=len(previous),development_assets_preserved=len(material["asset_sha256"]),
        fixed_queries=[dict(row_id=i,before_recall=old_scores[(i,"A1")]["recall"],after_recall=new_scores[(i,"A1")]["recall"],after_precision=new_scores[(i,"A1")]["r02"]["score"]) for i in sorted(gaps)],
        remaining_positive_group_gaps=[r["row_id"] for r in after["scored_queries"] if r["arm"]=="A1" and r["recall"] is not None and r["recall"]<1],
        source_sha256=after["source_sha256"],result_sha256=h(RESULT),external_requests=0,holdout_materialized=0,candidate_freeze="not_frozen_real_vector_and_professional_review_pending")
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["total","passed","failed","fixed_queries","previous_result_files_preserved"]},ensure_ascii=False))
    if result["failed"]:raise SystemExit(1)


if __name__=="__main__":main()
