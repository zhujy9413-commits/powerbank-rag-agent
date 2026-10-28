"""Controlled synthetic PDF review. No evaluation labels or LLM verdicts are used."""
import base64
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid

from app.knowledge_assistant.core import ROOT, card, rank_bm25, search_text

VERSION = "synthetic-short-circuit-v0.1"
KINDS = {"response": "保护响应", "recovery": "恢复电压", "temperature": "壳温变化",
         "appearance": "外观观察", "method": "恢复方式"}
LABELS = {"保护响应": "response", "恢复电压": "recovery", "壳温起值/末值": "temperature",
          "外观观察": "appearance", "恢复方式": "method"}
RESULTS = {"no_issue": "未发现问题", "nonconformity": "按记录比较不符合", "conflict": "冲突",
           "evidence_insufficient": "证据不足", "failed": "检查失败", "not_checked": "未检查"}
DISPOSITIONS = {"pending": "待复核", "confirmed": "确认系统结果", "excluded": "排除系统结果", "unresolved": "暂无法确认"}
UNCONFIGURED = ["充电输入角色", "其他电压档", "多口组合", "其他保护功能"]
RULE_SOURCES = {"response": ["SYN-NORM-RESPONSE"], "recovery": ["SYN-NORM-RECOVERY", "SYN-SPEC-PB01-RevB-REC"],
                "temperature": ["SYN-NORM-TEMP"], "appearance": ["SYN-NORM-APPEARANCE"],
                "method": ["SYN-NORM-METHOD"], "consistency": ["SYN-NORM-CONFLICT"]}
ALL_SOURCES = list(dict.fromkeys(["SYN-NORM-RANGE"] + [c for ids in RULE_SOURCES.values() for c in ids]))


class ConflictError(ValueError):
    pass


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


ENGINE_SHA256 = digest(Path(__file__).read_bytes())


def parse_pdf(blob, filename):
    if not isinstance(blob, bytes) or not blob.startswith(b"%PDF-") or not 0 < len(blob) <= 2 * 1024 * 1024:
        raise ValueError("请选择不超过2 MB的可提取文本PDF。")
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError("PDF解析组件未安装，请按AI Work运行说明安装pypdf后重启。") from None
    try:
        reader = PdfReader(BytesIO(blob), strict=True)
        if reader.is_encrypted:
            raise ValueError("暂不支持加密PDF，请提供未加密的模拟报告。")
        if not 1 <= len(reader.pages) <= 12:
            raise ValueError("本版支持1至12页的模拟报告。")
        texts = [p.extract_text() or "" for p in reader.pages]
    except ValueError:
        raise
    except Exception:
        raise ValueError("PDF不可读取，请检查文件是否完整。") from None
    if sum(map(len, texts)) > 80000:
        raise ValueError("PDF提取文字超过本版限制，请缩小输入范围。")
    joined = "\n".join(texts)
    # The published rules below belong only to this explicitly synthetic product.
    if not all(x in joined for x in ["模拟整机保护功能测试报告", "PB-DEMO-01", "模拟材料"]):
        raise ValueError("本版仅支持PB-DEMO-01模拟报告模板；此文件不适用，未套用模拟规则。")
    if not all(x in joined for x in ["5 V输出角色", "记录表A", "记录表B"]):
        raise ValueError("未识别支持的模拟报告布局与5 V输出范围，请提供样本模板。")
    file_hash = digest(blob)
    pages = [dict(source_id=f"PDF-{file_hash[:12]}-P{i+1}", page=i+1, text=t,
                  document_id="uploaded-"+file_hash[:12], title=filename, sha256=file_hash,
                  scope="task_only", material_type="synthetic") for i, t in enumerate(texts)]
    fields = {p+":"+k: [] for p in ["A1", "C1"] for k in KINDS}
    pattern = re.compile(r"(?m)^(R\d{2})\s+(A1|C1)\s+(保护响应|恢复电压|壳温起值/末值|外观观察|恢复方式)\s+([^\n]+)")
    for page in pages:
        for m in pattern.finditer(page["text"]):
            record_id, port, label, value = m.groups()
            fields[port+":"+LABELS[label]].append(dict(record_id=record_id, port=port, kind=LABELS[label],
                value=value.strip(), source_id=page["source_id"], page=page["page"], quote=m.group(0)))
    summary = []
    for page in pages:
        for m in re.finditer(r"(S\d{2})[：:]\s*(A1|C1)保护响应\s*([\d.]+)\s*(ms|s)(?![a-zA-Z])", page["text"]):
            summary.append(dict(record_id=m[1], port=m[2], value=m[3]+" "+m[4], source_id=page["source_id"],
                                page=page["page"], quote=m.group(0)))
    basis_matches = re.findall(r"报告填写的规格版本[：:]\s*SYN-SPEC-PB01-(Rev[A-Z])", joined)
    # Never choose the first of several incompatible identities silently.
    bases = sorted(set(basis_matches))
    basis = bases[0] if len(bases) == 1 else None
    ids = [r["record_id"] for rows in fields.values() for r in rows]
    duplicated = sorted(k for k, n in Counter(ids).items() if n > 1)
    return dict(filename=filename, sha256=file_hash, page_count=len(pages), pages=pages, fields=fields,
                summary=summary, report_basis=basis, duplicate_record_ids=duplicated,
                model="PB-DEMO-01", parser="pypdf-controlled-table-v0.1", parsed_at=stamp())


def number(value, units):
    m = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*("+"|".join(map(re.escape, units))+r")\s*", value)
    if not m:
        return None
    return Decimal(m[1]) * units[m[2]]


def basis_catalog(corpus, principal):
    result = {}
    for cid in ALL_SOURCES:
        c = corpus.by_id.get(cid)
        if not c or not corpus.accessible(c, principal):
            raise PermissionError("当前身份无权使用评审依据。")
        if c["publication_status"] != "active" or c["material_type"] != "synthetic":
            raise ValueError("模拟规则依据已停用或身份改变，请重新确认规则。")
        result[cid] = card(c)
    return result


def get_limits(basis):
    # Parse the actual published source text, not the reference annotation table.
    def one(cid, expression):
        m = re.search(expression, basis[cid]["text"])
        if not m:
            raise ValueError("规则依据格式变化，需维护者重新核实并发布。")
        return m
    response = Decimal(one("SYN-NORM-RESPONSE", r"不大于(\d+(?:\.\d+)?) ms")[1])
    temp = Decimal(one("SYN-NORM-TEMP", r"上限(\d+(?:\.\d+)?) K")[1])
    recovery = one("SYN-SPEC-PB01-RevB-REC", r"([\d.]+) V 至 ([\d.]+) V，含边界")
    scope = basis["SYN-NORM-RANGE"]["text"]
    if "仅A1、C1的5 V输出角色" not in scope:
        raise ValueError("模拟规则适用范围变化，需重新发布。")
    return dict(response=response, temperature=temp, recovery=(Decimal(recovery[1]), Decimal(recovery[2])))


def report_ref(page, quote=None):
    quote = quote or page["text"]
    if quote not in page["text"]:
        raise ValueError("报告引用未通过原文校验。")
    return {k:page[k] for k in ["source_id", "page", "document_id", "title", "sha256"]} | {"quote": quote}


def evaluate(snapshot, basis):
    started = time.perf_counter()
    report = snapshot["report"]
    limits = get_limits(basis)
    pages = {p["source_id"]: p for p in report["pages"]}
    items, trace = [], []
    def make(item_id, port, kind, result, explanation, requirement, refs, extra=None):
        sources = RULE_SOURCES[kind]
        item = dict(item_id=item_id, port=port, kind=kind, title=KINDS.get(kind, "资料一致性"),
                    execution="completed", result=result, explanation=explanation, requirement=requirement,
                    basis=[basis[c] for c in sources], report_evidence=refs, conditional=False)
        if extra:
            item.update(extra)
        # Recheck both independent evidence namespaces before emitting a result.
        for ref in refs:
            report_ref(pages[ref["source_id"]], ref["quote"])
        items.append(item)
        return item
    for port in ["A1", "C1"]:
        for n, kind in enumerate(KINDS, 1):
            key = port+":"+kind
            rows = report["fields"][key]
            query = port+" "+KINDS[kind]
            candidates = [dict(p, chunk_id=p["source_id"], version="uploaded", section="PDF提取文字", search_text=search_text(dict(p, section="PDF提取文字"))) for p in pages.values()]
            ranked = rank_bm25(query, candidates)
            trace.append(dict(item_key=key, query=query, method="task_filtered_bm25+field_port_scan",
                              ranked_page_ids=[p["source_id"] for p, _ in ranked],
                              scanned_page_ids=list(pages), matched_records=[r["record_id"] for r in rows]))
            refs = [report_ref(pages[r["source_id"]], r["quote"]) for r in rows]
            requirement = {"response": f"响应时间 ≤ {limits['response']} ms", "recovery": f"{limits['recovery'][0]} V ≤ 恢复电压 ≤ {limits['recovery'][1]} V",
                           "temperature": f"末值－起值 ≤ {limits['temperature']} K", "appearance": "每个端口明确记录无起火、无爆炸、无漏液", "method": "每个端口有非空恢复方式记录"}[kind]
            result, explanation, calc = "evidence_insufficient", "未定位到此端口、字段的可识别记录；需补证，不能据此推定未测试。", None
            if len(rows) > 1 or any(r["record_id"] in report["duplicate_record_ids"] for r in rows):
                result, explanation = "conflict", "同一核对单元有多条记录或记录ID重复，需确认对应关系。"
            elif len(rows) == 1:
                row = rows[0]
                correction = snapshot["corrections"].get(key)
                value = correction["value"] if correction else row["value"]
                if kind in {"response", "recovery"}:
                    val = number(value, {"ms": Decimal(1), "s": Decimal(1000)} if kind == "response" else {"V": Decimal(1)})
                    if val is not None and val >= 0:
                        if kind == "response":
                            ok = val <= limits["response"]
                            calc = f"{value} = {val} ms；{val} {'≤' if ok else '>'} {limits['response']} ms"
                        else:
                            lo, hi = limits["recovery"]
                            ok = lo <= val <= hi
                            calc = f"{val} V {'位于' if ok else '不在'} [{lo}, {hi}] V（含边界）"
                        result, explanation = ("no_issue" if ok else "nonconformity"), calc
                    else:
                        explanation = "数值、单位或关键位无法确认；本项停止比较，需核对原文。"
                elif kind == "temperature":
                    match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)摄氏度\s*/\s*([+-]?\d+(?:\.\d+)?)摄氏度\s*", value)
                    if match:
                        delta = Decimal(match[2])-Decimal(match[1])
                        ok = delta <= limits["temperature"]
                        calc = f"{match[2]} − {match[1]} = {delta} K；{delta} {'≤' if ok else '>'} {limits['temperature']} K"
                        result, explanation = ("no_issue" if ok else "nonconformity"), calc
                    else:
                        explanation = "壳温起值或末值关键位/单位无法确认；不猜测模糊数字。"
                elif kind == "appearance":
                    if value == "无起火、无爆炸、无漏液":
                        result, explanation = "no_issue", "此端口三项无异常观察均有明确文字记录。"
                    elif re.search(r"(?:^|[，、；。\s])(?:有|发生)(?:起火|爆炸|漏液)", value):
                        result, explanation = "nonconformity", "此端口记录明确出现异常，需专业复核。"
                    else:
                        explanation = "外观文字不满足已配置的明确记录格式，需人工核对三项观察。"
                elif kind == "method" and value.startswith("记录为") and value.removeprefix("记录为").strip() not in {"", "-", "—"}:
                    result, explanation = "no_issue", "此端口存在恢复方式文字记录；仅核对记录完整性。"
                if correction:
                    explanation += "（使用人工确认的解析修正，原文与修正原因保留。）"
            elif ranked:
                # Location for an absence finding is the searched report context, not a fabricated record.
                context = pages[ranked[0][0]["source_id"]]
                negative = re.search(r"无记录ID\s+"+port+r"\s+"+re.escape(KINDS[kind])+r"\s+-", context["text"])
                refs = [report_ref(context, negative.group(0) if negative else context["text"][:400])]
            item = make(f"{port}-{n:02d}", port, kind, result, explanation, requirement, refs,
                        dict(calculation=calc, record_ids=[r["record_id"] for r in rows], correction=snapshot["corrections"].get(key)))
            if kind == "response" and len(rows) == 1:
                summaries = [s for s in report["summary"] if s["port"] == port]
                raw = number(snapshot["corrections"].get(key, {}).get("value", rows[0]["value"]), {"ms": Decimal(1), "s": Decimal(1000)})
                if summaries and raw is not None:
                    vals = [number(s["value"], {"ms": Decimal(1), "s": Decimal(1000)}) for s in summaries]
                    if any(v != raw for v in vals):
                        item["conditional"] = True
                        item["explanation"] += "；同端口摘要与明细冲突未决，比较结果为条件性结果，不能形成最终通过结论。"
                        item["report_evidence"] += [report_ref(pages[s["source_id"]], s["quote"]) for s in summaries]
                        item["basis"].append(basis["SYN-NORM-CONFLICT"])
    for port in ["A1", "C1"]:
        detail = next(i for i in items if i["port"] == port and i["kind"] == "response")
        summaries = [s for s in report["summary"] if s["port"] == port]
        if detail["conditional"]:
            refs = detail["report_evidence"]
            make("SUMMARY-"+port, port, "consistency", "conflict", "同一端口保护响应的摘要与明细数值不一致；双方均保留，待人工确认。",
                 "同对象、同字段的摘要与明细需一致", refs)
        elif summaries:
            comparable = len(report["fields"][port+":response"]) == 1 and len(summaries) == 1 and detail.get("calculation") is not None
            make("SUMMARY-"+port, port, "consistency", "no_issue" if comparable else "evidence_insufficient",
                 "摘要与明细的同端口响应数值一致。" if comparable else "明细或摘要不能唯一对应或数值不可识别，尚无法核对一致性。",
                 "同对象、同字段的摘要与明细需一致", detail["report_evidence"]+[report_ref(pages[s["source_id"]],s["quote"]) for s in summaries])
    if not report["summary"]:
        make("SUMMARY-MISSING", "报告", "consistency", "evidence_insufficient", "全文未定位支持格式的响应摘要，无法核对摘要与明细一致性。",
             "摘要与明细对应关系可核实", [report_ref(report["pages"][0],report["pages"][0]["text"][:300])])
    first = report["pages"][0]
    report_basis = report["report_basis"]
    basis_page = next((p for p in report["pages"] if "报告填写的规格版本" in p["text"]), first)
    basis_line = next((line for line in basis_page["text"].splitlines() if "报告填写的规格版本" in line), basis_page["text"][:400])
    make("BASIS-VERSION", "报告", "consistency", "conflict" if report_basis and report_basis != "RevB" else "no_issue" if report_basis else "evidence_insufficient",
         f"报告填写{report_basis or '版本不明'}，任务明确采用RevB。" + ("版本差异保留；按RevB进行条件性核对，不用报告自填的通过覆盖依据。" if report_basis != "RevB" else "版本相符。"),
         "本任务采用SYN-SPEC-PB01-RevB", [report_ref(basis_page, basis_line)],
         dict(basis=[basis[c] for c in ["SYN-NORM-RECOVERY", "SYN-SPEC-PB01-RevB-REC", "SYN-NORM-CONFLICT"]]))
    return dict(items=items, counts=dict(Counter(i["result"] for i in items)), configured_units=10,
                consistency_items=len(items)-10, unconfigured=UNCONFIGURED, retrieval_trace=trace,
                elapsed_ms=round((time.perf_counter()-started)*1000, 2), generator="deterministic_rules_no_llm",
                professional_review="pending", rule_version=VERSION)


class ReviewService:
    def __init__(self, path, corpus):
        self.corpus = corpus
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript("""CREATE TABLE IF NOT EXISTS aw_tasks(id TEXT PRIMARY KEY, owner TEXT, payload TEXT, pdf BLOB);
        CREATE TABLE IF NOT EXISTS aw_runs(id TEXT PRIMARY KEY, task_id TEXT, request_key TEXT, payload TEXT, UNIQUE(task_id,request_key));
        CREATE TABLE IF NOT EXISTS aw_reviews(run_id TEXT, item_id TEXT, version INTEGER, payload TEXT, PRIMARY KEY(run_id,item_id,version));""")

    def auth(self, principal):
        return basis_catalog(self.corpus, principal)

    def catalog(self, principal):
        basis = self.auth(principal)
        limits = get_limits(basis)
        return dict(rule_version=VERSION, selected_basis="RevB", model="PB-DEMO-01", ports=["A1", "C1"],
                    voltage="5 V", role="输出", kinds=KINDS, basis=list(basis.values()),
                    unconfigured=UNCONFIGURED, limits={k:str(v) for k,v in limits.items()})

    def create(self, principal, data):
        self.auth(principal)
        if set(data)-{"sample", "filename", "pdf_base64"}:
            raise ValueError("任务输入字段无效。")
        if data == {"sample": True}:
            self.corpus.source("TR-P2-RESPONSE", principal)
            blob = (ROOT/"output/pdf/SYN-TR-001-R1.pdf").read_bytes()
            filename = "SYN-TR-001-R1.pdf"
        else:
            if set(data) != {"filename", "pdf_base64"} or not isinstance(data["filename"], str) or not isinstance(data["pdf_base64"], str):
                raise ValueError("请选择模拟PDF或使用预置样本。")
            filename = data["filename"]
            if not re.fullmatch(r"[^/\\\x00-\x1f]{1,150}\.pdf", filename, re.I):
                raise ValueError("PDF文件名无效。")
            try:
                blob = base64.b64decode(data["pdf_base64"], validate=True)
            except ValueError:
                raise ValueError("PDF上传编码无效。") from None
        report = parse_pdf(blob, filename)
        task_id = "AW-"+uuid.uuid4().hex[:12]
        snapshot = dict(revision=1, confirmed=False, report=report, corrections={}, created_at=stamp(),
                        confirmed_by=None, basis=None, rule_version=VERSION)
        payload = dict(task_id=task_id, created_at=stamp(), snapshots=[snapshot])
        with self.lock, self.db:
            self.db.execute("INSERT INTO aw_tasks VALUES(?,?,?,?)", (task_id, principal.user_id, json.dumps(payload, ensure_ascii=False), blob))
        return self.task(principal, task_id)

    def _task(self, principal, task_id):
        self.auth(principal)
        row = self.db.execute("SELECT payload FROM aw_tasks WHERE id=? AND owner=?", (task_id, principal.user_id)).fetchone()
        if not row:
            raise PermissionError("任务不存在或当前身份无权访问。")
        return json.loads(row[0])

    def task(self, principal, task_id):
        with self.lock:
            payload = self._task(principal, task_id)
            runs = [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM aw_runs WHERE task_id=? ORDER BY rowid DESC", (task_id,))]
            return dict(**payload, runs=[dict(run_id=r["run_id"], revision=r["revision"], created_at=r["created_at"]) for r in runs])

    def list_tasks(self, principal):
        self.auth(principal)
        with self.lock:
            rows = [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM aw_tasks WHERE owner=? ORDER BY rowid DESC LIMIT 50", (principal.user_id,))]
        return [dict(task_id=r["task_id"], created_at=r["created_at"], revision=r["snapshots"][-1]["revision"], filename=r["snapshots"][-1]["report"]["filename"]) for r in rows]

    def confirm(self, principal, task_id, data):
        if set(data) != {"revision", "acknowledged", "corrections"} or data["acknowledged"] is not True or not isinstance(data["corrections"], dict):
            raise ValueError("请确认报告身份、模拟依据与检查范围。")
        with self.lock, self.db:
            payload = self._task(principal, task_id)
            old = payload["snapshots"][-1]
            if type(data["revision"]) is not int or old["revision"] != data["revision"]:
                raise ConflictError("输入版本已变化，请刷新后确认。")
            corrections = {}
            for key, value in data["corrections"].items():
                if key not in old["report"]["fields"] or len(old["report"]["fields"][key]) != 1 or not isinstance(value, dict) or set(value) != {"value", "reason"}:
                    raise ValueError("只能修正已唯一定位的解析字段。缺失记录请补充报告。")
                if not all(isinstance(value[k], str) and 0 < len(value[k].strip()) <= 300 for k in value):
                    raise ValueError("解析修正需填写有效值和原因（各1至300字）。")
                corrections[key] = dict(value=value["value"].strip(), reason=value["reason"].strip(), actor=principal.user_id, at=stamp())
            basis = self.auth(principal)
            get_limits(basis)
            snapshot = deepcopy(old)
            snapshot.update(revision=old["revision"]+1, confirmed=True, corrections=corrections,
                            confirmed_by=principal.user_id, confirmed_at=stamp(), basis=basis, publication=self.corpus.snapshot)
            payload["snapshots"].append(snapshot)
            self.db.execute("UPDATE aw_tasks SET payload=? WHERE id=?", (json.dumps(payload, ensure_ascii=False), task_id))
        return self.task(principal, task_id)

    def run(self, principal, task_id, data):
        if set(data) != {"revision", "idempotency_key"} or not isinstance(data["idempotency_key"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", data["idempotency_key"]):
            raise ValueError("运行请求字段无效。")
        with self.lock, self.db:
            payload = self._task(principal, task_id)
            prior = self.db.execute("SELECT id,payload FROM aw_runs WHERE task_id=? AND request_key=?", (task_id, data["idempotency_key"])).fetchone()
            if prior:
                if json.loads(prior[1])["revision"] != data["revision"]:
                    raise ConflictError("同一幂等标识不能用于不同输入版本。")
                return self.result(principal, prior[0])
            snapshot = payload["snapshots"][-1]
            if type(data["revision"]) is not int or data["revision"] != snapshot["revision"] or not snapshot["confirmed"]:
                raise ConflictError("请先确认当前输入版本、依据与范围，再开始检查。")
            current = self.auth(principal)
            if digest(current) != digest(snapshot["basis"]):
                raise ConflictError("依据内容已变化，请重新确认后运行。")
            run_id = "RUN-"+uuid.uuid4().hex[:12]
            try:
                result = evaluate(snapshot, snapshot["basis"])
                state = "awaiting_review"
            except Exception as exc:
                # A task failure must expose all configured units as incomplete.
                failed = [dict(item_id=f"{p}-{n:02d}", port=p, kind=k, title=KINDS[k], execution="failed",
                               result="failed", explanation="规则执行未完成，未产生检查结论。", requirement="需重新运行核查",
                               basis=[snapshot["basis"][c] for c in RULE_SOURCES[k]], report_evidence=[], conditional=False)
                          for p in ["A1", "C1"] for n,k in enumerate(KINDS,1)]
                result = dict(items=failed, counts={"failed":10}, configured_units=10, consistency_items=0,
                              unconfigured=UNCONFIGURED, error="检查未完成；请核查规则与输入后新建运行。", error_type=type(exc).__name__)
                state = "failed"
            result.update(run_id=run_id, task_id=task_id, revision=snapshot["revision"], created_at=stamp(), state=state,
                          input_sha256=digest(snapshot), report_sha256=snapshot["report"]["sha256"], snapshot=snapshot,
                          engine_sha256=ENGINE_SHA256)
            self.db.execute("INSERT INTO aw_runs VALUES(?,?,?,?)", (run_id, task_id, data["idempotency_key"], json.dumps(result, ensure_ascii=False)))
        return self.result(principal, run_id)

    def result(self, principal, run_id):
        with self.lock:
            row = self.db.execute("SELECT task_id,payload FROM aw_runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                raise PermissionError("运行不存在或当前身份无权访问。")
            task = self._task(principal, row[0])
            result = json.loads(row[1])
            history = [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM aw_reviews WHERE run_id=? ORDER BY rowid", (run_id,))]
            latest = {r["item_id"]: r for r in history}
            for item in result["items"]:
                item["review"] = latest.get(item["item_id"], dict(version=0, disposition="pending", reason=""))
            result["review_history"] = history
            result["pending_reviews"] = sum(i["review"]["disposition"] == "pending" for i in result["items"])
            if result["state"] != "failed":
                result["state"] = "review_complete" if result["pending_reviews"] == 0 else "awaiting_review"
            result["historical"] = result["revision"] != task["snapshots"][-1]["revision"]
            return result

    def review(self, principal, run_id, data):
        if set(data) != {"item_id", "version", "disposition", "reason"} or not isinstance(data["disposition"],str) or data["disposition"] not in set(DISPOSITIONS)-{"pending"}:
            raise ValueError("复核字段或处置无效。")
        if not isinstance(data["reason"], str) or not 0 < len(data["reason"].strip()) <= 1000:
            raise ValueError("请填写1至1000字复核理由。")
        with self.lock, self.db:
            result = self.result(principal, run_id)
            item = next((i for i in result["items"] if i["item_id"] == data["item_id"]), None)
            if not item:
                raise ValueError("检查项不存在。")
            if type(data["version"]) is not int or data["version"] != item["review"]["version"]:
                raise ConflictError("复核记录已更新，请刷新后提交。")
            entry = dict(**data, actor=principal.user_id, at=stamp())
            entry["version"] += 1
            self.db.execute("INSERT INTO aw_reviews VALUES(?,?,?,?)", (run_id, data["item_id"], entry["version"], json.dumps(entry, ensure_ascii=False)))
        return self.result(principal, run_id)

    def pdf(self, principal, task_id):
        with self.lock:
            self._task(principal, task_id)
            return self.db.execute("SELECT pdf FROM aw_tasks WHERE id=?", (task_id,)).fetchone()[0]
