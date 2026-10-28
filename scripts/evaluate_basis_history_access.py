"""Isolated HTTP regression and optional browser fixture; never reads production settings."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_workflow_acceptance import Client, read_xlsx, start, stop
from app.ai_work.review import ENGINE_SHA256, stamp

CID = "SYN-NORM-RESPONSE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--exports", type=Path)
    ap.add_argument("--serve-fixture", action="store_true")
    args = ap.parse_args()
    if not args.serve_fixture and (not args.output or not args.exports):
        ap.error("需指定新结果文件及导出目录。")
    if not args.serve_fixture and (args.output.exists() or args.exports.exists()):
        ap.error("路径已存在，拒绝覆盖历史结果。")
    result = dict(version="basis-history-access-v0.4.3", started_at=stamp(), engine_sha256=ENGINE_SHA256,
                  sample_status="consumed_access_regression", model_requests=0, human_business_trial=False, checks=[])
    with tempfile.TemporaryDirectory(prefix="powerbank-basis-access-") as temp:
        server, thread = start(temp)
        client = Client(server)
        try:
            task = client.ok("POST", "/api/ai-work/tasks", {"sample": True})
            tid = task["task_id"]; base = "/api/ai-work/tasks/"+tid
            task = client.ok("POST", base+"/confirm", dict(revision=1, acknowledged=True, corrections={}))
            request = dict(revision=2, idempotency_key="basis-http-original")
            original = client.ok("POST", base+"/run", request)
            rid = original["run_id"]; route = "/api/ai-work/runs/"+rid
            source = server.corpus.by_id[CID]; saved_source = deepcopy(source)
            if args.serve_fixture:
                print(json.dumps(dict(url=f"http://127.0.0.1:{client.port}", task_id=tid, run_id=rid)), flush=True)
                # Controlled test process input, never an application/admin HTTP endpoint.
                for line in sys.stdin:
                    command = line.strip()
                    if command == "stop": break
                    if command not in {"disable", "revoke", "restore"}: continue
                    source.clear(); source.update(deepcopy(saved_source))
                    if command in {"disable", "revoke"}: source["publication_status"] = "disabled"
                    if command == "revoke": source["allowed_roles"] = []
                    print(json.dumps(dict(fixture_state=command)), flush=True)
                return

            def check(name, passed, **evidence):
                result["checks"].append(dict(name=name, passed=bool(passed), **evidence))

            def stored():
                return {table: server.review_service.db.execute(f"SELECT * FROM {table}").fetchall()
                        for table in ["aw_tasks", "aw_runs", "aw_reviews"]}

            args.exports.mkdir(parents=True)
            original_pdf = client.ok("GET", base+"/pdf", raw=True)
            before_export = read_xlsx(client.ok("GET", route+"/export", raw=True))
            before_db = stored()
            source["publication_status"] = "disabled"
            get_routes = ["/api/ai-work/catalog", "/api/ai-work/tasks", base, route, base+"/pdf", route+"/export", "/api/source/"+CID]
            for endpoint in get_routes:
                status, _, _ = client.call("GET", endpoint, raw=True)
                check("disabled_read:"+endpoint, status == 200, status=status)
            current = client.ok("GET", route)
            check("immutable_run_evidence", all(current[k] == original[k] for k in ["snapshot", "items", "counts", "input_sha256", "report_sha256", "engine_sha256", "created_at", "review_history"]))
            check("original_pdf_identical", client.ok("GET", base+"/pdf", raw=True) == original_pdf)
            check("current_status_separate_from_snapshot", not current["basis_state"]["current_usable"] and current["basis_state"]["requires_reconfirmation"] and current["snapshot"]["basis"][CID]["publication_status"] == "active")
            blocked = [("/api/ai-work/tasks", {"sample": True}),
                       (base+"/confirm", dict(revision=2, acknowledged=True, corrections={})),
                       (base+"/run", dict(request, idempotency_key="basis-http-fresh"))]
            for endpoint, body in blocked:
                status, _, _ = client.call("POST", endpoint, body)
                check("disabled_new_work:"+endpoint, status == 400, status=status)
            again = client.ok("POST", base+"/run", request)
            check("disabled_idempotency_read", again["run_id"] == rid)
            check("reads_and_blocked_work_do_not_mutate_storage", stored() == before_db)
            blob = client.ok("GET", route+"/export", raw=True)
            (args.exports/"disabled-basis-history.xlsx").write_bytes(blob)
            rows = read_xlsx(blob); scope = dict(rows["任务与范围"][1:])
            check("export_original_three_detail_sheets", all(rows[k] == before_export[k] for k in ["逐项检查", "依据与原文", "复核记录"]))
            check("export_current_status_visible", "disabled" in scope["依据变化明细"] and scope["当前依据可用于新检查"].startswith("否") and bool(scope["依据当前状态核验时间UTC"]))
            reviewed = client.ok("POST", route+"/review", dict(item_id="A1-01", version=0, disposition="unresolved", reason="隔离回归：停用后核对历史资料，保留未决"))
            check("disabled_review_append", len(reviewed["review_history"]) == 1 and reviewed["items"][0]["result"] == original["items"][0]["result"])
            source["allowed_roles"] = []
            revoked_before = stored()
            for endpoint in get_routes:
                status, _, _ = client.call("GET", endpoint, raw=True)
                check("revoked_read:"+endpoint, status == 403, status=status)
            for endpoint, body in blocked + [(base+"/run", request), (route+"/review", dict(item_id="A1-01", version=1, disposition="confirmed", reason="must deny"))]:
                status, _, _ = client.call("POST", endpoint, body)
                check("revoked_write:"+endpoint, status == 403, status=status)
            check("revocation_no_storage_changes", stored() == revoked_before)
            source.clear(); source.update(saved_source)
            check("access_restored_existing_history", client.ok("GET", route)["review_history"] == reviewed["review_history"])
            source["text"] += " 修订说明"
            status, _, _ = client.call("POST", base+"/run", dict(request, idempotency_key="basis-http-changed"))
            check("active_changed_basis_blocks_unconfirmed_run", status == 409)
            client.ok("POST", base+"/confirm", dict(revision=2, acknowledged=True, corrections={}))
            new = client.ok("POST", base+"/run", dict(revision=3, idempotency_key="basis-http-reconfirmed"))
            check("active_changed_basis_reconfirmation", not new["basis_state"]["requires_reconfirmation"] and new["revision"] == 3)
            check("old_run_preserved_after_reconfirmation", client.ok("GET", route)["snapshot"] == original["snapshot"])
            result["export"] = dict(path=str(args.exports/"disabled-basis-history.xlsx"), sha256=hashlib.sha256(blob).hexdigest())
        finally:
            stop(server, thread)
    result.update(finished_at=stamp(), passed=sum(c["passed"] for c in result["checks"]), total=len(result["checks"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(passed=result["passed"], total=result["total"])))
    if result["passed"] != result["total"]: raise SystemExit(1)


if __name__ == "__main__":
    main()
