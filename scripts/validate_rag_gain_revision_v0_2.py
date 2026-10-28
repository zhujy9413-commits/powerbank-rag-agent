"""R02 contract, qrels coverage and immutable-material audit; never run a retriever."""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.rag_gain_scoring_v0_2 import aggregate_r02, corpus_digest, score_r02, seed_from_chunk


def load(p):return json.loads(p.read_text(encoding="utf-8"))
def digest(p):return sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error("拒绝覆盖核验记录")
    checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    base=ROOT/"data/ai-work-rag-gain-v0.2"
    p=load(base/"protocol.json");old=load(ROOT/"data/ai-work-rag-gain-v0.1/protocol.json")
    ledger=load(base/"cases.json");qfile=load(base/"qrels-dev-v0.1.json");qrels=qfile["rows"]
    check("protocol_version_and_scope",p["protocol_id"]==ledger["protocol_id"]==qfile["protocol_id"]=="AIWORK-RAG-GAIN-0.2" and p["supersedes"]==old["protocol_id"])
    for key in ["baseline","scope","arms","sampling","retrieval","provider","run_plan","adoption"]:check("unchanged_contract:"+key,p[key]==old[key])
    for m in old["metrics"]:
        current=next(x for x in p["metrics"] if x["id"]==m["id"])
        if m["id"]!="R02":check("unchanged_metric:"+m["id"],current==m)
    r02=next(x for x in p["metrics"] if x["id"]=="R02")
    check("r02_threshold_still_80_percent",r02["threshold"]==.8)
    check("r02_actual_raw_return_denominator",r02["denominator"]=="min(5,len(raw_returned_seeds_before_validation_or_deduplication))")
    check("r02_applicability_and_zero_policy",r02["applies_to_arms"]==["A1","A2","A3","A4"] and r02["positive_empty_return_score"]==0 and r02["negative_query_score"] is None)
    check("qrels_hash_binding",digest(ROOT/p["qrels"]["path"])==p["qrels"]["sha256"])
    check("scorer_hash_binding",digest(ROOT/p["reference_scorer"]["path"])==p["reference_scorer"]["sha256"])
    check("material_manifest_hash_binding",digest(ROOT/p["dev_material_manifest"]["path"])==p["dev_material_manifest"]["sha256"])
    check("no_model_or_application_run",p["execution_status"]=="not_run" and p["model_requests_this_delivery"]==0 and p["candidate_chain_status"]=="not_implemented_not_frozen")
    check("48_ids_kept",len(ledger["cases"])==48 and {c["case_id"] for c in ledger["cases"]}=={c["case_id"] for c in load(ROOT/"data/ai-work-rag-gain-v0.1/cases.json")["cases"]})
    check("16_materialized_32_planned",Counter(c["status"] for c in ledger["cases"])==dict(material_verified_application_not_executed=16,planned_not_materialized=32))
    check("all_case_results_empty",all(c["observed_result"] is None for c in ledger["cases"]))
    for path,expected in p["baseline"]["source_sha256"].items():check("baseline_unchanged:"+path,digest(ROOT/path)==expected)
    manifest=load(ROOT/p["dev_material_manifest"]["path"])
    for path,expected in manifest["asset_sha256"].items():check("dev_material_unchanged:"+path,digest(ROOT/path)==expected)
    for group in ["review-holdout-v0.1","p0-holdout-v0.1","p1-holdout-v0.1"]:
        for path,expected in load(ROOT/"data"/group/"freeze.json")["asset_sha256"].items():check("old_frozen_unchanged:"+path,digest(ROOT/path)==expected)
    check("original_zip_unchanged",digest(ROOT/"output/packages/ai-work-rag-gain-dev-v0.1.zip")=="34220560d3fcd9b1f8299308204703e91a0a9c4b96c992639259eee1f6726245")
    original_commit="a1c58946d604a672e6745f6c136a01c5339fd527"
    paths=subprocess.check_output(["git","ls-tree","-r","--name-only",original_commit,"eval-results","data/ai-work-rag-gain-v0.1"],cwd=ROOT).decode().splitlines()
    for path in paths:
        original=subprocess.check_output(["git","show",original_commit+":"+path],cwd=ROOT)
        check("historical_record_unchanged:"+path,digest(ROOT/path)==sha256(original).hexdigest())
    check("248_unique_query_namespace_rows",len(qrels)==len({q["row_id"] for q in qrels})==248)
    check("245_positive_3_negative",Counter(q["query_state"] for q in qrels)==dict(positive=245,no_available_evidence=3))
    check("labels_evaluator_only",qfile["gold_visible_to_application"] is False and qfile["optional_relevant_seed_labels"]==0)
    for path,expected in qfile["source_sha256"].items():check("qrel_source_binding:"+path,digest(ROOT/path)==expected)
    examples=[];records={};old_unreachable=0;judgment_cells=0
    for q in qrels:
        key=q["row_id"]
        corpus={c["chunk_id"]:c for c in [json.loads(s) for s in (ROOT/q["corpus_path"]).read_text().splitlines()]}
        source=load(ROOT/"data/ai-work-rag-gain-dev-v0.1/reference-annotations"/(q["report_id"]+".json"))
        source_query=next(x for x in source["queries"] if x["query_id"]==q["query_id"])
        expected_groups=source_query[q["namespace"]+"_groups"]+(source_query["extra_required_groups"] if q["namespace"]=="report" else [])
        relevant={k for g in expected_groups for a in g["alternatives"] for k in a}
        judgments=q["seed_judgments"];judgment_cells+=len(judgments)
        universe={k for k,c in corpus.items() if c["namespace"]==q["namespace"]}
        check("exhaustive_seed_judgments:"+key,set(judgments)==set(q["authorized_candidate_ids"])==universe and all(x["label"] in [0,1] for x in judgments.values()))
        check("bound_corpus_digest:"+key,corpus_digest(corpus)==q["corpus_snapshot_sha256"])
        check("necessary_groups_preserved:"+key,q["necessary_groups"]==expected_groups)
        check("positive_seeds_not_invented:"+key,{k for k,j in judgments.items() if j["label"]==1}==relevant)
        check("text_hashes_and_authorization:"+key,all(j["text_sha256"]==sha256(corpus[k]["text"].encode()).hexdigest() and q["actor_role"] in corpus[k]["allowed_roles"] and corpus[k]["task_id"]==q["task_id"] for k,j in judgments.items()))
        check("distractors_not_relevant:"+key,all(j["label"]==0 for k,j in judgments.items() if re.search(r"-N\d{2}$",k)))
        if relevant:
            ids=sorted(relevant)[:5]
            result=score_r02(q,[seed_from_chunk(corpus[k]) for k in ids],corpus,arm="A2")
            old_ceiling=min(5,len(relevant))/min(5,len(universe))
            old_unreachable+=old_ceiling<.8
            check("ideal_arithmetic_reachable:"+key,result["status"]=="scored" and result["score"]==1 and not result["violations"])
            check("ideal_groups_complete:"+key,result["raw_group_coverage_diagnostic"]==1)
            examples.append(dict(row_id=key,kind="gold_constructed_ideal_list_not_retrieval",old_fixed_slot_upper_bound=old_ceiling,new_actual_return_score=result["score"],returned=len(ids)))
        else:
            noise=next(iter(universe))
            outcome=dict(state="evidence_insufficient",accepted_evidence_ids=[],absence_proof_citation=None,claims_test_not_performed=False)
            result=score_r02(q,[seed_from_chunk(corpus[noise])],corpus,negative_outcome=outcome)
            check("negative_not_precision_score:"+key,result["score"] is None and result["negative_converged"] is True)
        records[key]=result
    check("old_fixed_slot_issue_reproduced",old_unreachable==245)
    macro=aggregate_r02(qrels,records)
    check("ideal_namespaces_separate",macro["requirement"]["positive_query_denominator"]==124 and macro["report"]["positive_query_denominator"]==121 and all(x["macro_precision_returned_at_5"]==1 for x in macro.values()))
    check("three_negative_abstentions_separate",macro["report"]["negative_query_denominator"]==3 and macro["report"]["negative_correct"]==3)
    # Real material identities: equal values cannot swap ports; contrast/background keep their roles.
    port=next(q for q in qrels if q["row_id"]=="RG-PORT-DEV-01:A1-01:report")
    check("equal_value_other_port_is_irrelevant",port["seed_judgments"]["D805-R80506"]["label"]==0 and port["seed_judgments"]["D805-R80501"]["label"]==1)
    for cid,prefix in [("RG-CONDITION-DEV-01","D807"),("RG-CONDITION-DEV-02","D808")]:
        contrast=[q for q in qrels if q["case_id"]==cid and q["namespace"]=="report" and q["seed_judgments"][prefix+"-OTHER"]["label"]==1]
        check("contrast_only_two_registered_queries:"+cid,len(contrast)==2 and all(q["seed_judgments"][prefix+"-OTHER"]["relevance_role"]=="contrast_only" for q in contrast))
    background=[q for q in qrels if q["case_id"]=="RG-NOISE-DEV-02" and q["namespace"]=="report" and q["seed_judgments"]["D812-BACKGROUND"]["label"]==1]
    check("background_not_measurement",len(background)==1 and background[0]["query_id"]=="BACKGROUND-CONSISTENCY" and background[0]["seed_judgments"]["D812-BACKGROUND"]["relevance_role"]=="background_claim_only")
    docs=["docs/ai-work/rag-gain-validation-plan-v0.1.md","docs/ai-work/rag-gain-evaluation-checklist-v0.1.md"]
    for path in docs:
        text=(ROOT/path).read_text()
        check("current_version_in_doc:"+path,"版本v0.2" in text and "前5条实际返回精度" in text)
        for link in re.findall(r"\]\(([^)]+)\)",text):
            if not link.startswith(("https://","http://","#")):check("local_doc_link:"+path+":"+link,((ROOT/path).parent/link).resolve().is_file())
    checklist=(ROOT/docs[1]).read_text()
    for c in ledger["cases"]:check("all_48_checklist_rows:"+c["case_id"],checklist.count("| "+c["case_id"]+" · ")==1)
    log=(ROOT/"eval-results/rag-gain-r02-scoring-tests-v0.2.txt").read_text()
    check("26_reference_contract_tests_passed","Ran 26 tests" in log and log.rstrip().endswith("OK"))
    result=dict(kind="r02_contract_and_material_binding_validation_not_rag_evaluation",date="2026-10-29",protocol_id=p["protocol_id"],checks=checks,
                passed=sum(c["passed"] for c in checks),total=len(checks),reference_contract_tests=26,
                qrel_rows=248,positive_query_namespace_pairs=245,negative_query_namespace_pairs=3,judgment_cells=judgment_cells,
                old_unreachable_positive_pairs=old_unreachable,ideal_constructed_examples=examples,ideal_macro_diagnostic=macro,
                actual_retrieval_runs=0,application_runs=0,provider_requests=0,holdout_materialized=0,
                expert_review="pending_same_author_internal_annotations",candidate_integration="pending",
                current_asset_sha256={path:digest(ROOT/path) for path in docs+["data/ai-work-rag-gain-v0.2/protocol.json","data/ai-work-rag-gain-v0.2/cases.json","data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json","scripts/rag_gain_scoring_v0_2.py","tests/test_rag_gain_scoring_v0_2.py"]})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["kind","passed","total","reference_contract_tests","qrel_rows","judgment_cells","actual_retrieval_runs","provider_requests"]}))
    failures=[c for c in checks if not c["passed"]]
    if failures:print(json.dumps(failures,ensure_ascii=False));raise SystemExit(1)


if __name__=="__main__":main()
