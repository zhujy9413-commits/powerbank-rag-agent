"""G01: current authorization and new-check validity are independent gates."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from app.ai_work.export import workbook_rows
from app.ai_work.review import ConflictError, ReviewService
from app.knowledge_assistant.core import Corpus, Principal

USER = Principal("basis-access-test", "engineer", ("DEMO-TASK-001",))
CID = "SYN-NORM-RESPONSE"


class BasisHistoryAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = ReviewService(Path(self.temp.name)/"review.db", Corpus())
        self.task = self.service.create(USER, {"sample": True})
        self.tid = self.task["task_id"]
        self.confirm(1)
        self.request = dict(revision=2, idempotency_key="basis-access-original")
        self.run = self.service.run(USER, self.tid, self.request)
        self.rid = self.run["run_id"]
        self.source = self.service.corpus.by_id[CID]

    def tearDown(self):
        self.service.db.close()
        self.temp.cleanup()

    def confirm(self, revision):
        return self.service.confirm(USER, self.tid, dict(revision=revision, acknowledged=True, corrections={}))

    def persisted(self):
        return {table: self.service.db.execute(f"SELECT * FROM {table}").fetchall()
                for table in ["aw_tasks", "aw_runs", "aw_reviews"]}

    def test_disabled_preserves_reads_and_immutable_storage(self):
        before = self.persisted()
        pdf = self.service.pdf(USER, self.tid)
        self.source["publication_status"] = "disabled"
        self.assertFalse(self.service.catalog(USER)["basis_state"]["current_usable"])
        self.assertEqual(self.service.list_tasks(USER)[0]["task_id"], self.tid)
        self.assertEqual(self.service.task(USER, self.tid)["snapshots"], self.task["snapshots"] + [self.run["snapshot"]])
        current = self.service.result(USER, self.rid)
        self.assertEqual(current["snapshot"], self.run["snapshot"])
        self.assertEqual(current["items"], self.run["items"])
        self.assertEqual(current["input_sha256"], self.run["input_sha256"])
        self.assertTrue(current["basis_state"]["requires_reconfirmation"])
        self.assertEqual(current["basis_state"]["changes"][0]["current_status"], "disabled")
        self.assertEqual(self.service.pdf(USER, self.tid), pdf)
        self.assertEqual(self.service.corpus.source(CID, USER)["publication_status"], "disabled")
        self.assertEqual(before, self.persisted())

    def test_disabled_blocks_confirm_and_fresh_run_but_allows_unconfirmed_import(self):
        self.source["publication_status"] = "disabled"
        before = self.persisted()
        for action in [lambda: self.confirm(2),
                       lambda: self.service.run(USER, self.tid, dict(self.request, idempotency_key="basis-access-new"))]:
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(before, self.persisted())
        fresh=self.service.create(USER, {'sample':True})
        self.assertFalse(fresh['snapshots'][-1]['confirmed'])
        self.assertFalse(fresh['basis_state']['current_usable'])
        with self.assertRaises(ValueError):
            self.service.confirm(USER,fresh['task_id'],dict(revision=1,acknowledged=True,corrections={}))
        with self.assertRaises(ConflictError):
            self.service.run(USER,fresh['task_id'],dict(revision=1,idempotency_key='unconfirmed-import'))

    def test_idempotency_after_disable_returns_saved_run_without_evaluation(self):
        self.source["publication_status"] = "disabled"
        before = self.persisted()
        self.assertEqual(self.service.run(USER, self.tid, self.request)["run_id"], self.rid)
        with self.assertRaises(ConflictError):
            self.service.run(USER, self.tid, dict(self.request, revision=3))
        self.assertEqual(before, self.persisted())

    def test_current_permission_revocation_denies_every_read_and_write(self):
        self.source["publication_status"] = "disabled"
        self.source["allowed_roles"] = []
        actions = [lambda: self.service.catalog(USER), lambda: self.service.list_tasks(USER),
                   lambda: self.service.task(USER, self.tid), lambda: self.service.result(USER, self.rid),
                   lambda: self.service.pdf(USER, self.tid), lambda: self.service.corpus.source(CID, USER),
                   lambda: self.service.run(USER, self.tid, self.request),
                   lambda: self.service.review(USER, self.rid, dict(item_id="A1-01", version=0, disposition="unresolved", reason="test"))]
        before = self.persisted()
        for action in actions:
            with self.assertRaises(PermissionError):
                action()
        self.assertEqual(before, self.persisted())

    def test_missing_current_source_fails_closed(self):
        del self.service.corpus.by_id[CID]
        with self.assertRaises(PermissionError):
            self.service.result(USER, self.rid)

    def test_active_changed_basis_requires_confirmation_and_keeps_old_run(self):
        self.source["text"] += " 修订说明"
        state = self.service.task(USER, self.tid)["basis_state"]
        self.assertTrue(state["current_usable"])
        self.assertTrue(state["requires_reconfirmation"])
        with self.assertRaises(ConflictError):
            self.service.run(USER, self.tid, dict(self.request, idempotency_key="changed-basis-new"))
        self.confirm(2)
        new = self.service.run(USER, self.tid, dict(revision=3, idempotency_key="reconfirmed-new"))
        old = self.service.result(USER, self.rid)
        self.assertFalse(new["basis_state"]["requires_reconfirmation"])
        self.assertTrue(old["historical"])
        self.assertEqual(old["snapshot"], self.run["snapshot"])
        self.assertEqual(old["items"], self.run["items"])

    def test_invalid_format_and_material_change_allow_history_and_unconfirmed_import(self):
        original = deepcopy(self.source)
        for field, value in [("text", "维护中的未发布格式"), ("material_type", "public_metadata"), ("publication_status", "archived")]:
            with self.subTest(field=field):
                self.source.clear(); self.source.update(original); self.source[field] = value
                self.assertFalse(self.service.catalog(USER)["basis_state"]["current_usable"])
                self.assertEqual(self.service.result(USER, self.rid)["snapshot"], self.run["snapshot"])
                fresh=self.service.create(USER, {'sample':True})
                self.assertFalse(fresh['snapshots'][-1]['confirmed'])
                with self.assertRaises(ValueError):
                    self.service.confirm(USER,fresh['task_id'],dict(revision=1,acknowledged=True,corrections={}))
        self.source.clear(); self.source.update(original)
        recovery = self.service.corpus.by_id["SYN-SPEC-PB01-RevB-REC"]
        recovery["text"] = "恢复电压 4..75 V 至 5.25 V，含边界"
        self.assertFalse(self.service.catalog(USER)["basis_state"]["current_usable"])
        self.assertEqual(self.service.result(USER, self.rid)["snapshot"], self.run["snapshot"])
        with self.assertRaises(ValueError):
            self.confirm(2)

    def test_disabled_review_append_and_export_separate_current_state(self):
        before = workbook_rows(self.run)
        self.source["publication_status"] = "disabled"
        run = self.service.review(USER, self.rid, dict(item_id="A1-01", version=0, disposition="unresolved", reason="停用后核对历史证据，保留未决"))
        self.assertEqual(run["items"][0]["result"], self.run["items"][0]["result"])
        self.assertEqual(len(run["review_history"]), 1)
        exported = workbook_rows(run)
        scope = dict(exported[0][1][1:])
        self.assertIn("否", scope["当前依据可用于新检查"])
        self.assertIn("disabled", scope["依据变化明细"])
        self.assertEqual(exported[2], before[2])
        self.assertEqual(run["snapshot"]["basis"][CID]["publication_status"], "active")


if __name__ == "__main__":
    unittest.main()
