"""Local answer contracts, source references and explicit scope facts.

Only request-authorized evidence is accepted here. No evaluation data, model
credentials or implicit task state is available to this module.
"""
import re
import unicodedata
from decimal import Decimal


class ProviderError(Exception):
    def __init__(self, message, *, audit=None):
        super().__init__(message)
        self.audit = audit or {}


def compact(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).lower()


def validate_answer(value, evidence):
    if not isinstance(value, dict) or set(value) != {"status", "claims", "limitations"}:
        raise ProviderError("回答结构校验失败，已保留检索结果。")
    if not isinstance(value["status"],str) or value["status"] not in {"answered", "partial", "insufficient_evidence", "conflict"}:
        raise ProviderError("回答状态无效。")
    claims = value["claims"]
    if not isinstance(claims, list) or len(claims) > 12 or (not claims and value["status"] in {"answered", "conflict"}):
        raise ProviderError("回答缺少可核对结论。")
    if not isinstance(value["limitations"], list) or len(value["limitations"]) > 12 or any(not isinstance(x, str) or len(x) > 1000 for x in value["limitations"]):
        raise ProviderError("回答的限制说明格式无效。")
    if not claims and not value["limitations"]:
        raise ProviderError("回答为空，未作为正式结果展示。")
    by_id = {c["chunk_id"]: c for c in evidence}
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"text", "is_inference", "evidence"} or not isinstance(claim["text"], str) or not 1 <= len(claim["text"]) <= 1200 or type(claim["is_inference"]) is not bool:
            raise ProviderError("回答结论格式无效。")
        refs = claim["evidence"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 8:
            raise ProviderError("回答结论缺少引用。")
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {"chunk_id", "quote"} or not isinstance(ref["chunk_id"], str) or ref["chunk_id"] not in by_id or not isinstance(ref["quote"], str) or not 4 <= len(ref["quote"]) <= 600:
                raise ProviderError("引用不在本次授权证据范围内，回答未通过校验。")
            if compact(ref["quote"]) not in compact(by_id[ref["chunk_id"]]["text"]):
                raise ProviderError("引用短句与来源不符，回答未通过校验。")
        # A record-specific fact needs that record, not just a valid rule ID.
        cited=" ".join(ref["quote"] for ref in refs)
        for record in re.findall(r"(?<![a-z0-9])(?:R|S)\d{2}(?![a-z0-9])",claim["text"],re.I):
            if not re.search(r"(?<![a-z0-9])"+re.escape(record)+r"(?![a-z0-9])",cited,re.I):
                raise ProviderError(f"结论提及记录{record.upper()}，但所选引用缺少该记录原文。请选择包含该记录的来源。")
        # An actual summary value needs the summary; a generic conflict policy
        # alone does not establish what the report summary says.
        if "摘要" in claim["text"] and re.search(r"\d+(?:\.\d+)?\s*(?:ms|s|V|K|毫秒|秒|伏)",claim["text"],re.I):
            summary_ids={c["chunk_id"] for c in evidence if c.get("scope","").startswith("task:") and "SUMMARY" in c.get("section","").upper()}
            if summary_ids and not any(ref["chunk_id"] in summary_ids for ref in refs):
                raise ProviderError("结论涉及摘要中的具体数值，但未引用报告摘要原文。请选择摘要来源，同时保留原始记录及冲突规则。")
    # A narrow, explicit contradiction check, not a general semantic judge.
    for text in [c["text"] for c in claims] + value["limitations"]:
        if re.search(r"(?:输入的|输入下的|输入为)(?:\d+(?:\.\d+)?v)?输出角色", compact(text)):
            raise ProviderError("回答混淆输入与输出角色，未通过范围校验。")
    return value


def reference_catalog(evidence):
    """Create finite, request-local references and immutable source excerpts."""
    catalog = {}
    for c in evidence:
        text = c["text"]
        starts = range(0, len(text), 500)
        for start in starts:
            if len(text) - start < 4:
                start = max(0, len(text) - 500)
            quote = text[start:start + 500]
            if len(quote) < 4:
                continue
            catalog[f"REF{len(catalog)+1:03d}"] = dict(chunk_id=c["chunk_id"], quote=quote,
                title=c.get("title"), section=c.get("section"), version=c.get("version"),
                publication_status=c.get("publication_status"), material_type=c.get("material_type"), page=c.get("page"))
            catalog[f"REF{len(catalog):03d}"]["scope"]=c.get("scope","")
    return catalog


def resolve_references(candidate, catalog, evidence, *, completions=None):
    if not isinstance(candidate, dict) or set(candidate) != {"status", "claims", "limitations"} or not isinstance(candidate.get("claims"), list):
        raise ProviderError("回答结构校验失败，已保留检索结果。")
    claims = []
    for index,claim in enumerate(candidate["claims"]):
        if not isinstance(claim, dict) or set(claim) != {"text", "is_inference", "reference_ids"}:
            raise ProviderError("回答须选择来源编号，不能自行填写证据ID或引文。")
        ids = claim["reference_ids"]
        if not isinstance(ids, list) or not 1 <= len(ids) <= 8 or any(not isinstance(r, str) or r not in catalog for r in ids):
            raise ProviderError("引用编号不属于本次提供的来源，回答未通过校验。")
        ids=list(dict.fromkeys(ids))
        # Keep selected citations and complete unique, necessary report anchors
        # from the same authorized catalog. Never map an invented reference ID.
        requirements=[]
        for record in re.findall(r"(?<![a-z0-9])(?:R|S)\d{2}(?![a-z0-9])",str(claim["text"]),re.I):
            choices=[r for r,c in catalog.items() if c["scope"].startswith("task:")
                and re.search(r"(?<![a-z0-9])"+re.escape(record)+r"(?![a-z0-9])",c["quote"],re.I)]
            requirements.append((choices,"record:"+record.upper()))
        if "摘要" in str(claim["text"]) and re.search(r"\d+(?:\.\d+)?\s*(?:ms|s|V|K|毫秒|秒|伏)",str(claim["text"]),re.I):
            requirements.append(([r for r,c in catalog.items() if c["scope"].startswith("task:") and "SUMMARY" in (c["section"] or "").upper()],"summary_value"))
        for choices,reason in requirements:
            if len(choices)==1 and choices[0] not in ids:
                ids.append(choices[0])
                if completions is not None:
                    completions.append(dict(claim_index=index,reference_id=choices[0],chunk_id=catalog[choices[0]]["chunk_id"],reason=reason))
        claims.append(dict(text=claim["text"], is_inference=claim["is_inference"],
            evidence=[{k: catalog[r][k] for k in ["chunk_id", "quote"]} for r in dict.fromkeys(ids)]))
    answer = dict(status=candidate["status"], claims=claims, limitations=candidate["limitations"])
    return validate_answer(answer, evidence)


def scope_answer(question, evidence):
    """Render explicit demo scope without a free-form role paraphrase.

    This small extractor supports the canonical bootstrap scope sentence only.
    Unknown wording, multiple versions and hardware-capability questions fall
    back to normal QA. A dual-purpose connector does not imply both test roles.
    """
    asks_scope = any(t in question for t in ["范围", "覆盖", "配置", "包含", "只测", "测过"])
    asks_role = any(t in question for t in ["输入", "输出", "快充", "电压档", "档位"])
    asks_measurement = any(t in question for t in ["恢复电压", "响应时间", "保护响应", "温升", "壳温", "实测", "限值", "阈值"])
    if not (asks_scope and asks_role) or asks_measurement:
        return None
    matches = []
    for c in evidence:
        if c.get("material_type") != "synthetic" or c.get("section") != "身份与适用范围":
            continue
        match = re.search(r"本任务仅(?P<ports>[A-Z]\d+(?:、[A-Z]\d+)*)的(?P<voltage>\d+(?:\.\d+)?)\s*V(?P<role>输出|输入)角色。", c["text"])
        boundary = re.search(r"其他角色、电压、组合和保护项目未配置。", c["text"])
        if match and boundary:
            matches.append((c, match, boundary))
    if len(matches) != 1:
        return None
    c, match, boundary = matches[0]
    role = match.group("role")
    other = "输入" if role == "输出" else "输出"
    fast = "或全部快充档" if "快充" in question or "档" in question else ""
    claims = [dict(text=f"模拟规格Rev{c['version']}明确的本次配置为{match.group('ports')}的{match.group('voltage')} V{role}角色。",
        is_inference=False, evidence=[dict(chunk_id=c["chunk_id"], quote=match.group(0))]),
        dict(text=f"其他角色、电压、组合和保护项目未配置，不能据此认定{other}角色{fast}已覆盖。",
        is_inference=True, evidence=[dict(chunk_id=c["chunk_id"], quote=c["text"])])]
    answer = dict(status="answered", claims=claims, limitations=[])
    validate_answer(answer, evidence)
    facts = dict(chunk_id=c["chunk_id"], ports=match.group("ports").split("、"),
        voltage_v=match.group("voltage"), role="output" if role == "输出" else "input", version=c["version"])
    return answer, facts


def response_record_answer(question, evidence):
    """Join a named response record and its summary by report, port and field.

    No joining by equal numeric values: 80 ms on A1 is not the C1 summary.
    Only the explicit synthetic response and summary sentence formats are
    supported; other report fields continue through normal grounded QA.
    """
    requested=set(r.upper() for r in re.findall(r"(?<![a-z0-9])R\d{2}(?![a-z0-9])",question,re.I))
    asks_response=any(t in question for t in ["响应","摘要","换算","毫秒","超限"]) or bool(re.search(r"\d+(?:\.\d+)?\s*(?:ms|s)(?![a-z])",question,re.I))
    if len(requested)!=1 or not asks_response:
        return None
    observations=[];rules=[];summaries=[]
    for c in evidence:
        if c.get("material_type")!="synthetic":
            continue
        if c.get("scope","").startswith("task:") and c.get("section")=="P2-RESPONSE":
            for m in re.finditer(r"(R\d{2})\s+([A-Z]\d+)保护响应([0-9]+(?:\.[0-9]+)?)\s*(ms|s)(?![a-zA-Z])",c["text"]):
                if m.group(1) in requested:
                    observations.append((c,m))
        if c.get("section")=="DEMO-01" and "1 s = 1000 ms" in c["text"]:
            m=re.search(r"响应时间不大于([0-9]+(?:\.[0-9]+)?)\s*ms",c["text"])
            if m:rules.append((c,m))
        if c.get("scope","").startswith("task:") and c.get("section")=="P1-SUMMARY":
            for m in re.finditer(r"(S\d{2})[：:]\s*([A-Z]\d+)保护响应([0-9]+(?:\.[0-9]+)?)\s*(ms|s)(?![a-zA-Z])",c["text"]):
                summaries.append((c,m))
    if len(observations)!=1 or len(rules)!=1:
        return None
    source,record=observations[0];rule,limit_match=rules[0]
    summary_matches=[(c,m) for c,m in summaries if c["document_id"]==source["document_id"] and m.group(2)==record.group(2)]
    if len(summary_matches)>1 or ("摘要" in question and not summary_matches):
        return None
    def ms(m):
        return Decimal(m.group(3))*(1000 if m.group(4)=="s" else 1)
    def number(n):
        return format(n,"f").rstrip("0").rstrip(".") if n%1 else str(int(n))
    def ref(c):
        return dict(chunk_id=c["chunk_id"],quote=c["text"])
    measured=ms(record);limit=Decimal(limit_match.group(1))
    claims=[dict(text=f"模拟记录{record.group(1)}属于{record.group(2)}端口，保护响应记载为{record.group(3)} {record.group(4)}。",
        is_inference=False,evidence=[ref(source)])]
    conflict=False;summary_facts=None
    if summary_matches:
        sc,sm=summary_matches[0];summary_value=ms(sm);conflict=summary_value!=measured
        comparison="不一致，存在同端口摘要与明细冲突" if conflict else "一致"
        claims.append(dict(text=f"模拟摘要{sm.group(1)}同样属于{sm.group(2)}端口，记载为{sm.group(3)} {sm.group(4)}；与{record.group(1)}换算后的{number(measured)} ms{comparison}。",
            is_inference=True,evidence=[ref(sc),ref(source)]))
        summary_facts=dict(record_id=sm.group(1),port=sm.group(2),normalized_ms=number(summary_value),chunk_id=sc["chunk_id"])
    result_text=f"仅按模拟记录{record.group(1)}作条件性比较：{record.group(3)} {record.group(4)} = {number(measured)} ms，"
    result_text+=f"{number(measured)} ms {'>' if measured>limit else '≤'} {number(limit)} ms，{'超过' if measured>limit else '未超过'}模拟上限。"
    claims.append(dict(text=result_text,is_inference=True,evidence=[ref(source),ref(rule)]))
    limitations=[]
    if conflict:
        policy=next((c for c in evidence if c.get("section")=="DEMO-06"),None)
        if policy:
            claims.append(dict(text="摘要与明细冲突保留未决，不能静默选择数值或认定通过。",is_inference=False,evidence=[ref(policy)]))
        limitations.append("同端口摘要与原始记录的数值冲突仍需负责人核实；以上仅为模拟记录下的条件性计算。")
    answer=dict(status="conflict" if conflict else "answered",claims=claims,limitations=limitations)
    validate_answer(answer,evidence)
    facts=dict(record_id=record.group(1),port=record.group(2),field="response_ms",normalized_ms=number(measured),
        limit_ms=number(limit),record_chunk_id=source["chunk_id"],rule_chunk_id=rule["chunk_id"],summary=summary_facts,conflict=conflict)
    return answer,facts
