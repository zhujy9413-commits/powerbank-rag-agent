"""Evaluate only evidence retrieval on the author-drafted dev set, offline.

Labels are imported here only, never by the application. No model calls.
"""
import json
import argparse
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.knowledge_assistant.core import Corpus, Assistant, Principal


class Offline:
    def snapshot(self):
        return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"eval-results/retrieval-baseline-v0.1.json")
    args=parser.parse_args()
    if args.output.exists():
        parser.error("结果文件已存在；请通过--output指定新文件以保留原始基线。")
    corpus=Corpus()
    cases=[json.loads(line) for line in (ROOT/"data/bootstrap-v0.1/evaluation/questions.jsonl").read_text().splitlines()]
    rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        assistant=Assistant(corpus,Offline(),Path(tmp)/"vectors.json")
        for case in cases:
            principal=Principal("eval-"+case["user_role"],case["user_role"],tuple(case["authorized_task_ids"]))
            result=assistant.ask(case["question"],principal,include_archived=case["include_archived"],task_id=case["task_id"])
            actual=set(result["trace"]["retrieved_chunk_ids"])
            groups=case["required_evidence_groups"]
            found=[bool(set(group)&actual) for group in groups]
            rows.append(dict(case_id=case["case_id"],module=case["module"],required_groups=len(groups),hit_groups=sum(found),all_groups_hit=all(found),
                retrieved_chunk_ids=result["trace"]["retrieved_chunk_ids"],missing_groups=[g for g,ok in zip(groups,found) if not ok],status=result["status"]))
    output=dict(evaluation="keyword_retrieval_baseline_only",created_at=datetime.now(timezone.utc).isoformat(),snapshot=corpus.snapshot,corpus_digest=corpus.digest,
        split="dev_author_draft_expert_pending",top_k=6,generation="not_run",embedding="not_run",business_effect="not_measured",
        cases=len(rows),required_groups=sum(r["required_groups"] for r in rows),hit_groups=sum(r["hit_groups"] for r in rows),
        fully_hit_cases=sum(r["all_groups_hit"] for r in rows),rows=rows)
    out=args.output;out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in output.items() if k!="rows"},ensure_ascii=False))
    print("Missing evidence:",[(r["case_id"],r["missing_groups"]) for r in rows if not r["all_groups_hit"]])


if __name__=="__main__":
    main()
