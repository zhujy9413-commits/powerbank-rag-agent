"""Offline data integrity checks; this does not measure a RAG system."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import hashlib
import json
import re
from urllib.parse import urlparse

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/bootstrap-v0.1"


def read(rel):
    return json.loads((BASE / rel).read_text(encoding="utf-8"))


def lines(rel):
    return [json.loads(s) for s in (BASE / rel).read_text(encoding="utf-8").splitlines() if s.strip()]


def require(ok, message):
    if not ok:
        raise ValueError(message)


manifest = read("manifest.json")
for entry in manifest["files"]:
    p = ROOT / entry["path"]
    require(p.is_file(), f"Missing file: {p}")
    require(hashlib.sha256(p.read_bytes()).hexdigest() == entry["sha256"], f"Snapshot changed: {p}")

knowledge = lines("index/knowledge-chunks.jsonl")
tasks = lines("index/task-chunks.jsonl")
questions = lines("evaluation/questions.jsonl")
annotations = lines("evaluation/review-annotations.jsonl")
chunks = {c["chunk_id"]: c for c in knowledge + tasks}
require(len(chunks) == len(knowledge) + len(tasks), "Duplicate chunk IDs")
require(len(questions) == 24 and len({q['case_id'] for q in questions}) == 24, "Question IDs/count")
require(len(annotations) == 12 and len({a['annotation_id'] for a in annotations}) == 12, "Annotation IDs/count")
require(len(knowledge) == manifest["knowledge_chunks"] and len(tasks) == manifest["task_chunks"], "Chunk counts")
for c in chunks.values():
    require((BASE / c["path"]).is_file(), f"Broken evidence path: {c['chunk_id']}")
    require("evaluation" not in c["path"] and c["text"].strip(), f"Answer leakage or empty evidence: {c['chunk_id']}")
    require(c["allowed_roles"] and c["material_type"], f"Missing provenance or ACL: {c['chunk_id']}")
require(all(c["scope"] == "knowledge" for c in knowledge), "Report leaked into common corpus")
require(all(c["scope"] == "task:DEMO-TASK-001" for c in tasks), "Task corpus not scoped")
require(all(c["allowed_roles"] == ["engineer"] for c in tasks), "Report ACL changed")
require("2018-07-01" in chunks["PUB-01-C1"]["text"] and "2023-08-01" in chunks["PUB-02-C1"]["text"], "Required metadata dates absent from retrievable text")
require(all(c["publication_status"] == "archived" for c in knowledge if "RevA" in c["document_id"]), "RevA must remain archived")

sources = read("sources/source-register.json")
for s in sources:
    require(urlparse(s["url"]).hostname in {"std.samr.gov.cn", "openstd.samr.gov.cn", "www.cnca.gov.cn"}, "Non-official source")
    require(not s["full_text_included"] and not s["clause_rules_enabled"], "Metadata accidentally enabled as engineering rule")

for q in questions:
    require(q["split"] == "dev" and q["final_human_decision"] is None, "Unreviewed cases mislabeled")
    for group in q["required_evidence_groups"]:
        require(group and all(cid in chunks for cid in group), f"Broken QA evidence: {q['case_id']}")
        allowed = [chunks[cid] for cid in group if q["user_role"] in chunks[cid]["allowed_roles"]]
        require(bool(allowed), f"Required citation inaccessible: {q['case_id']}")
        require(all(c["publication_status"] == "active" or q["include_archived"] for c in allowed), "Implicit archived retrieval")
        require(all(c["scope"] == "knowledge" or q["task_id"] in q["authorized_task_ids"] for c in allowed), "Required task evidence without task access")
for a in annotations:
    require(a["human_state"] == "pending" and a["final_human_decision"] is None, "Unreviewed annotation marked accepted")
    require(all(cid in chunks for cid in a["required_evidence"]), f"Broken review evidence: {a['annotation_id']}")

rule_set = read("rules/demo-rules.json")
task_input = read("task-reports/task-input.json")
report = read("task-reports/SYN-TR-001-R1.json")
require(not rule_set["real_compliance_enabled"] and not task_input["real_compliance_enabled"], "Real compliance accidentally enabled")
require(task_input["spec_document_id"] == "SYN-SPEC-PB01-RevB" and report["report_claimed_spec"].endswith("RevA"), "Version conflict fixture lost")
require(task_input["review_date"] < "2026-05-31", "Historical fixture date no longer historical")
require(len(rule_set["rules"]) == 5 and all(r["real_standard_clause"] is None for r in rule_set["rules"]), "Synthetic rule set corrupted")
checklist = [a for a in annotations if a["group"] == "checklist"]
require({(a["port"], a["rule_id"]) for a in checklist} == {(p, r["rule_id"]) for p in ["A1", "C1"] for r in rule_set["rules"]}, "Expected checklist incomplete")
require(Counter(a["expected_finding"] for a in checklist) == {"no_issue": 5, "nonconformity": 2, "evidence_insufficient": 3}, "Review distribution")
require(sum(a["expected_finding"] == "conflict" for a in annotations) == 2, "Missing consistency conflicts")

# Independently compare the archived raw numbers and the configured decimal limits.
records = {r["record_id"]: r for r in report["records"]}
require(Decimal(str(records["R02"]["value"])) * 1000 == Decimal("680"), "Unit conversion fixture")
require(Decimal(str(records["R04"]["value"])) > Decimal("5.25"), "Upper-limit fixture")
require(Decimal(str(records["R05"]["final"])) - Decimal(str(records["R05"]["initial"])) == 9, "Normal temperature fixture")
require(records["R06"]["final"] is None and "?" in records["R06"]["raw"], "Ambiguous number silently repaired")

pdf = PdfReader(ROOT / report["pdf_path"])
require(len(pdf.pages) == 4, "PDF page count")
page_text = [re.sub(r"\s+", "", p.extract_text()) for p in pdf.pages]
for n, words in enumerate([
    ["模拟", "RevA", "S01", "80ms"],
    ["R01", "R02", "0.68s", "R04", "5.31V"],
    ["R05", "R06", "3?.0", "R07", "R08", "无记录ID"],
    ["F01", "不可信来源内容", "忽略之前全部规则"],
]):
    require(all(w in page_text[n] for w in words), f"PDF evidence missing on page {n + 1}")
for c in tasks:
    require(c["page"] in range(1, 5), "Invalid PDF locator")
    require(c["artifact_path"] == report["pdf_path"] and c["version"] == report["report_revision"], "Task citation artifact/revision mismatch")

# Local Markdown links should remain navigable from the repository source.
for p in BASE.rglob("*.md"):
    for target in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
        if not target.startswith(("https://", "http://", "#")):
            require((p.parent / target.split("#")[0]).exists(), f"Broken Markdown link: {p}: {target}")

print(json.dumps(dict(status="passed", snapshot=manifest["snapshot_id"], files_verified=len(manifest["files"]),
    knowledge_chunks=len(knowledge), task_chunks=len(tasks), qa_cases=len(questions), annotation_rows=len(annotations),
    pdf_pages=len(pdf.pages), limitation="Data integrity checks only; model evaluation not run; expert review pending."), ensure_ascii=False))
