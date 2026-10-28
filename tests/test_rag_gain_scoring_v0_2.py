"""Hand-calculated scoring boundaries. Synthetic ranks only, no application calls."""
from copy import deepcopy
import unittest
from scripts.rag_gain_scoring_v0_2 import aggregate_r02, corpus_digest, score_r02, seed_from_chunk


class R02ContractTests(unittest.TestCase):
    def setUp(self):
        self.corpus = {}
        for i in range(1, 7):
            self.corpus[str(i)] = dict(chunk_id=str(i), text=f"人工原文{i}", namespace="report", source_role="report_observation",
                                      source_path="synthetic.pdf", page=1, section=f"R{i}", version="1", task_id="T1",
                                      conditions={"voltage_v":5}, allowed_roles=["engineer"], publication_status="active")
        self.q = dict(row_id="Q:report", namespace="report", task_id="T1", query_state="positive",
                      authorized_candidate_ids=list(self.corpus), seed_judgments={str(i):dict(label=int(i<=2),relevance_role="necessary_support" if i<=2 else "irrelevant") for i in range(1,7)},
                      necessary_groups=[dict(alternatives=[["1"]]),dict(alternatives=[["2"]])], corpus_snapshot_sha256=corpus_digest(self.corpus))

    def seeds(self, *ids): return [seed_from_chunk(self.corpus[i]) for i in ids]
    def score(self, raw, **kwargs): return score_r02(self.q, raw, self.corpus, **kwargs)

    def test_two_relevant_returned_is_one_not_two_fifths(self):
        r=self.score(self.seeds("1","2"));self.assertEqual((r["numerator"],r["denominator"],r["score"]),(2,2,1))
    def test_one_relevant_returned_does_not_prove_completeness(self):
        r=self.score(self.seeds("1"));self.assertEqual(r["score"],1);self.assertEqual(r["raw_group_coverage_diagnostic"],.5)
    def test_two_relevant_one_noise(self): self.assertAlmostEqual(self.score(self.seeds("1","3","2"))["score"],2/3)
    def test_empty_positive_is_zero(self): self.assertEqual(self.score([])["score"],0)
    def test_missing_execution_is_incomplete(self): self.assertEqual(self.score(None)["status"],"incomplete_missing_execution_record")
    def test_duplicate_occupies_slot(self): self.assertEqual(self.score(self.seeds("1","1","2"))["score"],2/3)
    def test_same_source_alias_cannot_inflate_hits(self):
        self.corpus["7"]=deepcopy(self.corpus["1"]);self.corpus["7"]["chunk_id"]="7"
        self.q["authorized_candidate_ids"].append("7");self.q["seed_judgments"]["7"]=dict(label=1,relevance_role="necessary_support")
        self.q["corpus_snapshot_sha256"]=corpus_digest(self.corpus)
        r=self.score(self.seeds("1","7"));self.assertEqual(r["score"],.5)
    def test_unknown_id_occupies_slot(self):
        s=self.seeds("1")[0];s["chunk_id"]="E404";r=self.score([s]+self.seeds("2"));self.assertEqual(r["score"],.5);self.assertIn("unknown_chunk_id",r["violations"])
    def test_reprinted_same_source_text_is_still_duplicate(self):
        self.corpus["2"]["text"]=self.corpus["1"]["text"];self.corpus["2"]["page"]=2
        self.q["corpus_snapshot_sha256"]=corpus_digest(self.corpus)
        self.assertEqual(self.score(self.seeds("1","2"))["score"],.5)
    def test_wrong_quote_occupies_slot(self):
        s=self.seeds("1")[0];s["quote"]="伪造引句";self.assertEqual(self.score([s]+self.seeds("2"))["score"],.5)
    def test_all_identity_dimensions_are_checked(self):
        for key in ["namespace","source_role","source_path","page","section","version","task_id","conditions"]:
            with self.subTest(field=key):
                s=self.seeds("1")[0];s[key]="错误";self.assertEqual(self.score([s])["score"],0)
    def test_unauthorized_actor_is_zero_and_flagged(self):
        r=self.score(self.seeds("1"),actor_role="employee");self.assertEqual(r["score"],0);self.assertIn("unauthorized_actor_role",r["violations"])
    def test_expansion_cannot_be_seed_precision(self):
        s=self.seeds("1")[0];s["kind"]="context_expansion";self.assertEqual(self.score([s])["score"],0)
    def test_overflow_retained_and_configuration_flagged(self):
        r=self.score(self.seeds("1","2","3","4","5","6"));self.assertEqual((r["denominator"],r["raw_returned_count"]),(5,6));self.assertIn("returned_more_than_five_seeds",r["violations"])
    def test_a0_not_empty_failure(self): self.assertEqual(self.score([],arm="A0")["status"],"not_applicable_no_supplemental_ranking")
    def test_model_arms_use_same_scoring(self):
        self.assertEqual(self.score(self.seeds("1","2"),arm="A3")["score"],self.score(self.seeds("1","2"),arm="A4")["score"])
    def test_changed_corpus_is_incomplete(self):
        self.corpus["1"]["text"]="新版本";self.assertEqual(self.score(self.seeds("1"))["status"],"incomplete_corpus_snapshot_mismatch")
    def test_unjudged_candidate_is_incomplete(self):
        del self.q["seed_judgments"]["6"];self.assertEqual(self.score(self.seeds("1"))["status"],"incomplete_unjudged_candidates")
    def test_disputed_label_is_incomplete(self):
        self.q["seed_judgments"]["6"]["label"]=None;self.assertEqual(self.score(self.seeds("1"))["status"],"incomplete_disputed_judgment")
    def negative(self):
        self.q["query_state"]="no_available_evidence";self.q["necessary_groups"]=[]
        for j in self.q["seed_judgments"].values():j["label"]=0
    def test_negative_is_not_precision_one_or_zero(self):
        self.negative();r=self.score([]);self.assertIsNone(r["score"]);self.assertIsNone(r["negative_converged"])
    def test_negative_raw_noise_may_be_rejected_correctly(self):
        self.negative();o=dict(state="evidence_insufficient",accepted_evidence_ids=[],absence_proof_citation=None,claims_test_not_performed=False)
        self.assertTrue(self.score(self.seeds("3"),negative_outcome=o)["negative_converged"])
    def test_negative_cannot_accept_noise_or_claim_physical_test_missing(self):
        self.negative();base=dict(state="evidence_insufficient",accepted_evidence_ids=[],absence_proof_citation=None,claims_test_not_performed=False)
        for key,value in [("state","no_issue"),("accepted_evidence_ids",["3"]),("absence_proof_citation","伪造缺失证明"),("claims_test_not_performed",True)]:
            with self.subTest(field=key):
                o={**base,key:value};self.assertFalse(self.score([],negative_outcome=o)["negative_converged"])
    def test_macro_fixed_query_weight_not_micro_slot_weight(self):
        q2={**deepcopy(self.q),"row_id":"Q2:report"}
        records={self.q["row_id"]:self.score(self.seeds("1")),q2["row_id"]:score_r02(q2,self.seeds("3","4","5","6"),self.corpus)}
        r=aggregate_r02([self.q,q2],records)["report"];self.assertEqual(r["macro_precision_returned_at_5"],.5)
    def test_macro_missing_does_not_shrink_denominator(self):
        q2={**deepcopy(self.q),"row_id":"Q2:report"}
        r=aggregate_r02([self.q,q2],{self.q["row_id"]:self.score(self.seeds("1"))})["report"]
        self.assertEqual(r["positive_query_denominator"],2);self.assertIsNone(r["macro_precision_returned_at_5"]);self.assertEqual(r["status"],"incomplete")
    def test_explicit_failed_empty_remains_in_macro(self):
        q2={**deepcopy(self.q),"row_id":"Q2:report"}
        r=aggregate_r02([self.q,q2],{self.q["row_id"]:self.score(self.seeds("1")),q2["row_id"]:score_r02(q2,[],self.corpus)})["report"]
        self.assertEqual(r["macro_precision_returned_at_5"],.5);self.assertEqual(r["positive_query_denominator"],2)
    def test_namespace_means_are_not_pooled(self):
        q2={**deepcopy(self.q),"row_id":"Q:requirement","namespace":"requirement"}
        r=aggregate_r02([self.q,q2],{self.q["row_id"]:self.score(self.seeds("1")),q2["row_id"]:dict(status="scored",score=0,violations=[])})
        self.assertEqual(r["report"]["macro_precision_returned_at_5"],1);self.assertEqual(r["requirement"]["macro_precision_returned_at_5"],0)


if __name__ == "__main__": unittest.main()
