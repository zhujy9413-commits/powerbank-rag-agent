"""Bind the R02 correction to existing immutable development material."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"data/ai-work-rag-gain-v0.2"
DEV = ROOT/"data/ai-work-rag-gain-dev-v0.1"


def read(p): return json.loads(p.read_text(encoding="utf-8"))
def digest(p): return sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def dump(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    if OUT.exists(): raise SystemExit("拒绝覆盖协议修订与相关性标注。")
    OUT.mkdir()
    qrels = []
    inputs = {}
    for path in sorted((DEV/"reference-annotations").glob("*.json")):
        g = read(path)
        base = DEV/"application-inputs"/g["report_id"]
        task = read(base/"task.json")
        corpus = [json.loads(s) for s in (base/"chunks.jsonl").read_text().splitlines()]
        inputs[rel(path)] = digest(path)
        for file in [base/"task.json", base/"chunks.jsonl"]: inputs[rel(file)] = digest(file)
        for q in g["queries"]:
            for ns in ["requirement", "report"]:
                groups = deepcopy(q[ns+"_groups"])+(deepcopy(q["extra_required_groups"]) if ns == "report" else [])
                universe = [c["chunk_id"] for c in corpus if c["namespace"] == ns]
                positive = {key for group in groups for alt in group["alternatives"] for key in alt}
                contrast = {key for group in q["extra_required_groups"] for alt in group["alternatives"] for key in alt} if ns == "report" else set()
                if q["query_id"] == "CONDITION-CONSISTENCY":
                    contrast |= {key for group in groups if group["group_id"] == "other-condition" for alt in group["alternatives"] for key in alt}
                judgments = {}
                for c in [c for c in corpus if c["namespace"] == ns]:
                    key = c["chunk_id"]; label = int(key in positive)
                    role = "contrast_only" if key in contrast else "necessary_support" if label else "irrelevant"
                    if label and c["source_role"] == "background": role = "background_claim_only"
                    if label and c["source_role"] == "report_declaration": role = "report_version_declaration_only"
                    if label and c["source_role"] == "report_context": role = "context_required"
                    judgments[key] = dict(label=label, relevance_role=role,
                                          reason="已核验必要组中的可引用片段；单片段相关不等于证据齐备" if label else "不支持本查询；含无关附件、其他字段/端口或非本项版本声明",
                                          optional_relevance=False, text_sha256=sha256(c["text"].encode()).hexdigest())
                qrels.append(dict(row_id=g["case_id"]+":"+q["query_id"]+":"+ns, case_id=g["case_id"], report_id=g["report_id"],
                                  query_id=q["query_id"], task_id=task["task_id"], namespace=ns,
                                  query_state="positive" if positive else "no_available_evidence",
                                  authorized_candidate_ids=universe, seed_judgments=judgments, necessary_groups=groups,
                                  actor_role=task["actor_role"], corpus_path=rel(base/"chunks.jsonl"),
                                  corpus_snapshot_sha256=sha256(json.dumps({c["chunk_id"]:c for c in corpus},sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()))
    qrel_file = OUT/"qrels-dev-v0.1.json"
    dump(qrel_file, dict(qrels_id="R02-DEV-QRELS-0.1", protocol_id="AIWORK-RAG-GAIN-0.2", status="development_qrels_bound",
                         annotation_review="same_author_internal_not_external_or_expert", optional_relevant_seed_labels=0,
                         rationale="逐一登记当前授权候选的种子相关性；本版保守采用已核验必要组。未增加片段、复制切块或改写旧必要组。对照条件与背景声明只支持指定对照问题，不替代当前工况测量。",
                         gold_visible_to_application=False, source_sha256=inputs, rows=qrels))
    old = read(ROOT/"data/ai-work-rag-gain-v0.1/protocol.json")
    protocol = deepcopy(old)
    protocol.update(protocol_id="AIWORK-RAG-GAIN-0.2", supersedes="AIWORK-RAG-GAIN-0.1",
                    sample_status="dev_material_verified_holdout_unmaterialized", sample_freeze_status="dev_material_locked_candidate_pending",
                    revision_scope="R02 denominator, raw ranking integrity, explicit seed qrels, applicability and aggregation; other metric thresholds unchanged",
                    dev_material_manifest=dict(path=rel(DEV/"material-manifest.json"), sha256=digest(DEV/"material-manifest.json")),
                    qrels=dict(path=rel(qrel_file), sha256=digest(qrel_file)), candidate_chain_status="not_implemented_not_frozen")
    protocol["reference_scorer"] = dict(path="scripts/rag_gain_scoring_v0_2.py", sha256=digest(ROOT/"scripts/rag_gain_scoring_v0_2.py"),
                                        source_fingerprint_fields=["source_path", "version", "source_role", "text"],
                                        integration_status="reference_contract_only_not_application_integrated")
    r02 = next(m for m in protocol["metrics"] if m["id"] == "R02")
    r02.update(name="补充种子实际返回精度", unit="macro_precision_returned_at_5",
               criterion="A1-A4 each namespace, each holdout repetition: macro relevant first-five raw seed slots / returned first-five raw seed slots >=0.80. Empty positive return=0. Negative queries separate. R01/R03 and redlines still mandatory.",
               applies_to_arms=["A1", "A2", "A3", "A4"], a0_status="not_applicable_no_supplemental_ranking",
               denominator="min(5,len(raw_returned_seeds_before_validation_or_deduplication))",
               positive_empty_return_score=0, negative_query_score=None,
               duplicate_policy="duplicate chunk ID or source fingerprint occupies slot, relevance=0; do not pre-deduplicate",
               invalid_slot_policy="unknown, unauthorized, mismatched namespace/task/role/version/locator/condition/quote, or expansion mislabeled as seed occupy slot and score 0; flag independent control violations",
               expansion_policy="excluded from seed precision; naturally retrieved header seeds may be relevant if qrel says so",
               overflow_policy="score first five, retain full raw list; >5 is configuration violation and blocks valid experiment acceptance",
               aggregation="fixed positive query denominator per namespace and repetition; missing run/log or disputed label=incomplete, explicit executed empty/failure=0; do not pool namespaces/repetitions",
               negative_policy="not in precision macro; require recorded evidence_insufficient, no accepted evidence/absence-proof quote or claim that physical test was not performed; raw noise may exist but must be rejected",
               contrast_policy="only pre-labelled contrast_only sources support contrast; never substitute a different condition for current-condition measurement",
               generation_arms="A3/A4 reuse raw A1/A2 seed rankings; generation repair cannot delete or reorder retrieval errors")
    dump(OUT/"protocol.json", protocol)
    ledger = read(ROOT/"data/ai-work-rag-gain-v0.1/cases.json")
    ledger.update(protocol_id=protocol["protocol_id"], status="16_dev_material_verified_32_holdout_planned_results_not_run")
    material = {c["case_id"]: c for c in read(DEV/"cases.json")["cases"]}
    for c in ledger["cases"]:
        if c["case_id"] in material:
            m=material[c["case_id"]]
            c.update(status="material_verified_application_not_executed", fixture_path=m["fixture_path"], fixture_sha256=m["fixture_sha256"], family_id=m["family_id"], annotation_reviewer="same_author_internal_material_review")
            c["expected_evidence_groups"] = m.get("annotation_path")
            c["r02_qrels"] = rel(qrel_file) if c["kind"] == "content_report" else None
    dump(OUT/"cases.json", ledger)
    print(json.dumps(dict(protocol=protocol["protocol_id"], query_namespace_rows=len(qrels), positive=sum(q["query_state"] == "positive" for q in qrels), negative=sum(q["query_state"] != "positive" for q in qrels), model_requests=0)))


if __name__ == "__main__": main()
