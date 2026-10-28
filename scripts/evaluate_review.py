#!/usr/bin/env python3
"""Evaluate the controlled report workflow; annotations are scoring-only inputs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.ai_work.review import ReviewService, stamp, digest
from app.ai_work.export import export_xlsx
from app.knowledge_assistant.core import Corpus, Principal


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--xlsx",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.xlsx.exists():
        parser.error("结果文件已存在，请使用新路径保留历史运行。")
    corpus=Corpus()
    principal=Principal("workflow-eval-engineer","engineer",("DEMO-TASK-001",))
    annotation_path=ROOT/"data/bootstrap-v0.1/evaluation/review-annotations.jsonl"
    annotations=[json.loads(line) for line in annotation_path.read_text().splitlines()]
    cases=[]
    with tempfile.TemporaryDirectory() as temp:
        service=ReviewService(Path(temp)/"reviews.db",corpus)
        task=service.create(principal,{"sample":True})
        tid=task["task_id"]
        task=service.confirm(principal,tid,dict(revision=1,acknowledged=True,corrections={}))
        for repeat in range(1,4):
            run=service.run(principal,tid,dict(revision=2,idempotency_key=f"evaluation-repeat-{repeat}"))
            actual={i["item_id"]:i for i in run["items"]}
            scores=[]
            for a in annotations:
                item_id=(a["port"]+"-"+a["rule_id"].split("-")[-1]) if a["group"]=="checklist" else "SUMMARY-C1" if a["rule_id"]=="CONSISTENCY-01" else "BASIS-VERSION"
                item=actual[item_id]
                expected_basis={cid for cid in a["required_evidence"] if not cid.startswith("TR-")}
                actual_basis={b["chunk_id"] for b in item["basis"]}
                report_pages={ref["page"] for ref in item["report_evidence"]}
                expected_pages={int(cid.split("-")[1][1:]) for cid in a["required_evidence"] if cid.startswith("TR-")}
                scores.append(dict(annotation_id=a["annotation_id"],item_id=item_id,
                    finding_match=item["result"]==a["expected_finding"],
                    necessary_source_match=expected_basis<=actual_basis and expected_pages<=report_pages,
                    record_id_present=not a["record_id"] or any(a["record_id"] in ref["quote"] for ref in item["report_evidence"]),
                    expected=a["expected_finding"],actual=item["result"]))
            cases.append(dict(repeat=repeat,scores=scores,raw_run=run))
        # Export baseline with all professional decisions still pending.
        args.xlsx.parent.mkdir(parents=True,exist_ok=True)
        args.xlsx.write_bytes(export_xlsx(cases[0]["raw_run"]))
        service.db.close()
    paths=["app/ai_work/review.py","app/ai_work/export.py","app/knowledge_assistant/server.py",
           "app/knowledge_assistant/static/work.js","tests/test_ai_work.py","scripts/evaluate_review.py"]
    all_scores=[s for c in cases for s in c["scores"]]
    result=dict(version="ai-work-review-v0.1",evaluated_at=stamp(),dataset="author_drafted_development_fixture",
        professional_review="pending",independent_test=False,model_requests=0,
        generation="deterministic_rules_no_llm",snapshot=corpus.snapshot,
        corpus_sha256=corpus.digest,report_sha256=cases[0]["raw_run"]["report_sha256"],
        annotations_sha256=digest(annotation_path.read_bytes()),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths},
        summary=dict(unique_report_files=1,repeats=3,unique_reference_items=len(annotations),
            comparisons=len(all_scores),finding_matches=sum(s["finding_match"] for s in all_scores),
            necessary_source_matches=sum(s["necessary_source_match"] for s in all_scores),
            record_id_matches=sum(s["record_id_present"] for s in all_scores),
            baseline_counts=cases[0]["raw_run"]["counts"],
            per_repeat_ms=[c["raw_run"]["elapsed_ms"] for c in cases]),
        xlsx=dict(path=str(args.xlsx),sha256=digest(args.xlsx.read_bytes())),cases=cases,
        limitations=["只验证固定模拟模板和规则。", "参考标注为作者拟定，未完成专业核实。", "重复运行不等于独立样本。", "无真实标准条款判定或业务收益结论。"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result["summary"],ensure_ascii=False))


if __name__=="__main__":main()
