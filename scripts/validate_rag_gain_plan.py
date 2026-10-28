"""Validate planning consistency only; does not build samples, score outputs or call models."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/ai-work-rag-gain-v0.1"
DOCS = ["docs/ai-work/rag-gain-validation-plan-v0.1.md",
        "docs/ai-work/rag-gain-evaluation-checklist-v0.1.md"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出已存在，拒绝覆盖。")
    protocol = json.loads((BASE/"protocol.json").read_text())
    ledger = json.loads((BASE/"cases.json").read_text())
    cases = ledger["cases"]
    checks = []

    def check(name, valid):
        checks.append(dict(name=name, passed=bool(valid)))

    check("protocol_identity", protocol["protocol_id"] == ledger["protocol_id"] == "AIWORK-RAG-GAIN-0.1")
    check("scope_locked_execution_not_run", protocol["status"] == "scope_and_acceptance_locked" and protocol["execution_status"] == "not_run")
    check("samples_not_frozen_or_materialized", protocol["sample_status"] == ledger["status"] == "planned_not_materialized" and protocol["sample_freeze_status"] == "not_frozen")
    check("no_model_calls_or_spend_authorization", protocol["model_requests_this_delivery"] == 0 and protocol["metrics"][-1]["spend_authorized"] is False)
    check("48_unique_cases", len(cases) == len({c["case_id"] for c in cases}) == 48)
    check("case_splits", Counter(c["split"] for c in cases) == {"dev": 16, "holdout": 32})
    check("case_types", Counter(c["kind"] for c in cases) == {"content_report": 36, "offline_fault_fixture": 12})
    for category in ["TERM", "CONTEXT", "PORT", "CONDITION", "GAP", "NOISE"]:
        check("content_stratum:"+category, Counter(c["split"] for c in cases if c["category"] == category) == {"dev": 2, "holdout": 4})
    check("offline_fault_splits", Counter(c["split"] for c in cases if c["category"] == "OPS") == {"dev": 4, "holdout": 8})
    check("five_arms_retain_real_baseline", [a["id"] for a in protocol["arms"]] == ["A0", "A1", "A2", "A3", "A4"] and all(a["retains_a0"] for a in protocol["arms"]))
    check("generation_arms", [a["id"] for a in protocol["arms"] if a["generation"]] == ["A3", "A4"])
    check("retrieval_ablation", [a["supplement"] for a in protocol["arms"]] == ["none", "bm25", "bm25_embedding_rrf", "bm25", "bm25_embedding_rrf"])
    check("scope_unchanged", protocol["scope"]["core_comparison_units"] == 10 and protocol["scope"]["voltage_v"] == 5 and protocol["scope"]["ports"] == ["A1", "C1"])
    check("two_evidence_namespaces", protocol["retrieval"]["namespace_roles"] == ["requirement", "report"] and protocol["retrieval"]["gold_visible_to_application"] is False)
    check("retrieval_budget", protocol["retrieval"]["top_k_per_namespace"] == 5 and protocol["retrieval"]["max_queries_per_report"] == 12)
    metrics = {m["id"]: m for m in protocol["metrics"]}
    check("nine_acceptance_metrics", set(metrics) == {"S01", "S02", "S03", "R01", "R02", "R03", "M01", "P01", "C01"})
    check("redlines", all(metrics[m]["gate"] == "redline" for m in ["S01", "S02", "S03"]))
    check("retrieval_thresholds", metrics["R01"]["threshold"] == .95 and metrics["R02"]["threshold"] == .8)
    check("report_level_denominator", metrics["R03"]["complete_reports_min"] == 22 and metrics["R03"]["denominator"] == 24 and metrics["R03"]["net_improvement_min"] == 3 and metrics["R03"]["repetitions"] == 3)
    check("model_and_reader_thresholds", metrics["M01"]["first_pass_reports_min"] == metrics["M01"]["final_supported_reports_min"] == 23 and metrics["M01"]["human_complete_min"] == 22 and metrics["M01"]["human_preference_min"] == 16 and metrics["M01"]["human_status"] == "pending_unassigned")
    check("performance_deadlines", metrics["P01"]["cold_p95_seconds"] == 30 and metrics["P01"]["warm_p95_seconds"] == 15 and metrics["P01"]["single_chat_timeout_seconds"] == 20 and metrics["P01"]["total_deadline_seconds"] == 45 and metrics["P01"]["max_corrections"] == 1)
    check("cost_ceilings", metrics["C01"]["mean_incremental_cny_per_report_max"] == .2 and metrics["C01"]["campaign_cny_max"] == 100 and metrics["C01"]["external_requests_max"] == 2500)
    check("model_and_price_preflight_pending", protocol["provider"]["runtime_model_and_price_preflight_status"] == "pending_before_execution")
    normal = (12 + 24*3 + 3)*5
    fault = 12*5
    check("run_arithmetic", protocol["run_plan"]["normal_arm_executions"] == normal == 435 and protocol["run_plan"]["offline_fault_arm_executions"] == fault == 60 and protocol["run_plan"]["total_arm_executions"] == normal+fault == 495)
    check("generation_call_arithmetic", protocol["run_plan"]["max_generation_requests"] == (12+24*3+3)*2*2 == 348 and protocol["run_plan"]["fault_fixtures_external_requests"] == 0)
    check("preflight_generation_cap", protocol["run_plan"]["max_preflight_generation_requests"] == 4)
    check("cold_warm_schedule_same_three_runs", protocol["run_plan"]["holdout_index_schedule"] == ["cold_task_index", "same_task_warm_index", "same_task_warm_index"] and protocol["run_plan"]["reuse_query_or_generation_cache"] is False)
    checklist = (ROOT/DOCS[1]).read_text()
    for case in cases:
        cid = case["case_id"]
        check("planned_and_unscored:"+cid, case["status"] == "planned_not_materialized" and all(case[k] is None for k in ["fixture_path", "fixture_sha256", "expected_evidence_groups", "observed_result", "family_id", "annotation_reviewer"]))
        check("mapped_acceptance:"+cid, bool(case["assertion_ids"]) and set(case["assertion_ids"]) <= set(metrics))
        check("checklist_row:"+cid, checklist.count("| "+cid+" · ") == 1 and case["scenario"] in checklist and case["expected_behavior"] in checklist)
    baseline = protocol["baseline"]
    ref = baseline["git_commit"]
    check("baseline_commit_format", re.fullmatch(r"[a-f0-9]{40}", ref) is not None)
    for path, expected in baseline["source_sha256"].items():
        blob = subprocess.check_output(["git", "show", ref+":"+path], cwd=ROOT)
        check("baseline_source:"+path, hashlib.sha256(blob).hexdigest() == expected == hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
    for doc in DOCS:
        path = ROOT/doc
        text = path.read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if not target.startswith(("https://", "http://", "#")):
                check("local_reference:"+doc+":"+target, (path.parent/target).resolve().is_file())
    check("holdout_novelty_not_external_independence", "not external independent" in protocol["sampling"]["holdout_novelty"])
    files = DOCS + ["data/ai-work-rag-gain-v0.1/protocol.json", "data/ai-work-rag-gain-v0.1/cases.json"]
    output = dict(validation_kind="plan_consistency_only", experiments_executed=0, model_requests=0,
                  sample_freeze_status="not_frozen", checks=checks,
                  passed=sum(c["passed"] for c in checks), total=len(checks),
                  asset_sha256={f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k: output[k] for k in ["validation_kind", "passed", "total", "experiments_executed", "model_requests"]}))
    if output["passed"] != output["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
