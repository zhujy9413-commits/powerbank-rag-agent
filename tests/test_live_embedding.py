import json
import unittest
from unittest.mock import patch

from app.ai_work.live_embedding import EmbeddingStopped, MeteredEmbedding, MODEL


CONFIG = dict(provider="bailian", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
              model="unused-chat-model", embedding_model=MODEL, api_key="synthetic-test-key")


def response(payload, **changes):
    value = dict(model=MODEL, id="test-request", usage=dict(total_tokens=len(payload["input"])*7),
                 data=[dict(index=i, embedding=[1.0]+[0.0]*1023) for i in range(len(payload["input"]))])
    value.update(changes)
    return value


class LiveEmbeddingTests(unittest.TestCase):
    def test_batches_order_and_exact_usage_ledger(self):
        calls=[]
        def transport(c,path,payload):
            self.assertEqual(path,"/embeddings");self.assertEqual(payload["dimensions"],1024)
            calls.append(payload)
            r=response(payload);r["data"].reverse();return r
        e=MeteredEmbedding(CONFIG,transport=transport)
        e.context=dict(report_id="test",arm="A2")
        vectors=e.embed(["测试"]*11)
        self.assertEqual([len(c["input"]) for c in calls],[10,1])
        self.assertEqual(len(vectors["vectors"]),11)
        ledger=e.ledger()
        self.assertEqual(ledger["known_total_tokens"],77)
        self.assertEqual(ledger["known_list_price_cny"],"0.0000385")
        self.assertEqual(ledger["unknown_usage_requests"],0)
        self.assertTrue(all(r["status"]=="validated" for r in ledger["records"]))
        public=json.dumps(ledger)
        self.assertNotIn(CONFIG["api_key"],public);self.assertNotIn(CONFIG["base_url"],public)
        self.assertNotIn("测试",public)

    def test_request_budget_stops_before_second_http_request(self):
        calls=[]
        e=MeteredEmbedding(CONFIG,max_requests=1,transport=lambda c,p,x:(calls.append(x) or response(x)))
        with self.assertRaises(EmbeddingStopped):e.embed(["a"]*11)
        self.assertEqual(len(calls),1);self.assertEqual(e.stopped,"request_budget")
        self.assertEqual(e.ledger()["known_total_tokens"],70)

    def test_cost_reservation_stops_before_spend(self):
        e=MeteredEmbedding(CONFIG,max_cny="0.001",transport=lambda *a:self.fail("must not call"))
        with self.assertRaises(EmbeddingStopped):e.embed(["a"])
        self.assertEqual(e.stopped,"cost_budget");self.assertFalse(e.records)

    def test_deadline_stops_before_network(self):
        now=[0]
        e=MeteredEmbedding(CONFIG,clock=lambda:now[0],deadline_seconds=10)
        now[0]=10
        with self.assertRaises(EmbeddingStopped):e.embed(["a"])
        self.assertEqual(e.stopped,"campaign_deadline");self.assertFalse(e.records)

    def test_missing_usage_is_unknown_not_free_and_stops(self):
        e=MeteredEmbedding(CONFIG,transport=lambda c,p,x:response(x,usage={}))
        with self.assertRaises(EmbeddingStopped):e.embed(["a"])
        self.assertEqual(e.ledger()["unknown_usage_requests"],1)
        self.assertEqual(e.ledger()["unmetered_reserved_cny"],"0.004096")
        with self.assertRaises(EmbeddingStopped):e.embed(["b"])
        self.assertEqual(len(e.records),1)

    def test_invalid_usage_types_fail_closed(self):
        for usage in [True,-1,1.5,"7",None]:
            with self.subTest(usage=usage):
                e=MeteredEmbedding(CONFIG,transport=lambda c,p,x:response(x,usage=dict(total_tokens=usage)))
                with self.assertRaises(EmbeddingStopped):e.embed(["a"])
                self.assertIsNone(e.records[0]["total_tokens"])

    def test_model_drift_retains_payable_usage(self):
        for model in [None,"different-model"]:
            e=MeteredEmbedding(CONFIG,transport=lambda c,p,x:response(x,model=model))
            with self.assertRaises(EmbeddingStopped):e.embed(["a"])
            self.assertEqual(e.stopped,"returned_model_mismatch_or_missing")
            self.assertEqual(e.ledger()["known_total_tokens"],7)

    def test_wrong_dimension_and_nonfinite_vector_are_rejected(self):
        for vector in [[1.0]*512,[float("nan")]*1024,[0.0]*1024]:
            def transport(c,p,x):
                r=response(x);r["data"][0]["embedding"]=vector;return r
            e=MeteredEmbedding(CONFIG,transport=transport)
            with self.assertRaises(EmbeddingStopped):e.embed(["a"])
            self.assertEqual(e.records[0]["status"],"failed")
            self.assertEqual(e.ledger()["known_total_tokens"],7)

    def test_missing_duplicate_or_boolean_indexes_rejected(self):
        for indexes in [[0],[0,0],[False,1]]:
            def transport(c,p,x):
                r=response(x);r["data"]=[dict(index=i,embedding=[1.0]*1024) for i in indexes];return r
            e=MeteredEmbedding(CONFIG,transport=transport)
            with self.assertRaises(EmbeddingStopped):e.embed(["a","b"])
            self.assertEqual(e.ledger()["known_total_tokens"],14)

    def test_provider_failure_is_single_attempt_sanitized_and_checkpointed(self):
        checkpoints=[];calls=[]
        def transport(*args):
            calls.append(1);raise TimeoutError("sensitive key and address")
        e=MeteredEmbedding(CONFIG,transport=transport,checkpoint=lambda x:checkpoints.append(json.loads(json.dumps(x))))
        with self.assertRaisesRegex(EmbeddingStopped,"^provider_failure$"):e.embed(["a"])
        self.assertEqual(len(calls),1)
        self.assertEqual(checkpoints[0]["records"][0]["status"],"attempted")
        self.assertEqual(checkpoints[-1]["records"][0]["status"],"failed")
        self.assertNotIn("sensitive",json.dumps(checkpoints))

    def test_usage_above_documented_max_stops_and_retains_usage(self):
        e=MeteredEmbedding(CONFIG,transport=lambda c,p,x:response(x,usage=dict(total_tokens=8193)))
        with self.assertRaises(EmbeddingStopped):e.embed(["a"])
        self.assertEqual(e.stopped,"usage_exceeds_documented_limit")
        self.assertEqual(e.records[0]["total_tokens"],8193)

    def test_unverified_region_provider_model_and_input_are_blocked(self):
        for changes in [dict(base_url="https://example.ap-southeast-1.maas.aliyuncs.com/v1"),dict(embedding_model="text-embedding-v3")]:
            with self.assertRaises(ValueError):MeteredEmbedding({**CONFIG,**changes})
        for texts in [[],[""],["a"*8193],"text"]:
            e=MeteredEmbedding(CONFIG)
            with self.assertRaises(EmbeddingStopped):e.embed(texts)
            self.assertFalse(e.records)

    def test_candidate_cannot_masquerade_provider_failure_as_live_success(self):
        from app.ai_work.candidate import CandidateRetriever
        from app.ai_work.candidate_inputs import load_input
        from app.knowledge_assistant.core import Principal
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        task,chunks,originals=load_input(root/"data/ai-work-rag-gain-dev-v0.1/application-inputs/SYND-801",root)
        task["selected_versions"]={c["chunk_id"]:c["version"] for c in chunks if c["namespace"]=="requirement"}
        e=MeteredEmbedding(CONFIG,transport=lambda *a:(_ for _ in ()).throw(TimeoutError()))
        r=CandidateRetriever(chunks,task,Principal("test","engineer",(task["task_id"],)),originals,embedder=e)
        output=r.retrieve(task["queries"][0],"report",method="hybrid")
        self.assertEqual(output["degradation"],"embedding_failure_or_identity_drift")
        self.assertEqual(output["effective_method"],"bm25")
        self.assertEqual(e.stopped,"provider_failure")


if __name__=="__main__":unittest.main()
