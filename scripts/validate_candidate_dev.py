"""Audit development executions, source isolation and frozen material preservation."""
from collections import Counter
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.ai_work.candidate import digest
from scripts.rag_gain_scoring_v0_2 import score_r02


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True,type=Path);args=p.parse_args()
    if args.output.exists():p.error("拒绝覆盖核验记录。")
    def load(path):return json.loads((ROOT/path).read_text())
    def h(path):return sha256((ROOT/path).read_bytes()).hexdigest()
    checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    final=load("eval-results/candidate-dev-final-v0.4.json")
    protocol=load("data/ai-work-rag-gain-v0.2/protocol.json")
    for path,value in protocol["baseline"]["source_sha256"].items():check("baseline:"+path,h(path)==value)
    manifest=load("data/ai-work-rag-gain-dev-v0.1/material-manifest.json")
    for path,value in manifest["asset_sha256"].items():check("development_material:"+path,h(path)==value)
    for group in ["review-holdout-v0.1","p0-holdout-v0.1","p1-holdout-v0.1"]:
        for path,value in load("data/"+group+"/freeze.json")["asset_sha256"].items():check("frozen:"+path,h(path)==value)
    for path in ["data/ai-work-rag-gain-v0.2/protocol.json","data/ai-work-rag-gain-v0.2/cases.json","data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json","scripts/rag_gain_scoring_v0_2.py","output/packages/ai-work-rag-gain-dev-v0.1.zip"]:
        old=subprocess.check_output(["git","show","8f3be60761edde8e497095ab6aba95222b2b792d:"+path],cwd=ROOT)
        check("previous_contract_and_zip:"+path,sha256(old).hexdigest()==h(path))
    previous=subprocess.check_output(["git","ls-tree","-r","--name-only","8f3be60761edde8e497095ab6aba95222b2b792d","eval-results"],cwd=ROOT).decode().splitlines()
    for path in previous:
        old=subprocess.check_output(["git","show","8f3be60761edde8e497095ab6aba95222b2b792d:"+path],cwd=ROOT)
        check("historical_result:"+path,sha256(old).hexdigest()==h(path))
    for filename,ref in [("candidate-dev-first-v0.1.json","a7ac214"),("candidate-dev-routed-v0.2.json","2d862c6"),("candidate-dev-final-v0.3.json","8671707")]:
        r=load("eval-results/"+filename)
        for path,value in r["source_sha256"].items():
            check("traceable_source:"+filename+":"+path,sha256(subprocess.check_output(["git","show",ref+":"+path],cwd=ROOT)).hexdigest()==value)
    for path,value in final["source_sha256"].items():check("current_source:"+path,h(path)==value)
    check("final_12_pdf_and_4_offline",len(final["raw_application_runs"])==12 and len(final["offline"])==4)
    check("external_requests_zero",final["summary"]["external_requests"]==final["summary"]["model_generation_runs"]==final["summary"]["real_embedding_runs"]==0)
    check("producer_gold_denied",final["application_phase"]=="gold_denied_subprocess")
    check("202_full_tests",bool(re.search(r"Ran 202 tests.*\n\nOK",(ROOT/"eval-results/candidate-regression-v0.4.txt").read_text(),re.S)))
    check("35_candidate_tests",bool(re.search(r"Ran 35 tests.*\n\nOK",(ROOT/"eval-results/candidate-unit-tests-v0.4.txt").read_text(),re.S)))
    qrels=load("data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json")["rows"]
    gold={(q["report_id"],q["query_id"],q["namespace"]):q for q in qrels}
    scores={(x["row_id"],x["arm"]):x for x in final["scored_queries"]}
    check("496_scored_query_namespace_records",len(scores)==496)
    for case in final["raw_application_runs"]:
        check("immutable_a0:"+case["report_id"],case["original_payload_preserved"] and digest(case["baseline"])==case["original_payload_sha256"])
        corpus={c["chunk_id"]:c for c in [json.loads(l) for l in (ROOT/"data/ai-work-rag-gain-dev-v0.1/application-inputs"/case["report_id"]/"chunks.jsonl").read_text().splitlines()]}
        for query in case["queries"]:
            for arm,outputs in query["methods"].items():
                for ns,r in outputs.items():
                    q=gold[(case["report_id"],query["query_id"],ns)];key=q["row_id"]+":"+arm
                    expected=score_r02(q,r["raw_seeds"],corpus,arm=arm,negative_outcome=r["outcome"] if q["query_state"]=="no_available_evidence" else None)
                    check("r02_recomputed:"+key,expected==scores[(q["row_id"],arm)]["r02"])
                    check("ranking_integrity:"+key,len(r["raw_seeds"])<=5 and not expected.get("violations"))
                    check("source_and_network:"+key,r["trace"]["embedder_calls"]==r["trace"]["source_validation_rejections"]==0)
                    if arm=="A2":check("explicit_hybrid_degradation:"+key,r["effective_method"]=="bm25" and r["degradation"]=="embedding_not_configured")
    for f in final["offline"]:
        for name,value in f["checks"].items():check("offline:"+f["case_id"]+":"+name,value)
    gaps=[dict(row_id=x["row_id"],covered=x["groups_covered"],total=x["necessary_groups_total"],recall=x["recall"]) for x in final["scored_queries"] if x["arm"]=="A1" and x["recall"] is not None and x["recall"]<1]
    check("remaining_two_gaps_disclosed",len(gaps)==2 and all(x["row_id"].endswith(":requirement") for x in gaps))
    result=dict(kind="candidate_development_integrity_audit_not_holdout_acceptance",checks=checks,total=len(checks),passed=sum(x["passed"] for x in checks),failed=[x["name"] for x in checks if not x["passed"]],
        remaining_gaps=gaps,previous_result_files_preserved=len(previous),development_assets_preserved=len(manifest["asset_sha256"]),
        source_sha256=final["source_sha256"],result_sha256=h("eval-results/candidate-dev-final-v0.4.json"),
        external_requests=0,holdout_materialized=0,real_hybrid_quality="not_evaluated",candidate_freeze="pending_two_query_gaps_and_provider_preflight")
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["total","passed","failed","remaining_gaps","previous_result_files_preserved"]},ensure_ascii=False))
    if result["failed"]:raise SystemExit(1)


if __name__=="__main__":main()
