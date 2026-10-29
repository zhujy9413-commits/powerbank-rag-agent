"""Behavioral counterexamples use fresh IDs and versions, not development qrels."""
from copy import deepcopy
import unittest

from app.ai_work.candidate import CandidateRetriever,FIELDS,query_plan,seed
from app.knowledge_assistant.core import Principal


class ConsistencyQueryTests(unittest.TestCase):
    def setUp(self):
        self.task=dict(task_id="CURRENT",task_authorized=True,ports=["A1","C1"],
                       selected_requirement_chunks=["scope-x","clause-z","rule-view","rule-reset","rule-conflict"],
                       selected_versions={"scope-x":"1","clause-z":"D","rule-view":"1","rule-reset":"1","rule-conflict":"1"})
        def c(i,text,ns="requirement",role="selected_requirement",section="CLAUSE",version="1",**kw):
            return dict(chunk_id=i,text=text,namespace=ns,source_role=role,source_path="sources/"+i+".md",page=None,
                section=section,version=version,publication_status="active",material_type="synthetic",allowed_roles=["engineer"],
                task_id="CURRENT",conditions=deepcopy(self.conditions),context_ids=[],**kw)
        self.conditions=dict(voltage_v=5,electrical_role="输出",combination="单口")
        self.c=c
        self.chunks=[c("scope-x","任务清单显式选定的规格为准，不按文件名猜最新版。"),
                     c("clause-z","模拟条款：电流限制应按约定值核对。",section="SPEC-C 电流限制",version="D"),
                     c("rule-view","每端口应明确记录无起火、无爆炸、无漏液。"),
                     c("rule-reset","每端口需有恢复方式文字记录。"),
                     c("rule-conflict","摘要与原始记录矛盾时保留双方。")]
        texts=dict(response="保护响应 260 ms",recovery="恢复电压 5 V",temperature="壳温起值/末值 20 / 30",appearance="外观观察 无起火、无爆炸、无漏液",method="恢复方式 记录为重新连接")
        for port in ["A1","C1"]:
            for field in FIELDS:
                self.chunks.append(c(port+"-"+field,port+" "+texts[field],"report","report_observation"))
        self.principal=Principal("engineer","engineer",("CURRENT",))

    def make(self):
        originals={(c["source_path"],c["page"]):c["text"] for c in self.chunks}
        return CandidateRetriever(self.chunks,self.task,self.principal,originals)
    def query(self,text):return dict(text=text,port=None,field="consistency",conditions=deepcopy(self.conditions))

    def test_version_targets_selected_specification_clause_and_scope(self):
        r=self.make().retrieve(self.query("报告填写的规格版本与本次选定RevD是否一致"),"requirement")
        self.assertEqual({x["chunk_id"] for x in r["raw_seeds"]},{"scope-x","clause-z"})
        self.assertEqual(r["trace"]["query_plan"]["intent"],"version_consistency")
        self.assertIn("SPEC-C 电流限制",r["trace"]["retrieval_text"])
    def test_report_revision_does_not_select_requirement_revision(self):
        self.chunks.append(self.c("declaration-a","报告填写的规格版本为RevA","report","report_declaration",version="A"))
        r=self.make().retrieve(self.query("报告RevA与任务选定的规格版本核对"),"requirement")
        self.assertEqual({x["chunk_id"] for x in r["accepted"]},{"scope-x","clause-z"})
        self.assertEqual(next(x for x in r["accepted"] if x["chunk_id"]=="clause-z")["version"],"D")
    def test_unselected_newer_clause_cannot_enter_version_query(self):
        self.chunks.append(self.c("newer-but-unselected","规格版本 最新RevZ 规格电流限制",section="SPEC-Z 电流限制",version="Z"))
        self.assertNotIn("newer-but-unselected",[x["chunk_id"] for x in self.make().retrieve(self.query("规格版本与选定版本核对"),"requirement")["raw_seeds"]])
    def test_background_missing_fields_are_derived_from_observation_inventory(self):
        self.chunks=[x for x in self.chunks if x["chunk_id"] not in {"A1-method","C1-appearance"}]
        r=self.make().retrieve(self.query("背景摘要称记录齐全，核对原始记录完整性"),"requirement")
        self.assertEqual(r["trace"]["query_plan"]["focus_fields"],["appearance","method"])
        self.assertEqual({x["chunk_id"] for x in r["raw_seeds"]},{"rule-view","rule-reset"})
        self.assertFalse(r["trace"]["query_plan"]["claims_physical_test_missing"])
    def test_complete_inventory_does_not_invent_missing_fields(self):
        r=self.make().retrieve(self.query("背景摘要的原始记录完整性核对"),"requirement")
        self.assertEqual(r["trace"]["query_plan"]["focus_fields"],[])
        self.assertEqual(r["raw_seeds"],[])
        self.assertTrue(all(x["state"]=="candidate_present" for x in r["trace"]["query_plan"]["inventory"]))
    def test_unknown_conditions_cannot_fill_missing_current_observation(self):
        next(c for c in self.chunks if c["chunk_id"]=="C1-appearance")["conditions"]=None
        r=self.make().retrieve(self.query("背景记录齐全的完整性核对"),"requirement")
        self.assertEqual(r["trace"]["query_plan"]["focus_fields"],["appearance"])
    def test_other_voltage_cannot_fill_current_observation(self):
        next(c for c in self.chunks if c["chunk_id"]=="C1-appearance")["conditions"]["voltage_v"]=9
        r=self.make().retrieve(self.query("背景记录完整性核对"),"requirement")
        self.assertEqual(r["trace"]["query_plan"]["focus_fields"],["appearance"])
    def test_unauthorized_or_foreign_observation_is_not_counted(self):
        next(c for c in self.chunks if c["chunk_id"]=="C1-appearance")["task_id"]="OTHER"
        next(c for c in self.chunks if c["chunk_id"]=="A1-method")["allowed_roles"]=["admin"]
        plan=self.make().retrieve(self.query("背景记录完整性核对"),"requirement")["trace"]["query_plan"]
        self.assertEqual(plan["focus_fields"],["appearance","method"])
        self.assertNotIn("C1-appearance",str(plan));self.assertNotIn("A1-method",str(plan))
    def test_duplicate_observation_is_unresolved_not_complete(self):
        c=deepcopy(next(c for c in self.chunks if c["chunk_id"]=="A1-method"));c["chunk_id"]="duplicate-method";self.chunks.append(c)
        r=self.make().retrieve(self.query("背景记录完整性核对"),"requirement")
        self.assertIn("method",r["trace"]["query_plan"]["focus_fields"])
        self.assertEqual(next(x["state"] for x in r["trace"]["query_plan"]["inventory"] if x["port"]=="A1" and x["field"]=="method"),"ambiguous_candidates")
    def test_missing_port_scope_is_explicitly_unresolved(self):
        del self.task["ports"]
        plan=self.make().retrieve(self.query("背景记录完整性核对"),"requirement")["trace"]["query_plan"]
        self.assertEqual(plan["resolution"],"required_ports_unavailable");self.assertEqual(plan["focus_fields"],[])


if __name__=="__main__":unittest.main()
