"""Explicit, paid live dev-set evaluation; labels never enter model inputs.

Uses the backend's saved local settings and existing vector index. Credentials
are not printed or copied into results. Raw candidates are unvalidated audit
material, never application answers. This script does not score semantics.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.knowledge_assistant.core import Assistant, Corpus, Principal
from app.knowledge_assistant.providers import Settings, embeddings, generate


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--keyword-baseline", type=Path, default=ROOT/"eval-results/retrieval-baseline-v0.1.json")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("结果文件已存在；请使用新文件名保留原始运行记录。")
    source = ROOT / "data/bootstrap-v0.1/evaluation/questions.jsonl"
    cases = [json.loads(line) for line in source.read_text().splitlines()]
    if set(args.case) - {c["case_id"] for c in cases}:
        parser.error("包含未知用例ID。")
    cases = [c for c in cases if not args.case or c["case_id"] in args.case]
    corpus = Corpus()
    settings = Settings(ROOT / ".local/assistant/model.json")
    public = settings.public()
    if not public["configured"]:
        parser.error("尚未保存本机模型配置。")
    audit = {}

    def audited_generate(config, question, evidence, scope):
        audit["generation_attempts"] += 1
        value, usage = generate(config, question, evidence, scope)
        audit["raw_candidate_unvalidated"] = value
        audit["provider_generation_usage"] = {k: v for k, v in usage.items() if not k.startswith("_")}
        audit["prompt_sha256"] = usage.get("_prompt_sha256")
        audit["canonical_payload_sha256"] = usage.get("_canonical_payload_sha256")
        return value, usage

    def audited_embeddings(config, texts):
        audit["embedding_attempts"] += 1
        return embeddings(config, texts)

    assistant = Assistant(corpus, settings, ROOT / ".local/assistant/vectors.json",
                          generator=audited_generate, embedder=audited_embeddings)
    if not assistant.vector_ready():
        parser.error("需先在页面建立与当前配置匹配的向量索引。")
    output = dict(evaluation="live_hybrid_generation_dev", started_at=now(),
        snapshot=corpus.snapshot, corpus_digest=corpus.digest,
        dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        application_sha256={name:hashlib.sha256((ROOT/"app/knowledge_assistant"/name).read_bytes()).hexdigest() for name in ["core.py","providers.py"]},
        model={k: public[k] for k in ["provider", "model", "embedding_model"]},
        split="dev_author_draft_expert_pending", top_k=6,
        semantic_scoring="not_automated_expert_review_pending", business_effect="not_measured",
        index_build_usage="not_included", embedding_token_usage="not_collected", rows=[])
    baseline_path = args.keyword_baseline
    baseline = json.loads(baseline_path.read_text())
    comparable = baseline["corpus_digest"] == corpus.digest
    baseline_rows = {r["case_id"]: r for r in baseline["rows"]} if comparable else {}
    output["keyword_baseline_comparable_corpus"] = comparable
    output["keyword_baseline_file"] = baseline_path.name
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        audit.clear()
        audit.update(generation_attempts=0, embedding_attempts=0)
        principal = Principal("live-eval-" + case["user_role"], case["user_role"], tuple(case["authorized_task_ids"]))
        started = time.monotonic()
        result = assistant.ask(case["question"], principal, mode="answer",
            include_archived=case["include_archived"], task_id=case["task_id"])
        actual = set(result["trace"]["retrieved_chunk_ids"])
        groups = case["required_evidence_groups"]
        found = [bool(set(g) & actual) for g in groups]
        expected = {c["chunk_id"] for c in corpus.candidates(principal, case["include_archived"], case["task_id"])}
        row = dict(case_id=case["case_id"], category=case["category"], question=case["question"],
            principal=dict(role=principal.role, task_ids=list(principal.task_ids)),
            required_groups=len(groups), hit_groups=sum(found), all_groups_hit=all(found),
            missing_groups=[g for g, ok in zip(groups, found) if not ok],
            unauthorized_retrieved_ids=sorted(actual - expected),
            keyword_baseline_hit_groups=baseline_rows.get(case["case_id"], {}).get("hit_groups"),
            result=result, audit=dict(audit), wall_ms=round((time.monotonic()-started)*1000),
            semantic_review="pending", final_human_decision=None)
        output["rows"].append(row)
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(dict(case_id=row["case_id"], status=result["status"],
            hit_groups=row["hit_groups"], required_groups=row["required_groups"],
            citation_check=result["trace"]["citation_check"], elapsed_ms=result["elapsed_ms"]), ensure_ascii=False), flush=True)
    rows = output["rows"]
    usage = Counter()
    for row in rows:
        usage.update(row["audit"].get("provider_generation_usage", {}))
    output.update(finished_at=now(), cases=len(rows),
        required_groups=sum(r["required_groups"] for r in rows),
        hit_groups=sum(r["hit_groups"] for r in rows), fully_hit_cases=sum(r["all_groups_hit"] for r in rows),
        statuses=dict(Counter(r["result"]["status"] for r in rows)),
        generation_attempts=sum(r["audit"]["generation_attempts"] for r in rows),
        embedding_query_attempts=sum(r["audit"]["embedding_attempts"] for r in rows),
        citation_verified_responses=sum(r["result"]["trace"]["citation_check"] == "ids_and_quotes_verified" for r in rows),
        unauthorized_retrieval_cases=sum(bool(r["unauthorized_retrieved_ids"]) for r in rows),
        recorded_generation_usage=dict(usage))
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "rows"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
