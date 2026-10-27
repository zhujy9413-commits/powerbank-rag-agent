import copy
import json
from pathlib import Path
import tempfile
import unittest

from app.knowledge_assistant.contracts import reference_catalog, resolve_references, scope_answer, validate_answer, response_record_answer
from app.knowledge_assistant.core import Assistant, Corpus, Principal
from app.knowledge_assistant.providers import ProviderError, generate


class NoModel:
    def snapshot(self):
        return None


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = Corpus()
        cls.scope = cls.corpus.by_id["SYN-SPEC-PB01-RevB-SCOPE"]
        cls.response = cls.corpus.by_id["SYN-NORM-RESPONSE"]

    def candidate(self, ref="REF001", text="题设0.68 s换算为680 ms。"):
        return dict(status="answered", claims=[dict(text=text, is_inference=True, reference_ids=[ref])], limitations=[])

    def wire(self, value):
        return dict(choices=[dict(finish_reason="stop", message=dict(content=json.dumps(value, ensure_ascii=False)))],
                    usage=dict(prompt_tokens=10, completion_tokens=5, total_tokens=15))

    def test_scope_paraphrases_use_source_facts_without_generation(self):
        principal = Principal("regression", "engineer")
        with tempfile.TemporaryDirectory() as tmp:
            def forbidden(*args):
                raise AssertionError("范围说明不应交给模型改写角色")
            app = Assistant(self.corpus, NoModel(), Path(tmp)/"index", generator=forbidden)
            for query in ["这一演示范围是否覆盖C1充电输入和所有快充档？", "本次配置包含C1的输入测试吗？", "这次测过C1输入还是只覆盖输出？"]:
                with self.subTest(query=query):
                    result = app.ask(query, principal, mode="answer")
                    self.assertEqual(result["trace"]["generation"], "not_requested_scope_template")
                    self.assertEqual(result["trace"]["scope_facts"]["role"], "output")
                    self.assertEqual(result["trace"]["scope_facts"]["voltage_v"], "5")
                    self.assertIn("5 V输出角色", result["claims"][0]["text"])
                    self.assertIn("不能据此认定输入角色", result["claims"][1]["text"])
                    validate_answer({k:result[k] for k in ["status", "claims", "limitations"]}, result["sources"])

    def test_scope_values_are_extracted_and_unknown_or_mixed_scope_is_not_assumed(self):
        changed = copy.deepcopy(self.scope)
        changed["text"] = changed["text"].replace("本任务仅A1、C1的5 V输出角色。", "本任务仅B2、D3的9 V输入角色。")
        answer, facts = scope_answer("本次配置覆盖输入还是输出？", [changed])
        self.assertEqual(facts["ports"], ["B2", "D3"])
        self.assertEqual(facts["role"], "input")
        self.assertIn("9 V输入角色", answer["claims"][0]["text"])
        changed["text"] = changed["text"].replace("其他角色、电压、组合和保护项目未配置。", "其他范围待补充。")
        self.assertIsNone(scope_answer("本次覆盖C1输入吗？", [changed]))
        self.assertIsNone(scope_answer("比较范围是否覆盖输入？", [self.scope, self.corpus.by_id["SYN-SPEC-PB01-RevA-SCOPE"]]))
        self.assertIsNone(scope_answer("C1支持双向供电吗？", [self.scope]))

    def test_real_quote_does_not_allow_the_observed_compound_role_error(self):
        value = dict(status="answered", claims=[dict(text="演示范围仅覆盖C1充电输入的5 V输出角色。", is_inference=False,
            evidence=[dict(chunk_id=self.scope["chunk_id"], quote=self.scope["text"])])], limitations=[])
        with self.assertRaisesRegex(ProviderError, "混淆"):
            validate_answer(value, [self.scope])
        value["claims"][0]["text"] = "C1是双向口，本次只配置5 V输出，未配置输入。"
        validate_answer(value, [self.scope])

    def test_scope_routing_does_not_replace_parameter_or_hardware_questions(self):
        for query in ["演示C1输出的恢复电压范围是多少？", "本次C1输出的响应时间是多少？", "C1双向口支持输入和输出吗？"]:
            with self.subTest(query=query):
                self.assertIsNone(scope_answer(query,[self.scope]))

    def test_malformed_status_is_rejected_as_a_contract_failure(self):
        candidate=self.candidate();candidate["status"]=["answered"]
        with self.assertRaises(ProviderError):
            resolve_references(candidate,reference_catalog([self.response]),[self.response])

    def test_record_claim_and_summary_value_require_their_own_sources(self):
        evidence=[self.corpus.by_id[cid] for cid in ["TR-P2-RECOVERY","SYN-SPEC-PB01-RevB-REC","SYN-NORM-CONFLICT","TR-P1-SUMMARY"]]
        def claim(text,cid):
            c=self.corpus.by_id[cid]
            return dict(text=text,is_inference=False,evidence=[dict(chunk_id=cid,quote=c["text"])])
        value=dict(status="answered",claims=[claim("R04的5.31 V超出模拟上限。","SYN-SPEC-PB01-RevB-REC")],limitations=[])
        with self.assertRaisesRegex(ProviderError,"记录R04"):
            validate_answer(value,evidence)
        c=evidence[0];value["claims"][0]["evidence"].append(dict(chunk_id=c["chunk_id"],quote=c["text"]))
        validate_answer(value,evidence)
        value["claims"]=[claim("摘要中80 ms与原始记录0.68 s存在冲突。","SYN-NORM-CONFLICT")]
        with self.assertRaisesRegex(ProviderError,"摘要原文"):
            validate_answer(value,evidence)
        c=evidence[-1];value["claims"][0]["evidence"].append(dict(chunk_id=c["chunk_id"],quote=c["text"]))
        validate_answer(value,evidence)

    def test_summary_matches_port_and_field_instead_of_equal_numeric_value(self):
        evidence=[self.corpus.by_id[cid] for cid in ["TR-P2-RESPONSE","TR-P1-SUMMARY","SYN-NORM-RESPONSE","SYN-NORM-CONFLICT"]]
        answer,facts=response_record_answer("R02的0.68 s响应按规范怎么看，摘要却写80 ms？",evidence)
        self.assertEqual(answer["status"],"conflict")
        self.assertEqual(facts["port"],"C1")
        self.assertEqual(facts["summary"]["port"],"C1")
        self.assertEqual(facts["summary"]["record_id"],"S01")
        self.assertEqual(facts["normalized_ms"],"680")
        self.assertIn("680 ms > 500 ms",answer["claims"][2]["text"])
        self.assertIn("同端口",answer["claims"][1]["text"])
        validate_answer(answer,evidence)
        changed=copy.deepcopy(evidence)
        changed[0]["text"]="R01 A1保护响应80 ms；R10 D3保护响应0.12 s。"
        changed[1]["text"]="S09：D3保护响应120 ms，摘要填写通过。"
        answer,facts=response_record_answer("R10响应和摘要一致吗？",changed)
        self.assertEqual(facts["port"],"D3")
        self.assertEqual(facts["normalized_ms"],"120")
        self.assertFalse(facts["conflict"])
        self.assertEqual(answer["status"],"answered")

    def test_response_template_does_not_guess_missing_sources_or_other_fields(self):
        evidence=[self.corpus.by_id[cid] for cid in ["TR-P2-RESPONSE","SYN-NORM-RESPONSE"]]
        self.assertIsNone(response_record_answer("R02响应与摘要一致吗？",evidence))
        self.assertIsNone(response_record_answer("R02的负责人是谁？",evidence))
        self.assertIsNone(response_record_answer("R04恢复电压是多少？",evidence))

    def test_unique_report_anchor_is_completed_with_audit_without_mapping_fake_ids(self):
        evidence=[self.corpus.by_id[cid] for cid in ["SYN-SPEC-PB01-RevB-REC","TR-P2-RECOVERY"]]
        catalog=reference_catalog(evidence);changes=[]
        candidate=self.candidate("REF001","R04的5.31 V超出模拟RevB上限5.25 V。")
        answer=resolve_references(candidate,catalog,evidence,completions=changes)
        self.assertEqual([r["chunk_id"] for r in answer["claims"][0]["evidence"]],[evidence[0]["chunk_id"],evidence[1]["chunk_id"]])
        self.assertEqual(changes,[dict(claim_index=0,reference_id="REF002",chunk_id="TR-P2-RECOVERY",reason="record:R04")])
        self.assertEqual(candidate["claims"][0]["reference_ids"],["REF001"])
        with self.assertRaises(ProviderError):
            resolve_references(self.candidate("unit_calculations","R04的5.31 V超限。"),catalog,evidence)
        with self.assertRaises(ProviderError):
            resolve_references(self.candidate("REF001","R99的5.31 V超限。"),catalog,evidence)

    def test_catalog_only_resolves_current_sources_and_supplies_original_quotes(self):
        catalog = reference_catalog([self.response])
        resolved = resolve_references(self.candidate(), catalog, [self.response])
        self.assertEqual(resolved["claims"][0]["evidence"], [dict(chunk_id=self.response["chunk_id"], quote=self.response["text"])])
        for invalid in ["unit_calculations", "question", "SYN-NORM-RESPONSE", "REF999", {"id":"REF001"}]:
            with self.subTest(invalid=invalid), self.assertRaises(ProviderError):
                resolve_references(self.candidate(invalid), catalog, [self.response])
        # An already-mapped citation from another request cannot pass this one.
        with self.assertRaises(ProviderError):
            validate_answer(resolved, [self.corpus.by_id["PUB-01-C1"]])

    def test_contract_correction_keeps_failed_candidate_and_accounts_both_calls(self):
        calls = []
        def fake(config, path, payload):
            calls.append(copy.deepcopy(payload))
            return self.wire(self.candidate("unit_calculations" if len(calls) == 1 else "REF001"))
        answer, usage = generate(dict(provider="bailian", model="qwen-flash"), "0.68 s如何换算？", [self.response], {}, fake)
        self.assertEqual(len(calls), 2)
        self.assertEqual(usage["total_tokens"], 30)
        self.assertEqual([a["accepted"] for a in usage["_provider_attempts"]], [False, True])
        self.assertEqual(usage["_provider_attempts"][0]["raw_candidate_unvalidated"]["claims"][0]["reference_ids"], ["unit_calculations"])
        self.assertIn("validation_feedback", json.loads(calls[1]["messages"][1]["content"]))
        self.assertEqual(answer["claims"][0]["evidence"][0]["chunk_id"], self.response["chunk_id"])

    def test_two_invalid_candidates_stop_without_dropping_bad_references(self):
        calls = []
        def fake(*args):
            calls.append(1)
            return self.wire(self.candidate("REF999"))
        with self.assertRaises(ProviderError) as raised:
            generate(dict(provider="bailian", model="qwen-flash"), "换算", [self.response], {}, fake)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(raised.exception.audit["attempts"]), 2)
        self.assertTrue(all(not a["accepted"] for a in raised.exception.audit["attempts"]))

    def test_transport_failure_is_not_retried(self):
        calls = []
        def fail(*args):
            calls.append(1)
            raise ProviderError("模型或地域权限不足。")
        with self.assertRaises(ProviderError) as raised:
            generate(dict(provider="bailian", model="qwen-flash"), "换算", [self.response], {}, fail)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(raised.exception.audit["attempts"]), 1)

    def test_failed_provider_attempts_survive_application_response(self):
        class Configured:
            def snapshot(self):
                return dict(provider="bailian", model="qwen-flash")
        with tempfile.TemporaryDirectory() as tmp:
            def invalid(config, question, evidence, scope):
                return generate(config, question, evidence, scope, lambda *args:self.wire(self.candidate("REF999")))
            app = Assistant(self.corpus, Configured(), Path(tmp)/"index", generator=invalid)
            result = app.ask("0.68 s按模拟响应规范换算", Principal("regression", "engineer"), mode="answer")
            self.assertEqual(result["status"], "generation_failed")
            self.assertEqual(result["claims"], [])
            self.assertEqual(len(result["trace"]["provider_attempts"]), 2)
            self.assertEqual(result["usage"]["total_tokens"], 30)
            self.assertTrue(result["sources"])


if __name__ == "__main__":
    unittest.main()
