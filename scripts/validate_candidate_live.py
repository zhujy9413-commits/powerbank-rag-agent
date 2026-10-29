"""Recompute paired live development results and audit immutable inputs/lineage."""
import argparse
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BASELINE="5dffbb54b4c622ec347215415b7fcb418703b55d"
RESULT="eval-results/candidate-live-dev-v0.1.json"


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True,type=Path);args=p.parse_args()
    if args.output.exists():p.error("require_new_output_path")
    def load(path):return json.loads((ROOT/path).read_text())
    def h(path):return sha256((ROOT/path).read_bytes()).hexdigest()
    checks=[]
    def check(name,value):checks.append(dict(name=name,passed=bool(value)))
    from app.ai_work.candidate import CandidateRetriever,digest,rrf
    from app.ai_work.candidate_inputs import load_input
    from app.knowledge_assistant.core import Principal
    from scripts.evaluate_candidate_dev import evaluate
    after=load(RESULT);before=load("eval-results/candidate-query-fix-dev-v0.5.json")
    snapshot=load("data/ai-work-candidate-live-v0.1/execution-snapshot.json")
    material=load("data/ai-work-rag-gain-dev-v0.1/material-manifest.json")
    protocol=load("data/ai-work-rag-gain-v0.2/protocol.json")
    for group,assets in [("execution_snapshot",snapshot["asset_sha256"]),("executed_source",after["source_sha256"]),
                         ("locked_baseline",protocol["baseline"]["source_sha256"]),("dev_material",material["asset_sha256"])]:
        for path,value in assets.items():check(group+":"+path,h(path)==value)
    frozen_count=0
    for group in ["review-holdout-v0.1","p0-holdout-v0.1","p1-holdout-v0.1"]:
        for path,value in load("data/"+group+"/freeze.json")["asset_sha256"].items():
            check("prior_frozen:"+path,h(path)==value);frozen_count+=1
    history=subprocess.check_output(["git","ls-tree","-r","--name-only",BASELINE,"eval-results"],cwd=ROOT).decode().splitlines()
    locked=["data/ai-work-rag-gain-v0.2/protocol.json","data/ai-work-rag-gain-v0.2/cases.json","data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json",
            "scripts/rag_gain_scoring_v0_2.py","output/packages/ai-work-rag-gain-dev-v0.1.zip",
            "app/ai_work/candidate.py","app/ai_work/candidate_inputs.py","scripts/evaluate_candidate_dev.py"]
    for path in history+locked:
        saved=subprocess.check_output(["git","show",BASELINE+":"+path],cwd=ROOT)
        check("history_unchanged:"+path,h(path)==sha256(saved).hexdigest())
    with patch("socket.socket",side_effect=AssertionError("audit_network_forbidden")):
        recomputed=evaluate(dict(cases=after["raw_application_runs"]))
    for key in ["r01","r02","scored_queries"]:
        check("independent_recalculation:"+key,recomputed[key]==after[key])
    # The role fixture's two surfaces expose the same measured wall-clock
    # duration. Re-execution must preserve behavior, not reproduce this timer.
    # Remove only these two explicitly named measurements; virtual deadline
    # values, timeout outcomes, attempts and all other fixture fields stay exact.
    def comparable_offline(value):
        # JSON round-trip also matches the persisted representation: in-memory
        # fixture surfaces can share a trace dict while JSON has two copies.
        value=json.loads(json.dumps(value))
        row=next(f for f in value if f["case_id"]=="RG-OPS-DEV-01")
        surfaces=row["actual"]["surfaces"]
        del surfaces["application_log"]["elapsed_ms"]
        del surfaces["export"]["trace"]["elapsed_ms"]
        return value
    check("independent_recalculation:offline_except_two_measured_timers",comparable_offline(recomputed["offline"])==comparable_offline(after["offline"]))
    check("all_16_original_scenarios_executed",len(after["raw_application_runs"])==12 and len(after["offline"])==4 and all(f["passed"] for f in after["offline"]))
    check("live_completed_without_degradation",after["summary"]["completed"] and not after["summary"]["unexpected_degradations"])
    check("gold_denied_process",after["application_phase"]=="gold_denied_subprocess")
    check("225_regression_tests",bool(re.search(r"Ran 225 tests.*\n\nOK",(ROOT/"eval-results/candidate-live-regression-v0.1.txt").read_text(),re.S)))
    old_cases={c["report_id"]:c for c in before["raw_application_runs"]}
    ledger=after["ledger"];records={r["sequence"]:r for r in ledger["records"]};used=set();query_sequences=set();doc_sequences=set()
    business=("items","counts","configured_units","unconfigured","parse_audit","retrieval_trace")
    comparison=[];performance=[];report_completeness=[]
    scores={(r["row_id"],r["arm"]):r for r in after["scored_queries"]}
    gold={(r["report_id"],r["query_id"],r["namespace"]):r for r in load("data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json")["rows"]}
    for case in after["raw_application_runs"]:
        rid=case["report_id"];old=old_cases[rid]
        task,chunks,originals=load_input(ROOT/"data/ai-work-rag-gain-dev-v0.1/application-inputs"/rid,ROOT)
        task["selected_versions"]={i:c["version"] for i,c in case["baseline"]["snapshot"]["basis"].items()}
        retriever=CandidateRetriever(chunks,task,Principal("audit","engineer",(task["task_id"],)),originals)
        check("a0_immutable:"+rid,case["original_payload_preserved"] and digest(case["baseline"])==case["original_payload_sha256"])
        check("a0_business_identical:"+rid,all(case["baseline"][k]==old["baseline"][k] for k in business))
        check("query_list_identical:"+rid,[q["query_id"] for q in case["queries"]]==[q["query_id"] for q in old["queries"]])
        oldq={q["query_id"]:q for q in old["queries"]};elapsed={arm:0 for arm in ["A1","A2"]}
        case_scores={arm:[] for arm in elapsed}
        for q in case["queries"]:
            for ns in ["requirement","report"]:
                a1=q["methods"]["A1"][ns];a2=q["methods"]["A2"][ns];ident=gold[(rid,q["query_id"],ns)]["row_id"]
                check("a1_output_identical:"+ident,all(a1[k]==oldq[q["query_id"]]["methods"]["A1"][ns][k] for k in ["raw_seeds","context_expansions","accepted","rejected","outcome"]))
                check("paired_route_and_query_identical:"+ident,all(a1["trace"][k]==a2["trace"][k] for k in ["retrieval_text","query_plan","corpus_sha256","candidate_count","keyword_ranking","filtered_count","upstream_routing_exclusions"]))
                check("a1_no_external_requests:"+ident,not a1["live_request_sequences"] and a1["trace"]["embedder_calls"]==0)
                if a2["trace"]["candidate_count"]:
                    check("real_hybrid:"+ident,a2["effective_method"]=="bm25_embedding_rrf" and a2["degradation"] is None and a2["trace"]["embedding_model_identity"]=="text-embedding-v4" and bool(a2["trace"]["vector_ranking"]))
                    kw=[x["chunk_id"] for x in a2["trace"]["keyword_ranking"]]
                    vec=[x["chunk_id"] for x in a2["trace"]["vector_ranking"]]
                    order,_=rrf(kw,vec,60)
                    check("rrf_recomputed:"+ident,order[:5]==[x["chunk_id"] for x in a2["raw_seeds"]])
                    sequences=a2["live_request_sequences"]
                    query_sequences.add(sequences[-1]);doc_sequences.update(sequences[:-1])
                else:
                    check("empty_namespace_no_call:"+ident,a2["degradation"]=="no_eligible_candidates" and not a2["live_request_sequences"])
                allowed={sha256(c["text"].encode()).hexdigest() for c in chunks if retriever._authorized(c,ns) and retriever._located(c)}
                query_hash=sha256(a2["trace"]["retrieval_text"].encode()).hexdigest()
                for seq in a2["live_request_sequences"]:
                    entry=records[seq]
                    check("provider_context_and_authorization:"+str(seq),seq not in used and entry["context"]==dict(phase="development",report_id=rid,query_id=q["query_id"],arm="A2",namespace=ns) and set(entry["input_sha256"])<=allowed|{query_hash})
                    used.add(seq)
                for arm,r in [("A1",a1),("A2",a2)]:
                    elapsed[arm]+=r["trace"]["elapsed_ms"]
                    check("all_citations_original_authorized:"+ident+":"+arm,all(retriever.verify(s,ns) for s in r["raw_seeds"]+r["context_expansions"]+r["accepted"]))
                    check("ranking_contract:"+ident+":"+arm,not scores[(ident,arm)]["r02"].get("violations"))
                    case_scores[arm].append(scores[(ident,arm)])
                s1,s2=scores[(ident,"A1")],scores[(ident,"A2")]
                comparison.append(dict(row_id=ident,report_id=rid,namespace=ns,
                    a1_recall=s1["recall"],a2_recall=s2["recall"],a1_precision=s1["r02"]["score"],a2_precision=s2["r02"]["score"],
                    raw_order_changed=[s["chunk_id"] for s in a1["raw_seeds"]]!=[s["chunk_id"] for s in a2["raw_seeds"]],
                    accepted_ids_changed={s["chunk_id"] for s in a1["accepted"]}!={s["chunk_id"] for s in a2["accepted"]}))
        cost=sum(Decimal(r["list_price_cny"]) for r in records.values() if r["context"].get("report_id")==rid)
        performance.append(dict(report_id=rid,a1_retrieval_ms=round(elapsed["A1"],3),a2_retrieval_ms=round(elapsed["A2"],3),
                                paired_report_wall_ms=case["elapsed_ms"],list_price_cny=str(cost)))
        report_completeness.append(dict(report_id=rid,**{arm:all(s["recall"]==1 for s in ss if s["recall"] is not None) for arm,ss in case_scores.items()}))
    check("all_433_planned_requests_recorded",len(records)==snapshot["request_plan"]["request_count"]==433 and list(records)==list(range(1,434)))
    check("preflight_and_development_requests_partition",used==set(records)-{1} and records[1]["context"]==dict(phase="preflight") and after["preflight"]["passed"])
    for seq,r in records.items():
        check("request_metered_model_validated:"+str(seq),r["status"]=="validated" and r["attempts"]==1 and r["returned_model"]==ledger["model"] and bool(r["request_id"]) and type(r["total_tokens"]) is int and r["total_tokens"]>=0 and Decimal(r["list_price_cny"])==Decimal(r["total_tokens"])*Decimal("0.5")/1_000_000 and r["elapsed_ms"]>=0 and bool(r["vector_response_sha256"]))
    check("ledger_arithmetic_and_budgets",ledger["known_total_tokens"]==sum(r["total_tokens"] for r in records.values()) and Decimal(ledger["known_list_price_cny"])==sum(Decimal(r["list_price_cny"]) for r in records.values()) and ledger["unknown_usage_requests"]==0 and ledger["request_count"]<=600 and Decimal(ledger["known_list_price_cny"])<=1 and not ledger["stopped"])
    check("no_chat_calls",after["summary"]["model_generation_runs"]==0)
    def p95(values):return sorted(values)[math.ceil(len(values)*.95)-1]
    gains={}
    for ns in ["requirement","report"]:
        rows=[r for r in comparison if r["namespace"]==ns and r["a1_recall"] is not None]
        gains[ns]=dict(positive_rows=len(rows),precision_improved=sum(r["a2_precision"]>r["a1_precision"] for r in rows),
                       precision_regressed=sum(r["a2_precision"]<r["a1_precision"] for r in rows),
                       recall_improved=sum(r["a2_recall"]>r["a1_recall"] for r in rows),recall_regressed=sum(r["a2_recall"]<r["a1_recall"] for r in rows))
    result=dict(kind="live_development_integrity_and_paired_comparison_not_holdout",checks=checks,total=len(checks),passed=sum(c["passed"] for c in checks),failed=[c["name"] for c in checks if not c["passed"]],
                previous_commit=BASELINE,previous_result_files_preserved=len(history),dev_assets_preserved=len(material["asset_sha256"]),prior_frozen_assets_preserved=frozen_count,
                audit_revision=dict(first_audit="eval-results/candidate-live-validation-v0.1.json",reason="First audit compared nondeterministic role-fixture elapsed_ms; only application_log.elapsed_ms and export.trace.elapsed_ms are excluded from replay equality. Original execution and first audit remain unchanged; all virtual-clock values and behavior still compare exactly."),
                r01=after["r01"],r02=after["r02"],paired_rows=comparison,paired_change_summary=gains,report_completeness=report_completeness,
                performance=dict(measurement="single_development_run_sequential_queries_cold_task_within_report_index_reuse_no_warm_trial",reports=performance,
                    a1_report_retrieval_p95_ms=p95([p["a1_retrieval_ms"] for p in performance]),a2_report_retrieval_p95_ms=p95([p["a2_retrieval_ms"] for p in performance]),
                    http_request_p95_ms=p95([r["elapsed_ms"] for r in records.values()]),formal_p01="not_adjudicated_no_repeated_cold_warm_tasks"),
                cost=dict(total_tokens=ledger["known_total_tokens"],total_list_price_cny=ledger["known_list_price_cny"],preflight_list_price_cny=records[1]["list_price_cny"],
                    development_mean_list_price_cny_per_report=str(sum(Decimal(p["list_price_cny"]) for p in performance)/12),query_http_requests=len(query_sequences),document_http_requests=len(doc_sequences),preflight_http_requests=1,actual_account_bill="not_queried"),
                development_gates=dict(r01=all(after["r01"][arm][ns]>=.95 for arm in ["A1","A2"] for ns in ["requirement","report"]) and all(after["r01"]["A2"][ns]>=after["r01"]["A1"][ns] for ns in ["requirement","report"]),
                    r02=all(after["r02"][arm][ns]["precision_gate_passed"] for arm in ["A1","A2"] for ns in ["requirement","report"]),r03="not_adjudicated",adoption="not_authorized_by_development_scores"),
                result_sha256=h(RESULT),source_sha256=after["source_sha256"],holdout_materialized=0)
    with args.output.open("x") as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ["total","passed","failed","paired_change_summary","cost","development_gates"]},ensure_ascii=False))
    if result["failed"]:raise SystemExit(1)


if __name__=="__main__":main()
