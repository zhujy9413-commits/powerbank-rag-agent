"""Independent material audit only. Never imports or scores the application.

Two PDF text engines, original documents, author source and reference labels are
cross-checked. Offline fixtures are validated as contracts, not executed controls.
"""
import argparse
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/ai-work-rag-gain-dev-v0.1"


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def norm(s): return re.sub(r"\s+", "", s)
def digest(path): return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error("拒绝覆盖既有核验结果。")
    checks = []
    def check(name, value, detail=None):
        entry = dict(name=name, passed=bool(value))
        if detail is not None: entry["detail"] = detail
        checks.append(entry)
    ledger = load(PACK/"cases.json")
    cases = ledger["cases"]
    planned = load(ROOT/"data/ai-work-rag-gain-v0.1/cases.json")["cases"]
    check("exact_16_planned_dev_cases", {c["case_id"] for c in cases} == {c["case_id"] for c in planned if c["split"] == "dev"} and len(cases) == 16)
    check("types_12_content_4_offline", Counter(c["kind"] for c in cases) == dict(content_report=12, offline_fault_fixture=4))
    check("unique_dev_families", len({c["family_id"] for c in cases}) == 16 and all(c["split"] == "dev" for c in cases))
    check("unscored_no_holdout_no_model", ledger["holdout_materialized"] == ledger["model_requests"] == ledger["experiments_executed"] == 0 and all(c["observed_result"] is None for c in cases))
    snapshots = load(ROOT/"data/ai-work-rag-gain-v0.1/protocol.json")["baseline"]["source_sha256"]
    for path, expected in snapshots.items(): check("baseline_unchanged:"+path, digest(ROOT/path) == expected)
    frozen_count = 0
    for f in ["review-holdout-v0.1", "p0-holdout-v0.1", "p1-holdout-v0.1"]:
        for path, expected in load(ROOT/"data"/f/"freeze.json")["asset_sha256"].items():
            check("legacy_frozen_asset:"+path, digest(ROOT/path) == expected); frozen_count += 1
    check("88_legacy_assets", frozen_count == 88)
    # First evaluation files must remain byte-identical to the pre-material delivery.
    historical = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ledger["baseline_material_commit"], "eval-results"], cwd=ROOT).decode().splitlines()
    for path in historical:
        original = subprocess.check_output(["git", "show", ledger["baseline_material_commit"]+":"+path], cwd=ROOT)
        check("historical_result_unchanged:"+path, digest(ROOT/path) == sha256(original).hexdigest())
    stats = dict(pdfs=0, pages=0, offline_fixtures=0, core_units=0, queries=0, missing_core_units=0,
                 authorized_distractor_fragments=0, indexed_chunks=0, exact_pdf_quotes=0, exact_requirement_quotes=0)
    pdf_details = []
    selected = {x["chunk_id"]: x for x in load(PACK/"selected-basis/chunks.json")}
    check("selected_eight_chunks", len(selected) == 8)
    for ident, c in selected.items():
        raw = (ROOT/c["source_path"]).read_text(encoding="utf-8")
        check("verbatim_selected_source:"+ident, c["text"] in raw and (PACK/"selected-basis"/Path(c["source_path"]).name).read_text(encoding="utf-8") == raw)
    for c in cases:
        ident = c["case_id"]; fixture = ROOT/c["fixture_path"]
        check("fixture_hash:"+ident, digest(fixture) == c["fixture_sha256"])
        if c["kind"] == "offline_fault_fixture":
            f = load(fixture); stats["offline_fixtures"] += 1
            check("offline_contract_only:"+ident, f["mode"] == "offline_only" and f["network_allowed"] is False and f["virtual_clock"] and f["external_requests"] == 0 and f["application_execution_status"] == "not_executed")
            check("immutable_seed_hash:"+ident, sha256(json.dumps(f["immutable_seed"], sort_keys=True, ensure_ascii=False).encode()).hexdigest() == f["immutable_seed_sha256"])
            check("declared_deadlines:"+ident, f["max_corrections"] == 1 and f["single_chat_timeout_ms"] == 20000 and f["total_deadline_ms"] == 45000)
            if ident.endswith("01"):
                deny = next(x for x in f["sources"] if x["id"] == "DENY")
                check("permission_injection_unreadable", f["principal"]["role"] not in deny["allowed_roles"] and len(f["assertions"]) == 6 and all(a["forbidden_text"] == deny["text"] and a["expected_occurrences"] == 0 for a in f["assertions"]))
            if ident.endswith("02"):
                check("new_vs_history_expected_separately", f["selected_requirement"]["after_status"] == "archived" and f["actions"] == [dict(action="new_review", expected="blocked_before_provider"), dict(action="read_authorized_existing_history", expected="original_snapshot_readable")])
            if ident.endswith("03"):
                check("two_invalid_citation_responses", len(f["model_responses"]) == 2 and all(not set(x["body"]["citation_ids"]) & set(f["allowed_citations"]) for x in f["model_responses"]) and f["expected"]["corrections"] == 1 and f["expected"]["terminal"] == "template_fallback")
            if ident.endswith("04"):
                remaining = f["total_deadline_ms"]-f["clock"]["elapsed_before_generation_ms"]
                check("virtual_timeout_arithmetic", f["expected"]["effective_attempt_timeout_ms"] == min(remaining, f["single_chat_timeout_ms"]) == 15000 and f["expected"]["terminal_at_ms"] == 45000 and f["clock"]["mock_response_delay_ms"] > remaining)
            continue
        source = load(ROOT/c["author_source_path"])
        gold = load(ROOT/c["annotation_path"])
        input_dir = ROOT/c["input_dir"]
        task = load(input_dir/"task.json")
        chunks = [json.loads(s) for s in (input_dir/"chunks.jsonl").read_text(encoding="utf-8").splitlines()]
        index = {x["chunk_id"]: x for x in chunks}
        pp = [p.extract_text() or "" for p in PdfReader(fixture).pages]
        with pdfplumber.open(fixture) as doc: pl = [p.extract_text() or "" for p in doc.pages]
        stats["pdfs"] += 1; stats["pages"] += len(pp); stats["indexed_chunks"] += len(chunks)
        stats["queries"] += len(task["queries"]); stats["core_units"] += 10
        stats["authorized_distractor_fragments"] += len(c["authorized_distractor_ids"])
        check("two_pages_and_identity:"+ident, len(pp) == len(pl) == 2 and all("模拟整机保护功能测试报告" in s and "PB-DEMO-01" in s and "模拟材料" in s for s in pp+pl))
        check("index_budget_and_unique_ids:"+ident, len(chunks) == len(index) == c["index_chunk_count"] <= 80 and len(task["queries"]) == c["query_count"] <= 12)
        check("exactly_20_authorized_distractors:"+ident, len(set(c["authorized_distractor_ids"])) == 20 and all(index[k]["source_role"] == "background" and index[k]["allowed_roles"] == ["engineer"] and index[k]["task_id"] == task["task_id"] for k in c["authorized_distractor_ids"]))
        check("reference_and_runtime_query_ids:"+ident, [q["query_id"] for q in task["queries"]] == [q["query_id"] for q in gold["queries"]] and len({q["query_id"] for q in task["queries"]}) == len(task["queries"]))
        runtime = "\n".join(p.read_text(encoding="utf-8") for p in input_dir.iterdir() if p.is_file())+"".join(pp)
        check("no_gold_or_case_ids_in_runtime:"+ident, all(token not in runtime for token in ["RG-", "authored_comparison", "expected_behavior", "requirement_groups", "prohibited_claims", "reference-annotations"]))
        check("selected_requirement_namespace_only:"+ident, {x["chunk_id"] for x in chunks if x["namespace"] == "requirement"} == set(selected) and all(x["source_role"] == "selected_requirement" for x in chunks if x["namespace"] == "requirement"))
        check("metadata_and_context_links:"+ident, all(x["publication_status"] == "active" and x["task_id"] == task["task_id"] and x["allowed_roles"] == ["engineer"] and len(x["context_ids"]) <= 1 and all(y in index and index[y]["namespace"] == x["namespace"] for y in x["context_ids"]) for x in chunks))
        for x in chunks:
            key = x["chunk_id"]
            if x["page"]:
                ok = all(norm(x["text"]) in norm(engine[x["page"]-1]) for engine in [pp, pl])
                check("dual_engine_pdf_quote:"+ident+":"+key, ok)
                stats["exact_pdf_quotes"] += 1
            else:
                check("verbatim_text_source:"+ident+":"+key, x["text"] in (ROOT/x["source_path"]).read_text(encoding="utf-8"))
                if x["namespace"] == "requirement": stats["exact_requirement_quotes"] += 1
        for key, citation in gold["citations"].items():
            check("citation_identity_hash:"+ident+":"+key, key in index and all(citation[k] == index[key][k] for k in ["namespace", "source_role", "source_path", "page", "section", "version", "text", "conditions"]) and sha256(citation["text"].encode()).hexdigest() == citation["text_sha256"])
        for q in gold["queries"]:
            for space, groups in [("requirement", q["requirement_groups"]), ("report", q["report_groups"]+q["extra_required_groups"])]:
                check("nonempty_groups:"+ident+":"+q["query_id"]+":"+space, all(g["alternatives"] and all(a and all(k in index and k in gold["citations"] and index[k]["namespace"] == space for k in a) for a in g["alternatives"]) for g in groups))
            if re.fullmatch(r"[AC]1-0[1-5]", q["query_id"]):
                port, number = q["query_id"].split("-")
                field = ["response", "recovery", "temperature", "appearance", "method"][int(number)-1]
                record = next((r for r in source["records"] if r["port"] == port and r["field"] == field), None)
                missing = record is None
                stats["missing_core_units"] += int(missing)
                check("absence_label_no_invented_quote:"+ident+":"+q["query_id"], q["no_available_report_evidence"] == missing and q["absence_proof_citation"] is None and (not missing or (not q["report_groups"] and q["conservative_handling"] == "evidence_insufficient")))
                if record:
                    raw = record["text"]
                    expected = "no_issue"
                    if field in ["response", "recovery"]:
                        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(ms|s|V)\b", raw)
                        if not matches:
                            check("unit_header_explicit:"+ident+":"+port, source["unit_header"] is not None and "单位统一为ms" in source["unit_header"] and record["unit_header"] in index)
                            value, unit = re.search(r"保护响应\s+(\d+)$", raw).group(1), "ms"
                        else: value, unit = matches[0]
                        numeric = Decimal(value)*(1000 if unit == "s" else 1)
                        if field == "response": valid = numeric <= 500
                        else: valid = unit == "V" and Decimal("4.75") <= numeric <= Decimal("5.25")
                        if not valid: expected = "numeric_outside_demo_limit"
                    elif field == "temperature":
                        temperatures = re.findall(r"(\d+(?:\.\d+)?)摄氏度", raw)
                        check("two_temperature_values:"+ident+":"+port, len(temperatures) == 2)
                        if Decimal(temperatures[1])-Decimal(temperatures[0]) > 12: expected = "numeric_outside_demo_limit"
                    elif field == "appearance":
                        check("explicit_three_observations:"+ident+":"+port, all(s in raw for s in ["无起火", "无爆炸", "无漏液"]))
                    elif field == "method": check("nonempty_method:"+ident+":"+port, bool(raw.split("恢复方式", 1)[1].strip()))
                    check("independent_numeric_reference:"+ident+":"+q["query_id"], q["authored_comparison"] == expected)
                    keys = [k for g in q["report_groups"] for a in g["alternatives"] for k in a]
                    check("correct_record_and_port:"+ident+":"+q["query_id"], any(record["record_id"] in k and raw == index[k]["text"] and port in raw for k in keys))
        bounds = load(PACK/"render-bounds"/(source["report_id"]+".json"))
        check("author_layout_bounds:"+ident, all(b["x"] >= 35 and b["x"]+b["width"] <= 614 and b["y"] >= 24 and b["y"]+b["size"] <= 830 for b in bounds))
        pdf_details.append(dict(case_id=ident, pdf_path=c["fixture_path"], sha256=digest(fixture), pages=len(pp),
                                index_chunks=len(chunks), distractors=20, queries=len(task["queries"])))
    # Semantic signatures prevent a nominal 12-file pack with the wrong challenge.
    src = {load(ROOT/c["author_source_path"])["case_id"]: load(ROOT/c["author_source_path"]) for c in cases if c["kind"] == "content_report"}
    check("term_narrative_challenges", "输出被切断" in str(src["RG-TERM-DEV-01"]) and "输出回到" in str(src["RG-TERM-DEV-02"]))
    check("context_challenges", "试验前说明" in src["RG-CONTEXT-DEV-01"]["global_condition"] and src["RG-CONTEXT-DEV-02"]["unit_header"] is not None)
    unit_case = src["RG-CONTEXT-DEV-02"]
    unit_pdf = norm(PdfReader(ROOT/unit_case["pdf_path"]).pages[0].extract_text())
    response_rows = [norm(r["text"]) for r in unit_case["records"] if r["field"] == "response"]
    recovery_rows = [norm(r["text"]) for r in unit_case["records"] if r["field"] == "recovery"]
    check("header_applies_to_exactly_two_response_rows", unit_pdf.index(norm(unit_case["unit_header"])) < unit_pdf.index(response_rows[0]) < unit_pdf.index(response_rows[1]) < unit_pdf.index("记录表A2") < min(unit_pdf.index(t) for t in recovery_rows))
    for cid in ["RG-PORT-DEV-01", "RG-PORT-DEV-02"]:
        vals = [r["normalized_value"] for r in src[cid]["records"] if r["field"] == "response"]
        check("same_port_values:"+cid, len(set(vals)) == 1)
    check("same_digits_different_fields", {r["normalized_value"] for r in src["RG-PORT-DEV-02"]["records"] if r["port"] == "A1" and r["field"] in ["response", "recovery"]} == {"5 ms", "5.00 V"})
    check("5v_and_9v_explicit", src["RG-CONDITION-DEV-01"]["extras"][0]["conditions"]["voltage_v"] == 9)
    check("input_and_output_explicit", src["RG-CONDITION-DEV-02"]["extras"][0]["conditions"]["electrical_role"] == "输入")
    check("reva_declaration_revb_task", "RevA" in src["RG-GAP-DEV-02"]["specification_declaration"])
    check("untrusted_document_instruction", "不再核对明细" in src["RG-NOISE-DEV-02"]["extras"][0]["text"])
    check("three_genuine_missing_units", stats["missing_core_units"] == 3)
    check("120_fixed_core_units_124_queries", stats["core_units"] == 120 and stats["queries"] == 124)
    report = dict(validation_kind="development_material_integrity_not_application_evaluation", date="2026-10-29", checks=checks,
                  passed=sum(x["passed"] for x in checks), total=len(checks), stats=stats, pdfs=pdf_details,
                  app_behavior_tests_executed=0, retrieval_arm_jobs_executed=0, model_requests=0,
                  offline_fixtures_executed_against_application=0, holdout_materialized=0,
                  visual_review_status="see_separate_24_page_visual_record", professional_review_status="pending",
                  source_correction="Selected requirement chunks use source-section verbatim text; legacy bootstrap summaries and application remain unchanged.",
                  asset_sha256={rel: digest(ROOT/rel) for rel in sorted({str(p.relative_to(ROOT)) for p in PACK.rglob("*") if p.is_file()} | {c["fixture_path"] for c in cases})})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(passed=report["passed"], total=report["total"], stats=stats, failures=[x for x in checks if not x["passed"]]), ensure_ascii=False))
    if report["passed"] != report["total"]: raise SystemExit(1)


if __name__ == "__main__": main()
