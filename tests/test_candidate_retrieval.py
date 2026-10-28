from copy import deepcopy
import math
from pathlib import Path
import unittest

from app.ai_work.candidate import (CandidateRetriever, RetrievalConfig, augment_baseline,
    controlled_explanation, digest, normalized_vectors, rrf, seed)
from app.ai_work.candidate_inputs import load_input
from app.knowledge_assistant.core import Principal


class Embedder:
    identity = "offline-test-vector-v1"
    def __init__(self):self.calls=[]
    def embed(self,texts):
        self.calls.append(list(texts))
        return dict(model_id=self.identity,vectors=[[1.0]+[0.0]*15 for _ in texts])


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.task=dict(task_id="T",task_authorized=True,selected_requirement_chunks=["REQ"],selected_versions={"REQ":"B"})
        self.user=Principal("u","engineer",("T",))
        self.query=dict(text="A1 保护响应 输出 5 V 单口",port="A1",field="response",conditions=dict(voltage_v=5,electrical_role="输出",combination="单口"))
        def chunk(i,text,ns="report",role="report_observation",**kw):
            return dict(chunk_id=i,text=text,namespace=ns,source_role=role,source_path=i+".txt",page=1,
                section=i,version="B",publication_status="active",material_type="synthetic",allowed_roles=["engineer"],
                task_id="T",conditions=deepcopy(self.query["conditions"]),context_ids=[],**kw)
        self.chunks=[chunk("REQ","保护响应要求", "requirement", "selected_requirement"),
                     chunk("R1","R01 A1 保护响应 250 ms"),chunk("R2","R02 C1 保护响应 250 ms"),
                     chunk("CTX","输出 5 V 单口测试条件",role="report_context")]
        self.chunks[1]["context_ids"]=["CTX"]
        self.originals={(c["source_path"],1):c["text"] for c in self.chunks}

    def make(self,embedder=None):return CandidateRetriever(self.chunks,self.task,self.user,self.originals,embedder=embedder,config=RetrievalConfig(structured_routing=False))
    def test_namespaces_never_mix(self):
        r=self.make()
        for ns in ["report","requirement"]:
            got=r.retrieve(self.query,ns);self.assertTrue(all(s["namespace"]==ns for s in got["raw_seeds"]+got["context_expansions"]))
    def test_wrong_port_not_accepted_even_equal_numbers(self):
        r=self.make().retrieve(self.query,"report");self.assertNotIn("R2",[s["chunk_id"] for s in r["accepted"]])
        self.assertIn("R2",[x["chunk_id"] for x in r["rejected"]])
    def test_other_condition_preserved_only_as_contrast(self):
        self.chunks[1]["conditions"]["voltage_v"]=9
        r=self.make().retrieve(self.query,"report")
        self.assertEqual(next(s for s in r["accepted"] if s["chunk_id"]=="R1")["evidence_use"],"condition_contrast_only")
    def test_no_measurement_keeps_no_evidence_and_no_absence_quote(self):
        self.query["port"]="A9" # unsupported identities reject before searching
        with self.assertRaises(ValueError):self.make().retrieve(self.query,"report")
        self.query["port"]="A1";self.query["field"]="appearance"
        r=self.make().retrieve(self.query,"report")
        self.assertEqual(r["outcome"]["state"],"evidence_insufficient");self.assertIsNone(r["outcome"]["absence_proof_citation"])
    def test_extensions_only_use_registered_authorized_ids(self):
        self.chunks[1]["context_ids"]=["MISSING"]
        r=self.make().retrieve(self.query,"report");self.assertEqual(r["context_expansions"],[])
    def test_unknown_id_wrong_quote_or_any_identity_cannot_verify(self):
        r=self.make();s=seed(self.chunks[1]);self.assertTrue(r.verify(s,"report"))
        for k in ["chunk_id","quote","namespace","source_role","source_path","page","section","version","task_id","conditions"]:
            with self.subTest(field=k):
                x=deepcopy(s);x[k]="forged";self.assertFalse(r.verify(x,"report"))
    def test_source_text_not_locatable_never_indexed_or_sent(self):
        self.originals[("R1.txt",1)]="unrelated";e=Embedder();r=self.make(e).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(r["trace"]["source_validation_rejections"],1)
        self.assertNotIn(self.chunks[1]["text"],e.calls[0])
    def test_whitespace_wrapped_pdf_quote_is_locatable(self):
        self.originals[("R1.txt",1)]="R01 A1 保\n护响应 250 ms"
        self.assertTrue(self.make().verify(seed(self.chunks[1]),"report"))
    def test_permission_filter_precedes_embedding_and_logs(self):
        self.chunks[1]["allowed_roles"]=["other"];self.chunks[1]["text"]="FORBIDDEN_SECRET"
        self.originals[("R1.txt",1)]="FORBIDDEN_SECRET";e=Embedder();r=self.make(e).retrieve(self.query,"report",method="hybrid")
        import json
        self.assertNotIn("FORBIDDEN_SECRET",json.dumps([r,e.calls]))
    def test_foreign_task_never_indexed(self):
        self.chunks[1]["task_id"]="FOREIGN";e=Embedder();r=self.make(e).retrieve(self.query,"report",method="hybrid")
        self.assertNotIn(self.chunks[1]["text"],e.calls[0])
    def test_selected_inactive_source_blocks_before_provider(self):
        self.chunks[0]["publication_status"]="archived";e=Embedder()
        with self.assertRaises(PermissionError):self.make(e).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(e.calls,[])
    def test_selected_wrong_version_blocks(self):
        self.chunks[0]["version"]="A"
        with self.assertRaises(PermissionError):self.make().retrieve(self.query,"report")
    def test_revoked_task_blocks_cached_retrieval(self):
        r=self.make(Embedder());r.retrieve(self.query,"report",method="hybrid");r.task["task_authorized"]=False
        with self.assertRaises(PermissionError):r.retrieve(self.query,"report",method="hybrid")
    def test_cache_binds_role_source_and_model_and_never_query_results(self):
        e=Embedder();r=self.make(e)
        r.retrieve(self.query,"report",method="hybrid");r.retrieve(self.query,"report",method="hybrid")
        self.assertEqual(len(e.calls),3)
        e.identity="offline-test-v2";r.retrieve(self.query,"report",method="hybrid");self.assertEqual(len(e.calls),5)
        r.chunks[1]["publication_status"]="archived";r.retrieve(self.query,"report",method="hybrid");self.assertEqual(len(e.calls),7)
    def test_hybrid_real_fusion_with_injected_vectors(self):
        r=self.make(Embedder()).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(r["effective_method"],"bm25_embedding_rrf");self.assertIsNone(r["degradation"])
        self.assertEqual(r["trace"]["embedder_calls"],2)
    def test_unconfigured_hybrid_explicitly_degrades_to_keyword(self):
        r=self.make();a=r.retrieve(self.query,"report");b=r.retrieve(self.query,"report",method="hybrid")
        self.assertEqual(a["raw_seeds"],b["raw_seeds"]);self.assertEqual(b["degradation"],"embedding_not_configured")
    def test_embedding_failure_falls_back_without_leaking_exception(self):
        e=Embedder()
        def fail(texts):raise RuntimeError("secret-api-key")
        e.embed=fail;r=self.make(e).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(r["effective_method"],"bm25");self.assertNotIn("secret-api-key",str(r))
    def test_query_model_drift_invalidates_index_and_falls_back(self):
        e=Embedder();original=e.embed
        def drift(texts):
            response=original(texts)
            if len(e.calls)>1:response["model_id"]="changed"
            return response
        e.embed=drift;r=self.make(e).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(r["degradation"],"embedding_failure_or_identity_drift")
    def test_bad_vectors_rejected(self):
        for v in [[],[[0]*16],[[float("nan")]*16],[[True]*16],[[1]*15],[[1]*16,[1]*17]]:
            with self.subTest(value=str(v)[:20]),self.assertRaises(ValueError):normalized_vectors(v,1 if len(v)!=2 else 2)
    def test_rrf_scores_and_stable_ties(self):
        order,s=rrf(["B","A"],["A","B"])
        self.assertEqual(order,["A","B"]);self.assertAlmostEqual(s["A"],1/61+1/62)
    def test_limit_config_and_duplicate_corpus(self):
        with self.assertRaises(ValueError):RetrievalConfig(top_k=6)
        self.chunks.append(deepcopy(self.chunks[1]))
        with self.assertRaises(ValueError):self.make()
    def test_augmentation_preserves_entire_original_payload(self):
        a=dict(result="not_checked",value=None,history=[1],conditions=dict(unknown=True));before=deepcopy(a)
        r=augment_baseline(a,[self.make().retrieve(self.query,"report")]);self.assertEqual(a,before)
        self.assertEqual({k:v for k,v in r.items() if k!="candidate_retrieval"},a)
    def test_input_directory_allowlist(self):
        with self.assertRaises(ValueError):load_input(Path("/tmp/unknown"),Path.cwd())

    def routed(self,embedder=None):
        return CandidateRetriever(self.chunks,self.task,self.user,self.originals,embedder=embedder)
    def test_routing_uses_object_and_field_before_both_methods(self):
        e=Embedder();r=self.routed(e).retrieve(self.query,"report",method="hybrid")
        self.assertNotIn("R2",[s["chunk_id"] for s in r["raw_seeds"]])
        self.assertNotIn(self.chunks[2]["text"],e.calls[0])
    def test_routing_keeps_conditions_and_registered_header(self):
        self.chunks[1]["context_ids"]=["CTX"]
        r=self.routed().retrieve(self.query,"report")
        self.assertIn("CTX",[s["chunk_id"] for s in r["raw_seeds"]+r["context_expansions"]])
    def test_routing_appearance_requirement_uses_observation_vocabulary(self):
        self.chunks[0]["text"]="每个端口分别有明确的无起火、无爆炸、无漏液记录。"
        self.originals[("REQ.txt",1)]=self.chunks[0]["text"]
        self.query.update(field="appearance",text="A1 外观观察")
        r=self.routed().retrieve(self.query,"requirement")
        self.assertEqual(r["raw_seeds"][0]["chunk_id"],"REQ")
    def test_routing_temperature_requirement_uses_temperature_difference(self):
        self.chunks[0]["text"]="末值减起值；温差上限。";self.originals[("REQ.txt",1)]=self.chunks[0]["text"]
        self.query.update(field="temperature",text="A1 壳温")
        self.assertEqual(self.routed().retrieve(self.query,"requirement")["raw_seeds"][0]["chunk_id"],"REQ")
    def test_routing_can_disable_for_exact_development_ablation(self):
        self.assertTrue(any(s["chunk_id"]=="R2" for s in self.make().retrieve(self.query,"report")["raw_seeds"]))
        self.assertFalse(any(s["chunk_id"]=="R2" for s in self.routed().retrieve(self.query,"report")["raw_seeds"]))
    def test_empty_route_has_no_embedding_call(self):
        e=Embedder();self.query.update(field="appearance",text="A1 外观观察")
        r=self.routed(e).retrieve(self.query,"report",method="hybrid")
        self.assertEqual(e.calls,[]);self.assertEqual(r["degradation"],"no_eligible_candidates")
    def test_malformed_conditions_rejected(self):
        self.query["conditions"]="guess"
        with self.assertRaises(ValueError):self.routed().retrieve(self.query,"report")


class ExplanationContractTests(unittest.TestCase):
    def test_two_fabricated_attempts_fall_back_and_remain_auditable(self):
        r=controlled_explanation({"result":"conflict"},[{"id":"E1"}],lambda **kw:dict(explanation="draft",citation_ids=["E404"]),now_ms=lambda:0)
        self.assertEqual(r["terminal"],"template_fallback");self.assertEqual(len(r["attempts"]),2)
        self.assertEqual(r["attempts"][0]["raw_response"]["citation_ids"],["E404"])
    def test_timeout_respects_remaining_total_budget(self):
        clock=[30000]
        def provider(**kw):self.assertEqual(kw["timeout_ms"],15000);clock[0]+=15000;raise TimeoutError()
        r=controlled_explanation({"result":"not_checked"},[{"id":"E1"}],provider,now_ms=lambda:clock[0])
        self.assertEqual(len(r["attempts"]),1);self.assertEqual(clock[0],45000);self.assertEqual(r["terminal"],"template_fallback")
    def test_successful_structure_is_pending_semantic_review(self):
        r=controlled_explanation({"result":"conflict"},[{"id":"E1"}],lambda **kw:dict(explanation="draft",citation_ids=["E1"]),now_ms=lambda:0)
        self.assertEqual(r["terminal"],"draft_pending_semantic_review");self.assertEqual(r["original"]["result"],"conflict")
    def test_output_cannot_write_rule_verdict(self):
        r=controlled_explanation({"result":"conflict"},[{"id":"E1"}],lambda **kw:dict(explanation="draft",citation_ids=["E1"],result="no_issue"),now_ms=lambda:0)
        self.assertEqual(r["terminal"],"template_fallback");self.assertEqual(r["original"]["result"],"conflict")


if __name__=="__main__":unittest.main()
