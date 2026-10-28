"""Produce raw development runs in a gold-denied subprocess, then score separately."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEV = ROOT/"data/ai-work-rag-gain-dev-v0.1"


def produce(ratio,route=False):
    # The application phase cannot read any reference labels, prior scores or
    # author intent. The supervisor loads gold only after this process exits.
    denied = ("reference-annotations", "qrels", "author-source", "/eval-results/", "material-manifest")
    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = str(args[0])
            if any(x in path for x in denied):raise PermissionError("gold_denied_in_application_phase")
    sys.addaudithook(guard)
    from app.ai_work.candidate import CandidateRetriever, RetrievalConfig, augment_baseline, digest
    from app.ai_work.candidate_inputs import load_input
    from app.ai_work.review import ReviewService
    from app.knowledge_assistant.core import Corpus, Principal
    rows = []
    config = RetrievalConfig(min_bm25_ratio=ratio,structured_routing=route)
    with patch("socket.socket", side_effect=AssertionError("network_forbidden_in_offline_development")):
        for directory in sorted((DEV/"application-inputs").iterdir()):
            task, chunks, originals = load_input(directory, ROOT)
            principal = Principal("candidate-dev-engineer", "engineer", (task["task_id"],))
            with tempfile.TemporaryDirectory(prefix="aw-candidate-") as temp:
                service = ReviewService(Path(temp)/"review.db", Corpus())
                import base64
                created = service.create(principal,dict(filename=task["report_id"]+".pdf",
                    pdf_base64=base64.b64encode((ROOT/task["pdf_path"]).read_bytes()).decode()))
                tid = created["task_id"]
                service.confirm(principal,tid,dict(revision=1,acknowledged=True,corrections={}))
                baseline = service.run(principal,tid,dict(revision=2,idempotency_key="candidate-development"))
                service.db.close()
            task["selected_versions"] = {i:c["version"] for i,c in baseline["snapshot"]["basis"].items()}
            retriever = CandidateRetriever(chunks,task,principal,originals,config=config)
            queries = []
            for query in task["queries"]:
                by_method = {}
                for arm,method in [("A1","bm25"),("A2","hybrid")]:
                    by_method[arm] = {ns:retriever.retrieve(query,ns,method=method) for ns in ["requirement","report"]}
                queries.append(dict(query_id=query["query_id"],methods=by_method))
            augmented = augment_baseline(baseline,queries)
            rows.append(dict(report_id=task["report_id"],task_id=task["task_id"],baseline=baseline,
                original_payload_sha256=digest(baseline),
                original_payload_preserved=digest({k:v for k,v in augmented.items() if k!="candidate_retrieval"})==digest(baseline),
                queries=queries))
    return dict(application_phase="gold_denied_subprocess",network="forbidden",config=asdict(config),cases=rows)


def offline_contracts():
    from app.ai_work.candidate import CandidateRetriever, controlled_explanation, digest
    from app.knowledge_assistant.core import Principal
    rows=[]
    for path in sorted((DEV/"offline-fixtures").glob("*.json")):
        f=json.loads(path.read_text());original=f["immutable_seed"];before=digest(original)
        checks={};actual={}
        if "sources" in f:
            task=dict(task_id="OFFLINE-TASK",task_authorized=True,selected_requirement_chunks=[],selected_versions={})
            chunks=[dict(chunk_id=c["id"],text=c["text"],allowed_roles=c["allowed_roles"],task_id=c["task_id"],
                         namespace="report",source_role="background",source_path=c["id"]+".txt",page=None,
                         section="offline",version="1",conditions=None,publication_status="active",material_type="synthetic",context_ids=[]) for c in f["sources"]]
            r=CandidateRetriever(chunks,task,Principal("offline",f["principal"]["role"],("OFFLINE-TASK",)),{(c["source_path"],None):c["text"] for c in chunks})
            response=r.retrieve(dict(text="模拟任务流程说明",field="consistency",port=None,conditions={}),"report")
            safe=response["accepted"]
            surfaces=dict(candidates=response["raw_seeds"],citations=safe,prompt=safe,provider_payload=safe,application_log=response["trace"],export=response)
            checks={a["surface"]:json.dumps(surfaces[a["surface"]],ensure_ascii=False).count(a["forbidden_text"])==a["expected_occurrences"] for a in f["assertions"]}
            actual=dict(surfaces=surfaces,provider_calls=0)
        elif "selected_requirement" in f:
            c=dict(chunk_id="OFFLINE-BASIS",text="模拟依据",namespace="requirement",source_role="selected_requirement",source_path="basis.txt",page=None,section="offline",version="1",conditions=None,allowed_roles=["engineer"],task_id="OFFLINE-TASK",material_type="synthetic",publication_status="archived")
            task=dict(task_id="OFFLINE-TASK",task_authorized=True,selected_requirement_chunks=[c["chunk_id"]],selected_versions={c["chunk_id"]:"1"})
            r=CandidateRetriever([c],task,Principal("offline","engineer",("OFFLINE-TASK",)),{("basis.txt",None):c["text"]})
            blocked=False
            try:r.retrieve(dict(text="模拟依据",field="response",port="A1",conditions={}),"requirement")
            except PermissionError:blocked=True
            checks=dict(new_review_blocked=blocked,original_snapshot_readable=digest(original)==before)
            actual=dict(blocked=blocked,original_snapshot=original,provider_calls=0)
        else:
            clock=[f.get("clock",{}).get("elapsed_before_generation_ms",0)]
            def provider(*,evidence,timeout_ms,attempt):
                if "clock" in f:
                    clock[0]+=min(timeout_ms,f["clock"]["mock_response_delay_ms"])
                    raise TimeoutError()
                return f["model_responses"][attempt-1]["body"]
            actual=controlled_explanation(original,original["evidence"],provider,now_ms=lambda:clock[0])
            checks=dict(terminal=actual["terminal"]==f["expected"]["terminal"],attempts=len(actual["attempts"])==f["expected"]["attempts"],
                        fabricated_accepted=actual["draft"] is None,raw_attempts_retained=bool(actual["attempts"]))
            if "clock" in f:
                checks.update(terminal_time=clock[0]==45000,effective_timeout=actual["attempts"][0]["timeout_ms"]==15000)
            else:checks["one_correction"]=len(actual["attempts"])-1==1
        checks["original_preserved"]=digest(original)==before and actual.get("original",original)==original
        rows.append(dict(case_id=f["fixture_id"],kind="offline_adapter_contract_not_live_model",checks=checks,passed=all(checks.values()),actual=actual))
    return rows


def evaluate(raw):
    from scripts.rag_gain_scoring_v0_2 import aggregate_r02,score_r02
    qrels=json.loads((ROOT/"data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json").read_text())["rows"]
    gold={(q["report_id"],q["query_id"],q["namespace"]):q for q in qrels}
    scored=[];r02records={arm:{} for arm in ["A1","A2"]}; recalls={arm:{n:[] for n in ["requirement","report"]} for arm in r02records}
    for case in raw["cases"]:
        corpus={c["chunk_id"]:c for c in [json.loads(l) for l in (DEV/"application-inputs"/case["report_id"]/"chunks.jsonl").read_text().splitlines()]}
        for query in case["queries"]:
            for arm,output in query["methods"].items():
                for ns,r in output.items():
                    q=gold[(case["report_id"],query["query_id"],ns)]
                    s=score_r02(q,r["raw_seeds"],corpus,arm=arm,negative_outcome=r["outcome"] if q["query_state"]=="no_available_evidence" else None)
                    ids={x["chunk_id"] for x in r["accepted"]}
                    groups=q["necessary_groups"]
                    covered=sum(any(set(a)<=ids for a in g["alternatives"]) for g in groups)
                    raw_ids={x["chunk_id"] for x in r["raw_seeds"]}
                    raw_covered=sum(any(set(a)<=raw_ids for a in g["alternatives"]) for g in groups)
                    recall=covered/len(groups) if groups else None
                    if q["query_state"]=="positive":recalls[arm][ns].append(recall)
                    r02records[arm][q["row_id"]]=s
                    scored.append(dict(row_id=q["row_id"],arm=arm,effective_method=r["effective_method"],degradation=r["degradation"],
                        r02=s,necessary_groups_total=len(groups),groups_covered=covered,recall=recall,
                        raw_recall=raw_covered/len(groups) if groups else None))
    macro={arm:aggregate_r02(qrels,records) for arm,records in r02records.items()}
    offline=offline_contracts()
    return dict(scored_queries=scored,r02=macro,r01={a:{n:sum(v)/len(v) for n,v in ns.items()} for a,ns in recalls.items()},offline=offline)


def main():
    p=argparse.ArgumentParser();p.add_argument("--produce",action="store_true");p.add_argument("--ratio",type=float,default=0);p.add_argument("--output",type=Path);p.add_argument("--route",action="store_true")
    args=p.parse_args()
    if args.produce:
        print(json.dumps(produce(args.ratio,args.route),ensure_ascii=False));return
    if not args.output or args.output.exists():p.error("请提供新的输出路径，拒绝覆盖结果。")
    process=subprocess.run([sys.executable,__file__,"--produce","--ratio",str(args.ratio)]+(["--route"] if args.route else []),cwd=ROOT,capture_output=True,text=True,check=True)
    raw=json.loads(process.stdout)
    # Production has finished; only the evaluator now reads qrels/fixtures.
    with patch("socket.socket",side_effect=AssertionError("network_forbidden")):
        result=evaluate(raw)
    result.update(kind="development_candidate_run_not_holdout",evaluated_at=datetime.now(timezone.utc).isoformat(),protocol_id="AIWORK-RAG-GAIN-0.2",candidate_version="candidate-retrieval-0.2",
        input_config=raw["config"],application_phase=raw["application_phase"],raw_application_runs=raw["cases"],
        summary=dict(content_cases=len(raw["cases"]),offline_cases=len(result["offline"]),offline_cases_passed=sum(x["passed"] for x in result["offline"]),
                     query_namespace_rows_per_arm=248,original_payloads_preserved=all(x["original_payload_preserved"] for x in raw["cases"]),
                     real_embedding_runs=0,hybrid_runs="degraded_to_bm25_not_A2_quality",model_generation_runs=0,external_requests=0,
                     formal_holdout_gate="not_evaluated",r03_net_gain="not_adjudicated_no_adoption_claim",m01="not_executed_only_offline_fault_contracts"),
        source_sha256={str(x.relative_to(ROOT)):sha256(x.read_bytes()).hexdigest() for x in [ROOT/"app/ai_work/candidate.py",ROOT/"app/ai_work/candidate_inputs.py",Path(__file__)]})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(summary=result["summary"],r01=result["r01"],r02=result["r02"]),ensure_ascii=False))


if __name__=="__main__":main()
