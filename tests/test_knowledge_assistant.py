import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app.knowledge_assistant.core import Assistant, Corpus, Principal, validate_answer
from app.knowledge_assistant.providers import Settings, ProviderError, embeddings, generate, unit_calculations
from app.knowledge_assistant.server import LocalServer


ENGINEER=Principal("test-engineer","engineer",("DEMO-TASK-001",))
EMPLOYEE=Principal("test-employee","employee")


class EmptySettings:
    def snapshot(self):
        return None


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus=Corpus()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.assistant=Assistant(self.corpus,EmptySettings(),Path(self.tmp.name)/"vectors.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_search_cites_real_metadata(self):
        result=self.assistant.ask("GB/T 35590-2017何时实施？",ENGINEER)
        self.assertEqual(result["sources"][0]["chunk_id"],"PUB-01-C1")
        self.assertIn("2018-07-01",result["sources"][0]["text"])
        self.assertEqual(result["trace"]["generation"],"not_requested")

    def test_archived_requires_explicit_scope(self):
        result=self.assistant.ask("RevA恢复电压要求",ENGINEER)
        self.assertEqual(result["status"],"needs_scope")
        self.assertFalse(any(s["document_id"].endswith("RevA") for s in result["sources"]))
        historical=self.assistant.ask("RevA恢复电压要求",ENGINEER,include_archived=True)
        self.assertTrue(any(s["document_id"].endswith("RevA") for s in historical["sources"]))
        self.assertFalse(any(s["document_id"].endswith("RevB") for s in historical["sources"]))
        self.assertFalse(any(s["document_id"]=="SYN-QA-SC-1.0" for s in historical["sources"]))

    def test_explicit_comparison_keeps_both_versions(self):
        result=self.assistant.ask("比较RevA和RevB恢复电压",ENGINEER,include_archived=True)
        docs={s["document_id"] for s in result["sources"]}
        self.assertIn("SYN-SPEC-PB01-RevA",docs)
        self.assertIn("SYN-SPEC-PB01-RevB",docs)

    def test_role_and_original_document_filter(self):
        result=self.assistant.ask("内部模拟规范响应阈值",EMPLOYEE,mode="answer")
        self.assertEqual(result["status"],"insufficient_evidence")
        self.assertFalse(any(s["material_type"]=="synthetic" for s in result["sources"]))
        with self.assertRaises(PermissionError):
            self.corpus.source("SYN-NORM-RESPONSE",EMPLOYEE)

    def test_task_scope_is_not_inherited(self):
        first=self.assistant.ask("R02响应是多少",ENGINEER,task_id="DEMO-TASK-001")
        self.assertTrue(any(s["scope"].startswith("task:") for s in first["sources"]))
        second=self.assistant.ask("R02响应是多少",ENGINEER)
        self.assertEqual(second["status"],"needs_scope")
        self.assertFalse(any(s["scope"].startswith("task:") for s in second["sources"]))
        with self.assertRaises(PermissionError):
            self.assistant.ask("报告",EMPLOYEE,task_id="DEMO-TASK-001")

    def test_missing_standard_clauses_never_trigger_generation(self):
        for query in ["GB/T 35590-2017准确限值", "国标短路阈值是多少", "GB 99999-2020是什么"]:
            value=self.assistant.ask(query,ENGINEER,mode="answer")
            self.assertEqual(value["status"],"insufficient_evidence")
            self.assertEqual(value["trace"]["generation"],"skipped_insufficient_scope_or_evidence")

    def test_standard_in_announcement_body_is_available_metadata(self):
        result=self.assistant.ask("2024年自动套用GB 47372-2026吗？",ENGINEER,mode="answer")
        self.assertEqual(result["status"],"model_not_configured")
        self.assertIn("PUB-05-C1",result["trace"]["retrieved_chunk_ids"])

    def test_missing_clauses_still_preserve_requested_metadata_date(self):
        result=self.assistant.ask("GB 4943.1-2022什么时候实施？本包能回答具体条款吗？",ENGINEER,mode="answer")
        self.assertEqual(result["status"],"partial")
        self.assertIn("2023-08-01",result["claims"][0]["text"])
        self.assertIn("未收录完整技术条款",result["limitations"][0])
        self.assertEqual(result["trace"]["generation"],"skipped_insufficient_scope_or_evidence")
        validate_answer({k:result[k] for k in ["status","claims","limitations"]},result["sources"])

    def test_unit_arithmetic_is_exact_and_does_not_repair_ambiguous_inputs(self):
        calculations=unit_calculations("0.68 s、0.125 s、3?.0 s、-0.8 s、1e3 s",[])
        self.assertEqual([c["formula"] for c in calculations],["0.68 s = 680 ms","0.125 s = 125 ms"])
        self.assertEqual(calculations[0]["input_sources"],["question"])

    def test_unit_arithmetic_is_supplied_to_generation_without_labels(self):
        captured={}
        def fake(config,path,payload):
            captured.update(json.loads(payload["messages"][1]["content"]))
            return {"choices":[{"finish_reason":"stop","message":{"content":json.dumps({"status":"insufficient_evidence","claims":[],"limitations":["测试返回"]})}}]}
        _,usage=generate(dict(provider="bailian",model="qwen-flash"),"0.68 s如何换算？",[self.corpus.by_id["SYN-NORM-RESPONSE"]],{},fake)
        self.assertEqual(captured["unit_calculations"][0]["formula"],"0.68 s = 680 ms")
        self.assertNotIn("expected_points",captured)
        self.assertEqual(usage["_unit_calculations"],captured["unit_calculations"])

    def test_report_recovery_fetches_current_basis_and_retains_conflicting_record(self):
        ranked=[(self.corpus.by_id[cid],10-i) for i,cid in enumerate([
            "TR-P2-RECOVERY","TR-P1-SUMMARY","SYN-NORM-RANGE","SYN-NORM-RECOVERY","TR-P2-RESPONSE","POL-DECISION"])]
        with patch("app.knowledge_assistant.core.rank_bm25",return_value=ranked):
            result=self.assistant.ask("报告把R04的5.31 V写通过，按任务RevB应如何处理？",ENGINEER,task_id="DEMO-TASK-001")
        ids=set(result["trace"]["retrieved_chunk_ids"])
        self.assertTrue({"TR-P2-RECOVERY","TR-P1-SUMMARY","SYN-SPEC-PB01-RevB-REC","SYN-NORM-CONFLICT"} <= ids)
        self.assertNotIn("SYN-SPEC-PB01-RevA-REC",ids)
        forbidden=self.assistant.ask("R04恢复电压",EMPLOYEE)
        self.assertFalse(any(s["material_type"]=="synthetic" for s in forbidden["sources"]))

    def test_report_observation_question_keeps_both_requirements(self):
        result=self.assistant.ask("C1的外观和恢复方式能判通过吗？",ENGINEER,task_id="DEMO-TASK-001")
        ids=set(result["trace"]["retrieved_chunk_ids"])
        self.assertTrue({"TR-P3-OBS","SYN-NORM-APPEARANCE","SYN-NORM-METHOD"} <= ids)

    def test_no_key_does_not_fake_a_model_answer(self):
        result=self.assistant.ask("RevB恢复电压范围",ENGINEER,mode="answer")
        self.assertEqual(result["status"],"model_not_configured")
        self.assertEqual(result["claims"],[])

    def test_unknown_query(self):
        self.assertEqual(self.assistant.ask("火星天气预报",ENGINEER)["status"],"insufficient_evidence")

    def test_unavailable_source_and_path_cannot_be_read(self):
        for value in ["../sources/source-register.json","QA-01","missing"]:
            with self.assertRaises(PermissionError):
                self.corpus.source(value,ENGINEER)

    def test_citations_reject_fabricated_ids_and_quotes(self):
        evidence=[self.corpus.by_id["PUB-01-C1"]]
        good=dict(status="answered",claims=[dict(text="该标准的实施日期为2018-07-01。",is_inference=False,
                  evidence=[dict(chunk_id="PUB-01-C1",quote="实施日期2018-07-01。")])],limitations=[])
        validate_answer(good,evidence)
        for key,value in [("chunk_id","SYN-NORM-RESPONSE"),("quote","这句话原文里根本没有")]:
            bad=copy.deepcopy(good);bad["claims"][0]["evidence"][0][key]=value
            with self.assertRaises(ProviderError):validate_answer(bad,evidence)

    def test_generation_pipeline_success_and_fail_closed(self):
        settings=Settings(Path(self.tmp.name)/"model.json")
        settings.save(dict(provider="bailian",base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",model="qwen-flash",embedding_model="text-embedding-v4",api_key="fixture-only-value"))
        def fake_ok(config,query,evidence,scope):
            c=evidence[0]
            return dict(status="answered",claims=[dict(text=c["text"],is_inference=False,evidence=[dict(chunk_id=c["chunk_id"],quote=c["text"][:100])])],limitations=[]),{}
        app=Assistant(self.corpus,settings,Path(self.tmp.name)/"v.json",generator=fake_ok)
        result=app.ask("RevB恢复电压",ENGINEER,mode="answer")
        self.assertEqual(result["trace"]["citation_check"],"ids_and_quotes_verified")
        def fake_bad(*args):
            raise ProviderError("模拟超时")
        app.generator=fake_bad
        failed=app.ask("RevB恢复电压",ENGINEER,mode="answer")
        self.assertEqual(failed["status"],"generation_failed")
        self.assertTrue(failed["sources"])

    def test_config_does_not_echo_secret_or_allow_wrong_hosts(self):
        settings=Settings(Path(self.tmp.name)/"model.json")
        value=dict(provider="bailian",base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",model="qwen-flash",embedding_model="text-embedding-v4",api_key="fixture-only-value")
        public=settings.save(value)
        self.assertNotIn("api_key",public)
        self.assertEqual(settings.path.stat().st_mode&0o777,0o600)
        with self.assertRaises(ValueError):settings.save({**value,"base_url":"https://example.com/v1"})
        with self.assertRaises(ValueError):settings.save({**value,"base_url":"http://dashscope.aliyuncs.com/v1"})

    def test_embedding_batch_order_and_dimensions(self):
        config=dict(provider="bailian",embedding_model="text-embedding-v4")
        calls=[]
        def fake(cfg,path,payload):
            calls.append(payload)
            return {"data":[{"index":i,"embedding":[i+1.0]*16} for i in reversed(range(len(payload["input"])))]}
        values=embeddings(config,[str(i) for i in range(21)],fake)
        self.assertEqual([len(c["input"]) for c in calls],[10,10,1])
        self.assertEqual(len(values),21)
        with self.assertRaises(ProviderError):embeddings(config,["x"],lambda *args:{"data":[{"index":2,"embedding":[1.0]*16}]})

    def test_hybrid_retrieval_filters_before_ranking_and_invalidates_old_index(self):
        settings=Settings(Path(self.tmp.name)/"model.json")
        cfg=dict(provider="bailian",base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",model="qwen-flash",embedding_model="text-embedding-v4",api_key="fixture-only-value")
        settings.save(cfg)
        app=Assistant(self.corpus,settings,Path(self.tmp.name)/"v.json",embedder=lambda config,texts:[[.25]*16 for _ in texts])
        app.build_vectors()
        self.assertTrue(app.vector_ready())
        result=app.ask("响应",EMPLOYEE)
        self.assertEqual(result["trace"]["retrieval_method"],"bm25+embedding-rrf")
        self.assertFalse(any(s["material_type"]=="synthetic" for s in result["sources"]))
        settings.save({**cfg,"embedding_model":"text-embedding-v3"})
        self.assertFalse(app.vector_ready())

    def test_vector_failure_is_visible_after_successful_generation(self):
        settings=Settings(Path(self.tmp.name)/"model.json")
        settings.save(dict(provider="bailian",base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",model="qwen-flash",embedding_model="text-embedding-v4",api_key="fixture-only-value"))
        def fake_generation(config,query,evidence,scope):
            c=evidence[0]
            return dict(status="answered",claims=[dict(text=c["text"],is_inference=False,evidence=[dict(chunk_id=c["chunk_id"],quote=c["text"][:100])])],limitations=[]),{}
        app=Assistant(self.corpus,settings,Path(self.tmp.name)/"v.json",generator=fake_generation)
        app.vectors=dict(embedding_config=app.fingerprint(settings.snapshot()),vectors={})
        def fail(*args):raise ProviderError("模拟向量故障")
        app.embedder=fail
        result=app.ask("RevB恢复电压",ENGINEER,mode="answer")
        self.assertEqual(result["status"],"answered")
        self.assertTrue(any("向量查询失败" in s for s in result["limitations"]))

    def test_provider_json_mode_and_incomplete_answer(self):
        cfg=dict(provider="bailian",model="qwen-flash")
        def fake(config,path,payload):
            self.assertEqual(path,"/chat/completions")
            self.assertEqual(payload["response_format"],{"type":"json_object"})
            self.assertFalse(payload["enable_thinking"])
            self.assertEqual(len(payload["messages"]),2)
            self.assertNotIn("tools",payload)
            return {"choices":[{"finish_reason":"length","message":{"content":"{}"}}]}
        with self.assertRaises(ProviderError):generate(cfg,"问题",[],{},fake)

    def test_generation_hashes_track_actual_context_without_credentials(self):
        cfg=dict(provider="bailian",model="qwen-flash",api_key="fixture-only-value")
        def fake(config,path,payload):
            self.assertNotIn("fixture-only-value",json.dumps(payload))
            return {"choices":[{"finish_reason":"stop","message":{"content":json.dumps({"status":"insufficient_evidence","claims":[],"limitations":["缺资料"]})}}]}
        _,first=generate(cfg,"问题甲",[],{},fake)
        _,second=generate(cfg,"问题乙",[],{},fake)
        self.assertEqual(first["_prompt_sha256"],second["_prompt_sha256"])
        self.assertNotEqual(first["_canonical_payload_sha256"],second["_canonical_payload_sha256"])
        self.assertEqual(len(first["_prompt_sha256"]),64)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.server=LocalServer(("127.0.0.1",0),EMPLOYEE,cls.tmp.name)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.port=cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.server.store.db.close();cls.tmp.cleanup()

    def call(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection("127.0.0.1",self.port)
        connection.request(method,path,json.dumps(body) if body is not None else None,headers or {})
        response=connection.getresponse();data=response.read();result=(response.status,data,dict(response.getheaders()));connection.close();return result

    def auth(self):
        status,raw,headers=self.call("GET","/api/config")
        self.assertEqual(status,200)
        return {"Cookie":headers["Set-Cookie"].split(";")[0],"X-Local-Token":json.loads(raw)["csrf_token"],"Content-Type":"application/json"}

    def test_session_origin_role_override_and_source_permissions(self):
        self.assertEqual(self.call("POST","/api/query",{"query":"x"})[0],403)
        headers=self.auth()
        self.assertEqual(self.call("POST","/api/query",{"query":"x","role":"engineer"},headers)[0],400)
        self.assertEqual(self.call("POST","/api/query",{"query":"x"},{**headers,"Origin":"https://example.com"})[0],403)
        self.assertEqual(self.call("GET","/api/source/SYN-NORM-RESPONSE",headers=headers)[0],403)
        self.assertEqual(self.call("GET","/api/pdf/SYN-TR-001-R1",headers=headers)[0],403)
        self.assertEqual(self.call("GET","/../../README.md",headers=headers)[0],404)

    def test_request_logging_feedback_and_replay(self):
        headers=self.auth()
        status,raw,_=self.call("POST","/api/query",{"query":"GB/T 35590-2017什么时候实施","mode":"search"},headers)
        self.assertEqual(status,200);result=json.loads(raw)
        status,raw,_=self.call("GET","/api/requests/"+result["request_id"],headers=headers)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(raw)["request_id"],result["request_id"])
        status,_,_=self.call("POST","/api/feedback",dict(request_id=result["request_id"],kind="useful",note=""),headers)
        self.assertEqual(status,200)


if __name__=="__main__":
    unittest.main()
