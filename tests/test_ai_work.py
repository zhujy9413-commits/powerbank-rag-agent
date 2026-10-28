import base64
from copy import deepcopy
import http.client
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from app.ai_work.review import ReviewService, ConflictError, parse_pdf, evaluate, digest
from app.ai_work.export import export_xlsx, workbook_rows
from app.knowledge_assistant.core import Corpus, Principal, ROOT
from app.knowledge_assistant.server import LocalServer

ENGINEER = Principal("review-engineer", "engineer", ("DEMO-TASK-001",))
OTHER = Principal("other-engineer", "engineer", ("DEMO-TASK-001",))
EMPLOYEE = Principal("employee", "employee")


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = ReviewService(Path(self.tmp.name)/"review.db", Corpus())
        self.task = self.service.create(ENGINEER, {"sample": True})
        self.tid = self.task["task_id"]

    def tearDown(self):
        self.service.db.close()
        self.tmp.cleanup()

    def confirm(self, corrections=None, revision=1):
        self.task = self.service.confirm(ENGINEER, self.tid, dict(revision=revision, acknowledged=True, corrections=corrections or {}))
        return self.task["snapshots"][-1]

    def execute(self, key="test-run-0001", revision=2):
        return self.service.run(ENGINEER, self.tid, dict(revision=revision, idempotency_key=key))

    def test_real_pdf_extraction_identity_and_all_fields(self):
        r = self.task["snapshots"][0]["report"]
        self.assertEqual(r["page_count"], 4)
        self.assertEqual(r["sha256"], digest((ROOT/"output/pdf/SYN-TR-001-R1.pdf").read_bytes()))
        self.assertEqual(r["fields"]["C1:response"][0]["value"], "0.68 s")
        self.assertEqual(r["fields"]["C1:appearance"], [])
        self.assertEqual(r["report_basis"], "RevA")
        for rows in r["fields"].values():
            for record in rows:
                self.assertIn(record["quote"], r["pages"][record["page"]-1]["text"])

    def test_baseline_ten_units_two_conflicts_and_pending(self):
        self.confirm(); r = self.execute()
        self.assertEqual(r["counts"], dict(no_issue=5, nonconformity=2, evidence_insufficient=3, conflict=2))
        self.assertEqual(r["configured_units"], 10)
        self.assertEqual(len(r["items"]), 12)
        self.assertEqual(r["pending_reviews"], 12)
        c1 = next(i for i in r["items"] if i["item_id"] == "C1-01")
        self.assertTrue(c1["conditional"])
        self.assertIn("680", c1["calculation"])
        self.assertEqual(r["state"], "awaiting_review")

    def test_injection_and_unconfigured_never_become_pass(self):
        self.confirm(); r = self.execute()
        self.assertIn("F01", json.dumps(r, ensure_ascii=False))
        self.assertEqual(r["counts"]["nonconformity"], 2)
        self.assertEqual(len(r["unconfigured"]), 4)
        self.assertFalse(any("F01" in ref["quote"] for i in r["items"] for ref in i["report_evidence"]))

    def test_gate_and_stale_input(self):
        with self.assertRaises(ConflictError): self.execute(revision=1)
        self.confirm()
        with self.assertRaises(ConflictError): self.confirm(revision=1)
        with self.assertRaises(ConflictError): self.execute(revision=1)

    def test_corrections_need_reason_and_unique_original(self):
        for corrections in [{"C1:temperature": {"value":"25.0摄氏度 / 34.0摄氏度", "reason":""}},
                            {"C1:method": {"value":"记录为x", "reason":"x"}}]:
            with self.subTest(corrections=corrections), self.assertRaises(ValueError): self.confirm(corrections)

    def test_new_revision_keeps_old_result_and_correction_provenance(self):
        self.confirm(); first = self.execute()
        self.confirm({"C1:temperature": {"value":"25.0摄氏度 / 34.0摄氏度", "reason":"测试用人工解析修正，非真实报告核实"}}, revision=2)
        second = self.execute("test-run-0002", 3)
        self.assertTrue(self.service.result(ENGINEER, first["run_id"])["historical"])
        self.assertEqual(first["counts"]["evidence_insufficient"], 3)
        self.assertEqual(second["counts"]["evidence_insufficient"], 2)
        item = next(i for i in second["items"] if i["item_id"] == "C1-03")
        self.assertIn("3?.0", item["report_evidence"][0]["quote"])
        self.assertEqual(item["correction"]["actor"], ENGINEER.user_id)

    def test_idempotency_reuses_exact_run_and_rejects_different_revision(self):
        self.confirm(); a=self.execute(); b=self.execute()
        self.assertEqual(a["run_id"], b["run_id"])
        self.confirm(revision=2)
        with self.assertRaises(ConflictError): self.execute(revision=3)

    def test_closed_numeric_boundaries_and_units(self):
        snap = self.confirm()
        for key, value, expected in [("A1:response","0.5 s","no_issue"), ("A1:response","500.01 ms","nonconformity"),
                                      ("A1:response","500","evidence_insufficient"), ("A1:response","-1 ms","evidence_insufficient"),
                                      ("A1:recovery","4.75 V","no_issue"), ("A1:recovery","5.25 V","no_issue"),
                                      ("A1:recovery","5.251 V","nonconformity"), ("A1:recovery","5.0 mV","evidence_insufficient"),
                                      ("A1:temperature","25.0摄氏度 / 37.0摄氏度","no_issue"),
                                      ("A1:temperature","25.0摄氏度 / 37.1摄氏度","nonconformity")]:
            with self.subTest(value=value):
                c = deepcopy(snap); c["corrections"]={key: dict(value=value,reason="测试构造")}
                result = evaluate(c,c["basis"])
                item = next(i for i in result["items"] if i["port"] == key.split(":")[0] and i["kind"] == key.split(":")[1])
                self.assertEqual(item["result"], expected)

    def test_duplicate_records_are_conflict(self):
        snap = self.confirm(); snap["report"]["fields"]["A1:response"] *= 2
        item = evaluate(snap,snap["basis"])["items"][0]
        self.assertEqual(item["result"], "conflict")

    def test_actual_abnormal_appearance_is_not_missing(self):
        snap=self.confirm(); snap["corrections"]={"A1:appearance": dict(value="有起火",reason="测试构造")}
        item=next(i for i in evaluate(snap,snap["basis"])["items"] if i["item_id"]=="A1-04")
        self.assertEqual(item["result"],"nonconformity")
        for wording in ["没有起火", "未发生起火"]:
            snap["corrections"]["A1:appearance"]["value"]=wording
            item=next(i for i in evaluate(snap,snap["basis"])["items"] if i["item_id"]=="A1-04")
            self.assertEqual(item["result"],"evidence_insufficient")

    def test_summary_join_uses_port_not_same_value(self):
        snap=self.confirm(); r=evaluate(snap,snap["basis"])
        conflict=next(i for i in r["items"] if i["item_id"]=="SUMMARY-C1")
        self.assertTrue(any("C1" in x["quote"] for x in conflict["report_evidence"]))
        self.assertFalse(any(i["item_id"]=="SUMMARY-A1" for i in r["items"]))

    def test_missing_fields_do_not_claim_unexecuted(self):
        self.confirm(); r=self.execute()
        for item in r["items"]:
            if item["item_id"] in {"C1-04","C1-05"}:
                self.assertEqual(item["result"], "evidence_insufficient")
                self.assertIn("不能据此推定未测试",item["explanation"])

    def test_tampered_quote_rejected_before_output(self):
        snap=self.confirm(); snap["report"]["fields"]["A1:response"][0]["quote"]="不存在的来源"
        with self.assertRaises(ValueError): evaluate(snap,snap["basis"])

    def test_basis_change_and_deactivation_block_new_checks_but_allow_history(self):
        self.confirm(); self.service.corpus.by_id["SYN-NORM-RESPONSE"]["text"] += "修订"
        with self.assertRaises(ConflictError): self.execute()
        self.service.corpus.by_id["SYN-NORM-RESPONSE"]["publication_status"]="disabled"
        self.assertFalse(self.service.task(ENGINEER,self.tid)["basis_state"]["current_usable"])
        with self.assertRaises(ValueError): self.execute()

    def test_owner_role_and_source_permissions(self):
        self.confirm(); r=self.execute()
        for p in [OTHER,EMPLOYEE]:
            for fn in [lambda:self.service.task(p,self.tid),lambda:self.service.result(p,r["run_id"]),lambda:self.service.pdf(p,self.tid)]:
                with self.assertRaises(PermissionError): fn()
        self.assertEqual(self.service.list_tasks(OTHER), [])
        with self.assertRaises(PermissionError): self.service.catalog(EMPLOYEE)

    def test_review_append_only_optimistic_version_and_result_unchanged(self):
        self.confirm(); r=self.execute(); rid=r["run_id"]
        data=dict(item_id="C1-02",version=0,disposition="excluded",reason="测试构造：记录存在争议，先排除系统发现")
        updated=self.service.review(ENGINEER,rid,data)
        item=next(i for i in updated["items"] if i["item_id"]=="C1-02")
        self.assertEqual(item["result"],"nonconformity")
        self.assertEqual(updated["pending_reviews"],11)
        with self.assertRaises(ConflictError): self.service.review(ENGINEER,rid,data)
        self.service.review(ENGINEER,rid,dict(data,version=1,disposition="unresolved",reason="测试构造：再次记录未决"))
        self.assertEqual(len(self.service.result(ENGINEER,rid)["review_history"]),2)

    def test_review_completion_allows_explicit_unresolved(self):
        self.confirm(); r=self.execute()
        for i in r["items"]:
            out=self.service.review(ENGINEER,r["run_id"],dict(item_id=i["item_id"],version=0,disposition="unresolved",reason="测试构造：暂无法确认"))
        self.assertEqual(out["state"],"review_complete")
        self.assertEqual(out["counts"]["conflict"],2)

    def test_runtime_failure_remains_visible_and_exportable(self):
        self.confirm()
        with patch("app.ai_work.review.evaluate",side_effect=RuntimeError("模拟失败")):
            r=self.execute()
        self.assertEqual(r["state"],"failed")
        self.assertEqual(r["counts"],{"failed":10})
        self.assertTrue(all(i["execution"]=="failed" for i in r["items"]))
        self.assertTrue(export_xlsx(r).startswith(b"PK"))

    def test_restart_restores_task_run_and_review(self):
        self.confirm(); r=self.execute()
        self.service.review(ENGINEER,r["run_id"],dict(item_id="A1-01",version=0,disposition="confirmed",reason="测试构造"))
        new=ReviewService(Path(self.tmp.name)/"review.db",Corpus())
        try:self.assertEqual(new.result(ENGINEER,r["run_id"])["pending_reviews"],11)
        finally:new.db.close()

    def test_invalid_pdf_inputs_and_upload_identical_to_sample(self):
        for blob in [b"",b"%PDF-broken",b"x"*(2*1024*1024+1)]:
            with self.assertRaises(Exception):parse_pdf(blob,"x.pdf")
        from pypdf import PdfWriter
        w=PdfWriter();w.add_blank_page(width=600,height=800);out=BytesIO();w.write(out)
        with self.assertRaises(ValueError):parse_pdf(out.getvalue(),"blank.pdf")
        w.encrypt("test-password");out=BytesIO();w.write(out)
        with self.assertRaises(ValueError):parse_pdf(out.getvalue(),"encrypted.pdf")
        pdf=(ROOT/"output/pdf/SYN-TR-001-R1.pdf").read_bytes()
        uploaded=self.service.create(ENGINEER,dict(filename="uploaded.pdf",pdf_base64=base64.b64encode(pdf).decode()))
        self.assertEqual(uploaded["snapshots"][0]["report"]["sha256"],digest(pdf))

    def test_xlsx_integrity_scope_and_formula_injection(self):
        self.confirm();r=self.execute()
        r=self.service.review(ENGINEER,r["run_id"],dict(item_id="A1-01",version=0,disposition="confirmed",reason='=HYPERLINK("https://example.com")'))
        z=ZipFile(BytesIO(export_xlsx(r)));ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        self.assertEqual(len(workbook_rows(r)),4)
        detail=ET.fromstring(z.read("xl/worksheets/sheet2.xml"))
        self.assertEqual(len(detail.findall("m:sheetData/m:row",ns)),13)
        for name in z.namelist():
            if name.endswith(".xml"):ET.fromstring(z.read(name))
            if name.startswith("xl/worksheets/"):
                self.assertNotIn(b"<f>",z.read(name))
        self.assertIn("=HYPERLINK",z.read("xl/worksheets/sheet4.xml").decode())


class ReviewHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.server=LocalServer(("127.0.0.1",0),ENGINEER,cls.tmp.name)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.port=cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.server.store.db.close();cls.server.review_service.db.close();cls.tmp.cleanup()

    def call(self,method,path,body=None,headers=None):
        c=http.client.HTTPConnection("127.0.0.1",self.port)
        c.request(method,path,json.dumps(body) if body is not None else None,headers or {})
        r=c.getresponse();v=(r.status,r.read(),dict(r.getheaders()));c.close();return v

    def auth(self):
        _,raw,h=self.call("GET","/api/config")
        return {"Cookie":h["Set-Cookie"].split(";")[0],"X-Local-Token":json.loads(raw)["csrf_token"],"Content-Type":"application/json"}

    def test_session_origin_body_limit_and_role_injection(self):
        self.assertEqual(self.call("GET","/api/ai-work/catalog")[0],401)
        h=self.auth()
        self.assertEqual(self.call("POST","/api/ai-work/tasks",{"sample":True},{**h,"Origin":"https://example.com"})[0],403)
        self.assertEqual(self.call("POST","/api/ai-work/tasks",{"sample":True,"owner":"another"},h)[0],400)
        self.assertEqual(self.call("POST","/api/ai-work/tasks",{},dict(h, **{"Content-Length": str(3*1024*1024+1)}))[0],400)

    def test_http_full_flow_upload_review_export_and_stale_conflict(self):
        h=self.auth();status,raw,_=self.call("POST","/api/ai-work/tasks",{"sample":True},h);self.assertEqual(status,200);tid=json.loads(raw)["task_id"]
        base="/api/ai-work/tasks/"+tid
        self.assertEqual(self.call("GET",base+"/pdf",headers=h)[1][:5],b"%PDF-")
        self.assertEqual(self.call("POST",base+"/run",dict(revision=1,idempotency_key="http-test-key"),h)[0],409)
        self.assertEqual(self.call("POST",base+"/confirm",dict(revision=1,acknowledged=True,corrections={}),h)[0],200)
        status,raw,_=self.call("POST",base+"/run",dict(revision=2,idempotency_key="http-test-key"),h);self.assertEqual(status,200);r=json.loads(raw)
        rid=r["run_id"];route="/api/ai-work/runs/"+rid
        data=dict(item_id="C1-01",version=0,disposition="unresolved",reason="HTTP测试用未决记录")
        self.assertEqual(self.call("POST",route+"/review",data,h)[0],200)
        self.assertEqual(self.call("POST",route+"/review",data,h)[0],409)
        status,raw,headers=self.call("GET",route+"/export",headers=h)
        self.assertEqual(status,200);self.assertTrue(raw.startswith(b"PK"));self.assertIn("spreadsheetml",headers["Content-Type"])


if __name__=="__main__":
    unittest.main()
