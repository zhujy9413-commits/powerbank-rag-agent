"""Reference R02 arithmetic/identity contract. No retrieval, application or provider calls.

Input is the unedited supplementary seed ranking. Never pre-deduplicate or remove
bad slots before calling this evaluator. Qrels belong to the evaluator only.
"""
from copy import deepcopy
from hashlib import sha256
import json

IDENTITY = ("namespace", "source_role", "source_path", "page", "section", "version", "task_id", "conditions")


def seed_from_chunk(chunk):
    return dict(chunk_id=chunk["chunk_id"], kind="seed", quote=chunk["text"],
                **{k: deepcopy(chunk[k]) for k in IDENTITY})


def source_fingerprint(chunk):
    fields = ("source_path", "version", "source_role", "text")
    return sha256(json.dumps({k: chunk[k] for k in fields}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def corpus_digest(corpus):
    return sha256(json.dumps(corpus, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def score_r02(qrel, raw_seeds, corpus, *, arm="A2", actor_role="engineer", negative_outcome=None):
    if arm not in ["A0", "A1", "A2", "A3", "A4"]:
        raise ValueError("未知实验组")
    if arm == "A0":
        return dict(status="not_applicable_no_supplemental_ranking", score=None, denominator=None)
    if raw_seeds is None:
        return dict(status="incomplete_missing_execution_record", score=None, denominator=None)
    if not isinstance(raw_seeds, list):
        raise ValueError("raw_seeds必须是原始有序列表；缺日志用None，已执行空返回用[]")
    if corpus_digest(corpus) != qrel["corpus_snapshot_sha256"]:
        return dict(status="incomplete_corpus_snapshot_mismatch", score=None, denominator=None)
    universe = set(qrel["authorized_candidate_ids"])
    judgments = qrel["seed_judgments"]
    if set(judgments) != universe:
        return dict(status="incomplete_unjudged_candidates", score=None, denominator=None)
    if not universe <= set(corpus):
        return dict(status="incomplete_corpus_snapshot_mismatch", score=None, denominator=None)
    if any(j["label"] not in [0, 1] for j in judgments.values()):
        return dict(status="incomplete_disputed_judgment", score=None, denominator=None)
    violations = []
    if len(raw_seeds) > 5: violations.append("returned_more_than_five_seeds")
    seen_ids, seen_sources = set(), set()
    slots, valid_ids = [], set()
    for rank, seed in enumerate(raw_seeds[:5], 1):
        errors = []
        if not isinstance(seed, dict): seed = {}; errors.append("malformed_seed")
        ident = seed.get("chunk_id")
        c = corpus.get(ident)
        if seed.get("kind") != "seed": errors.append("expansion_or_non_seed_in_seed_ranking")
        if not c: errors.append("unknown_chunk_id")
        else:
            if actor_role not in c["allowed_roles"]: errors.append("unauthorized_actor_role")
            if c["publication_status"] != "active": errors.append("inactive_source")
            if ident not in universe: errors.append("wrong_namespace_or_candidate_scope")
            for key in IDENTITY:
                if seed.get(key) != c[key]: errors.append("identity_mismatch:"+key)
            if c["task_id"] != qrel["task_id"]: errors.append("foreign_task_source")
            if c["namespace"] != qrel["namespace"]: errors.append("wrong_namespace_source")
            if seed.get("quote") != c["text"]: errors.append("quote_not_exact")
            fingerprint = source_fingerprint(c)
            if ident in seen_ids or fingerprint in seen_sources: errors.append("duplicate_seed_or_source")
            seen_ids.add(ident); seen_sources.add(fingerprint)
        relevant = not errors and judgments[ident]["label"] == 1
        if not errors: valid_ids.add(ident)
        slots.append(dict(rank=rank, chunk_id=ident, relevant=bool(relevant), errors=errors,
                          relevance_role=judgments.get(ident, {}).get("relevance_role")))
        for error in errors:
            if error != "duplicate_seed_or_source": violations.append(error)
    positives = {key for key, j in judgments.items() if j["label"] == 1}
    if qrel["query_state"] == "no_available_evidence":
        outcome = negative_outcome or {}
        converged = (outcome.get("state") == "evidence_insufficient" and
                     outcome.get("accepted_evidence_ids") == [] and
                     outcome.get("absence_proof_citation") is None and
                     outcome.get("claims_test_not_performed") is False)
        return dict(status="negative_query_separate", score=None, denominator=None, numerator=None,
                    raw_returned_count=len(raw_seeds), slots=slots, violations=violations,
                    negative_outcome_recorded=negative_outcome is not None,
                    negative_converged=converged if negative_outcome is not None else None)
    if not positives: return dict(status="incomplete_positive_query_without_labels", score=None, denominator=None)
    denominator = len(slots)
    numerator = sum(s["relevant"] for s in slots)
    groups = qrel["necessary_groups"]
    covered = sum(any(set(alt) <= valid_ids for alt in group["alternatives"]) for group in groups)
    return dict(status="scored", score=numerator/denominator if denominator else 0.0,
                numerator=numerator, denominator=denominator, raw_returned_count=len(raw_seeds),
                empty_positive_return=denominator == 0, slots=slots, violations=violations,
                raw_necessary_groups_covered=covered, raw_necessary_groups_total=len(groups),
                raw_group_coverage_diagnostic=covered/len(groups) if groups else None)


def aggregate_r02(qrels, execution_records):
    """Fixed macro denominators per namespace. Missing records never disappear."""
    result = {}
    for namespace in ["requirement", "report"]:
        target = [q for q in qrels if q["namespace"] == namespace]
        positive = [q for q in target if q["query_state"] == "positive"]
        negative = [q for q in target if q["query_state"] == "no_available_evidence"]
        scored = [execution_records.get(q["row_id"]) for q in positive]
        complete = all(s and s["status"] == "scored" for s in scored)
        mean = sum(s["score"] for s in scored)/len(positive) if complete and positive else None
        neg = [execution_records.get(q["row_id"]) for q in negative]
        negative_complete = all(s and s["status"] == "negative_query_separate" and s["negative_outcome_recorded"] for s in neg)
        neg_ok = sum(s["negative_converged"] is True for s in neg) if negative_complete else None
        any_violations = any(s and s.get("violations") for s in scored+neg)
        result[namespace] = dict(positive_query_denominator=len(positive), observed_positive_results=sum(bool(s and s["status"] == "scored") for s in scored),
                                 macro_precision_returned_at_5=mean, precision_threshold=.8,
                                 precision_gate_passed=mean >= .8 if mean is not None else None,
                                 ranking_contract_passed=not any_violations if complete and negative_complete else None,
                                 negative_query_denominator=len(negative), negative_correct=neg_ok,
                                 negative_convergence_rate=neg_ok/len(negative) if negative_complete and negative else None,
                                 status="complete" if complete and negative_complete else "incomplete",
                                 invalid_ranking_or_identity_observed=any_violations,
                                 acceptance_note="R02 arithmetic alone never grants adoption; R01/R03 and safety/performance/cost gates remain mandatory.")
    return result
