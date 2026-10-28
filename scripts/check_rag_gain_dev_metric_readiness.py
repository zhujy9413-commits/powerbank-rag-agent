"""Check metric feasibility against labelled seed relevance, without running retrieval."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    if a.output.exists(): p.error("拒绝覆盖")
    rows = []
    for path in sorted((ROOT/"data/ai-work-rag-gain-dev-v0.1/reference-annotations").glob("*.json")):
        gold = json.loads(path.read_text())
        task = json.loads((ROOT/"data/ai-work-rag-gain-dev-v0.1/application-inputs"/gold["report_id"]/"task.json").read_text())
        corpus = [json.loads(s) for s in (ROOT/"data/ai-work-rag-gain-dev-v0.1/application-inputs"/gold["report_id"]/"chunks.jsonl").read_text().splitlines()]
        for q in gold["queries"]:
            for ns in ["requirement", "report"]:
                groups = q[ns+"_groups"]+(q["extra_required_groups"] if ns == "report" else [])
                if not groups: continue
                relevant = {key for g in groups for alt in g["alternatives"] for key in alt}
                candidates = sum(c["namespace"] == ns for c in corpus)
                denom = min(5, candidates)
                rows.append(dict(case_id=gold["case_id"], query_id=q["query_id"], namespace=ns,
                                 registered_relevant_seed_count=len(relevant), authorized_candidate_count=candidates,
                                 current_fixed_slot_denominator=denom,
                                 upper_bound_with_current_group_labels=min(len(relevant), 5)/denom,
                                 threshold=.8, query_source_fact_task=task["task_id"]))
    problem = [r for r in rows if r["upper_bound_with_current_group_labels"] < r["threshold"]]
    result = dict(kind="metric_feasibility_advisory_not_evaluation", rows=rows, positive_query_namespace_pairs=len(rows),
                  pairs_below_fixed_slot_threshold=len(problem), status="r02_scoring_definition_needs_resolution_before_effect_scoring",
                  condition="Upper bound assumes seed relevance equals the currently registered necessary-group sources. Any optional relevant sources require explicit separate qrels before scoring.",
                  recommended_amendment_not_applied="Precision@5 denominator = number of returned distinct seeds (up to 5), positive-query empty return = 0; retain >=80% and enforce completeness separately with R01/R03. Freeze seed qrels explicitly.",
                  protocol_changed=False, experiments_executed=0, model_requests=0)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["kind", "positive_query_namespace_pairs", "pairs_below_fixed_slot_threshold", "protocol_changed"]}))


if __name__ == "__main__": main()
