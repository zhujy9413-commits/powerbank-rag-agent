"""One paired A1/A2 development run, with live metering and isolated scoring.

--plan is strictly offline and estimates request count only, never quality.
--live is an explicit paid invocation; outputs and checkpoints never overwrite.
"""
import argparse
import base64
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEV = ROOT / "data/ai-work-rag-gain-dev-v0.1"


class PlanEmbedding:
    identity = "offline_request_count_only_not_quality"

    def __init__(self):
        self.records = []
        self.context = {}
        self.stopped = None

    def embed(self, texts):
        for offset in range(0, len(texts), 10):
            batch = texts[offset:offset+10]
            self.records.append(dict(input_count=len(batch), utf8_bytes=sum(len(t.encode()) for t in batch),
                                     max_text_utf8_bytes=max(len(t.encode()) for t in batch)))
        return dict(vectors=[[1.0]+[0.0]*1023 for _ in texts], model_id=self.identity)

    def ledger(self):
        return dict(kind="offline_request_plan_not_quality", request_count=len(self.records),
                    input_count=sum(r["input_count"] for r in self.records),
                    utf8_bytes=sum(r["utf8_bytes"] for r in self.records),
                    max_text_utf8_bytes=max(r["max_text_utf8_bytes"] for r in self.records),
                    external_requests=0)


def produce(live, checkpoint):
    denied = ("reference-annotations", "qrels", "author-source", "/eval-results/", "material-manifest")
    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)) and any(x in str(args[0]) for x in denied):
            raise PermissionError("gold_denied_in_application_phase")
    sys.addaudithook(guard)
    from app.ai_work.candidate import CandidateRetriever, RetrievalConfig, augment_baseline, digest
    from app.ai_work.candidate_inputs import load_input
    from app.ai_work.review import ReviewService
    from app.knowledge_assistant.core import Corpus, Principal
    rows = []
    config = RetrievalConfig(structured_routing=True)
    def save_ledger(ledger):
        temporary = checkpoint.with_suffix(".tmp")
        temporary.write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+"\n")
        temporary.replace(checkpoint)
    if live:
        from app.ai_work.live_embedding import MeteredEmbedding
        from app.knowledge_assistant.providers import Settings
        embedder = MeteredEmbedding(Settings(ROOT/".local/assistant/model.json").snapshot(), checkpoint=save_ledger)
    else:
        embedder = PlanEmbedding()
    failure = None
    preflight = None
    try:
        embedder.context = dict(phase="preflight")
        response = embedder.embed(["模拟充电宝整机短路保护测试记录", "模拟规格要求与当前测试工况核对"])
        preflight = dict(passed=len(response["vectors"])==2 and all(len(v)==1024 for v in response["vectors"]),
                         model_id=response["model_id"], dimensions=1024)
        if not preflight["passed"]:
            raise RuntimeError("preflight_failed")
        for directory in sorted((DEV/"application-inputs").iterdir()):
            started = time.perf_counter()
            task, chunks, originals = load_input(directory, ROOT)
            principal = Principal("candidate-dev-engineer", "engineer", (task["task_id"],))
            with tempfile.TemporaryDirectory(prefix="aw-live-candidate-") as temp:
                service = ReviewService(Path(temp)/"review.db", Corpus())
                created = service.create(principal, dict(filename=task["report_id"]+".pdf",
                    pdf_base64=base64.b64encode((ROOT/task["pdf_path"]).read_bytes()).decode()))
                tid = created["task_id"]
                service.confirm(principal,tid,dict(revision=1,acknowledged=True,corrections={}))
                baseline = service.run(principal,tid,dict(revision=2,idempotency_key="candidate-development"))
                service.db.close()
            task["selected_versions"] = {i:c["version"] for i,c in baseline["snapshot"]["basis"].items()}
            retriever = CandidateRetriever(chunks,task,principal,originals,config=config,embedder=embedder)
            case = dict(report_id=task["report_id"],task_id=task["task_id"],baseline=baseline,
                        original_payload_sha256=digest(baseline),queries=[])
            rows.append(case)
            for query in task["queries"]:
                methods = {}
                case["queries"].append(dict(query_id=query["query_id"], methods=methods))
                for arm,method in [("A1","bm25"),("A2","hybrid")]:
                    methods[arm] = {}
                    for ns in ["requirement", "report"]:
                        embedder.context = dict(phase="development", report_id=task["report_id"], query_id=query["query_id"], arm=arm, namespace=ns)
                        before = len(embedder.records)
                        output = retriever.retrieve(query,ns,method=method)
                        output["live_request_sequences"] = list(range(before+1,len(embedder.records)+1))
                        methods[arm][ns] = output
                        if embedder.stopped or (arm=="A2" and output["degradation"] not in {None,"no_eligible_candidates"}):
                            raise RuntimeError("live_embedding_run_stopped")
            augmented = augment_baseline(baseline,case["queries"])
            case["original_payload_preserved"] = digest({k:v for k,v in augmented.items() if k!="candidate_retrieval"})==digest(baseline)
            case["elapsed_ms"] = round((time.perf_counter()-started)*1000,3)
            print(json.dumps(dict(completed_report=task["report_id"], external_requests=len(embedder.records), elapsed_ms=case["elapsed_ms"])), file=sys.stderr, flush=True)
    except Exception:
        failure = embedder.stopped or "application_execution_failure"
    finally:
        if live:
            save_ledger(embedder.ledger())
    return dict(application_phase="gold_denied_subprocess", network="live_official_embedding_only" if live else "forbidden",
                config=asdict(config), cases=rows, preflight=preflight, ledger=embedder.ledger(),
                completed=failure is None and len(rows)==12, failure=failure)


def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--live",action="store_true");group.add_argument("--plan",action="store_true")
    p.add_argument("--produce",action="store_true");p.add_argument("--output",type=Path)
    p.add_argument("--checkpoint",type=Path)
    args=p.parse_args()
    if args.produce:
        if args.plan:
            with patch("socket.socket",side_effect=AssertionError("network_forbidden_in_plan")):
                raw=produce(False,None)
        else:
            raw=produce(True,args.checkpoint)
        print(json.dumps(raw,ensure_ascii=False));return
    if not args.output or args.output.exists():
        p.error("require_new_output_path")
    if args.live and (not args.checkpoint or args.checkpoint.exists() or not args.checkpoint.resolve().is_relative_to(ROOT/"tmp")):
        p.error("require_new_checkpoint_under_tmp")
    command=[sys.executable,__file__,"--produce","--live" if args.live else "--plan"]
    if args.live:
        command += ["--checkpoint",str(args.checkpoint.resolve())]
    process=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,text=True,check=True)
    raw=json.loads(process.stdout)
    if args.plan:
        result={k:raw[k] for k in ["application_phase","network","config","completed","failure","ledger"]}
    else:
        from scripts.evaluate_candidate_dev import evaluate
        from app.ai_work.candidate import VERSION
        # References and fault fixtures are read only after the live producer
        # exits. The evaluator and the four fixtures have no network access.
        with patch("socket.socket",side_effect=AssertionError("network_forbidden_in_evaluator")):
            result=evaluate(raw)
        outputs=[r for c in raw["cases"] for q in c["queries"] for r in q["methods"].get("A2",{}).values()]
        result.update(kind="live_embedding_development_not_holdout",evaluated_at=datetime.now(timezone.utc).isoformat(),
            protocol_id="AIWORK-RAG-GAIN-0.2",candidate_version=VERSION,input_config=raw["config"],
            application_phase=raw["application_phase"],raw_application_runs=raw["cases"],preflight=raw["preflight"],ledger=raw["ledger"],
            summary=dict(completed=raw["completed"],failure=raw["failure"],content_cases=len(raw["cases"]),
                offline_cases=len(result["offline"]),offline_cases_passed=sum(f["passed"] for f in result["offline"]),
                a2_namespace_runs=len(outputs),real_hybrid_namespace_runs=sum(r["effective_method"]=="bm25_embedding_rrf" for r in outputs),
                empty_namespace_runs=sum(r["degradation"]=="no_eligible_candidates" for r in outputs),
                unexpected_degradations=sum(r["degradation"] not in {None,"no_eligible_candidates"} for r in outputs),
                external_requests=raw["ledger"]["request_count"],model_generation_runs=0,
                formal_holdout_gate="not_evaluated",r03_net_gain="not_adjudicated_no_adoption_claim"),
            source_sha256={path:sha256((ROOT/path).read_bytes()).hexdigest() for path in [
                "app/ai_work/candidate.py","app/ai_work/candidate_inputs.py","app/ai_work/live_embedding.py",
                "scripts/evaluate_candidate_dev.py","scripts/evaluate_candidate_live.py"]})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in (["completed","ledger"] if args.plan else ["summary","r01","r02"])},ensure_ascii=False))
    if not raw["completed"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
