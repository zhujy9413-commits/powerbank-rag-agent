"""Permission-filtered retrieval and grounded single-turn generation.

Only the two allowlisted corpus files are loaded. Evaluation labels are never
read here. BM25 is a transparent baseline, not a semantic embedding model.
"""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import threading
import time
import unicodedata
from uuid import uuid4

from .providers import embeddings, generate, ProviderError

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/bootstrap-v0.1"
WARNING = "模拟材料，仅用于软件流程与评测；数值为人为构造，不代表国家标准、企业实际要求或实测结果。"


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    task_ids: tuple = ()


def compact(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).lower()


def tokens(text):
    text = unicodedata.normalize("NFKC", text).lower()
    result = re.findall(r"[a-z]+[a-z0-9_.-]*|\d+(?:\.\d+)?", text)
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        result.extend(run[i:i+2] for i in range(len(run)-1))
        if len(run) == 1:
            result.append(run)
    return result


def standards(text):
    return [compact(x) for x in re.findall(r"GB\s*(?:/\s*T)?\s*\d+(?:\.\d+)?\s*[-—－]\s*\d{4}", text, re.I)]


def search_text(c):
    return " ".join([c["title"], c["section"], c["text"].replace(WARNING, "")])


class Corpus:
    def __init__(self, base=BASE):
        self.base = Path(base)
        manifest = json.loads((self.base / "manifest.json").read_text())
        self.snapshot = manifest["snapshot_id"]
        self.chunks = []
        for rel in ["index/knowledge-chunks.jsonl", "index/task-chunks.jsonl"]:
            for line in (self.base / rel).read_text().splitlines():
                c = json.loads(line)
                c["search_text"] = search_text(c)
                self.chunks.append(c)
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        if len(self.by_id) != len(self.chunks):
            raise ValueError("Duplicate corpus IDs")
        self.digest = hashlib.sha256(json.dumps([{k:v for k,v in c.items() if k != "search_text"} for c in self.chunks], ensure_ascii=False, sort_keys=True).encode()).hexdigest()

    def accessible(self, c, principal):
        return principal.role in c["allowed_roles"] and (c["scope"] == "knowledge" or c["scope"].removeprefix("task:") in principal.task_ids)

    def source(self, chunk_id, principal):
        c = self.by_id.get(chunk_id)
        if not c or not self.accessible(c, principal):
            raise PermissionError("资料不存在或当前身份无权访问。")
        p = (self.base / c["path"]).resolve()
        if not p.is_relative_to(self.base.resolve()):
            raise PermissionError("原文位置无效。")
        return {**card(c), "original_text": p.read_text(), "excerpt": c["text"]}

    def candidates(self, principal, include_archived=False, task_id=None):
        if task_id and task_id not in principal.task_ids:
            raise PermissionError("当前身份无权访问所选任务。")
        return [c for c in self.chunks if self.accessible(c, principal)
                and (c["publication_status"] == "active" or include_archived)
                and (c["scope"] == "knowledge" or c["scope"] == f"task:{task_id}")]


def card(c):
    return {k:c.get(k) for k in ["chunk_id", "document_id", "title", "section", "text", "version", "publication_status", "material_type", "page", "source_url", "scope"]}


def rank_bm25(question, candidates):
    expanded = question
    for term, extra in {"充电宝":"移动电源", "反应":"响应", "国标":"国家标准", "外壳温度":"壳温", "资料整理":"知识库", "快充":"电压档"}.items():
        if term in question:
            expanded += " " + extra
    query_terms = set(tokens(expanded))
    docs = [Counter(tokens(c["search_text"])) for c in candidates]
    avg = sum(sum(d.values()) for d in docs) / max(1,len(docs))
    df = Counter(t for d in docs for t in d)
    named_standards = standards(question)
    scored = []
    for c, d in zip(candidates, docs):
        length = sum(d.values())
        score = 0.0
        for term in query_terms & d.keys():
            idf = math.log(1 + (len(docs)-df[term]+.5)/(df[term]+.5))
            score += idf * d[term] * 2.5 / (d[term] + 1.5*(.25+.75*length/max(1,avg)))
        title_standards = standards(c["title"])
        if named_standards and set(named_standards) & set(title_standards):
            score += 18
        if re.search(r"(?<![a-z0-9])rev\s*"+re.escape(c["version"])+r"(?![a-z0-9])", question, re.I) and c["document_id"].startswith("SYN-SPEC"):
            score += 2
        for record in re.findall(r"(?<![a-z0-9])R\d{2}(?![a-z0-9])", question, re.I):
            if record.upper() in c["text"]:
                score += 8
        if score > 0:
            scored.append((c,score))
    return sorted(scored,key=lambda row:(-row[1],row[0]["chunk_id"]))


def validate_answer(value, evidence):
    if not isinstance(value, dict) or set(value) != {"status","claims","limitations"}:
        raise ProviderError("回答结构校验失败，已保留检索结果。")
    if value["status"] not in {"answered","partial","insufficient_evidence","conflict"}:
        raise ProviderError("回答状态无效。")
    claims = value["claims"]
    if not isinstance(claims,list) or len(claims)>12 or (not claims and value["status"] in {"answered","conflict"}):
        raise ProviderError("回答缺少可核对结论。")
    if not isinstance(value["limitations"],list) or len(value["limitations"])>12 or any(not isinstance(x,str) or len(x)>1000 for x in value["limitations"]):
        raise ProviderError("回答的限制说明格式无效。")
    if not claims and not value["limitations"]:
        raise ProviderError("回答为空，未作为正式结果展示。")
    by_id = {c["chunk_id"]: c for c in evidence}
    for claim in claims:
        if not isinstance(claim,dict) or set(claim)!={"text","is_inference","evidence"} or not isinstance(claim["text"],str) or not 1<=len(claim["text"])<=1200 or type(claim["is_inference"]) is not bool:
            raise ProviderError("回答结论格式无效。")
        refs=claim["evidence"]
        if not isinstance(refs,list) or not 1<=len(refs)<=8:
            raise ProviderError("回答结论缺少引用。")
        for ref in refs:
            if not isinstance(ref,dict) or set(ref)!={"chunk_id","quote"} or ref["chunk_id"] not in by_id or not isinstance(ref["quote"],str) or not 4<=len(ref["quote"])<=600:
                raise ProviderError("引用不在本次授权证据范围内，回答未通过校验。")
            if compact(ref["quote"]) not in compact(by_id[ref["chunk_id"]]["text"]):
                raise ProviderError("引用短句与来源不符，回答未通过校验。")
    return value


class Assistant:
    def __init__(self, corpus, settings, vector_path, generator=generate, embedder=embeddings):
        self.corpus, self.settings = corpus, settings
        self.vector_path = Path(vector_path)
        self.generator, self.embedder = generator, embedder
        self.index_lock = threading.Lock()
        self.vectors = None
        if self.vector_path.is_file():
            try:
                data = json.loads(self.vector_path.read_text())
                if data["corpus_digest"] == corpus.digest:
                    self.vectors = data
            except (ValueError,KeyError):
                pass

    def fingerprint(self, config):
        return {k:config.get(k) for k in ["provider","base_url","embedding_model"]} if config else None

    def vector_ready(self, config=None):
        config = config or self.settings.snapshot()
        return bool(self.vectors and self.vectors["embedding_config"] == self.fingerprint(config))

    def build_vectors(self):
        if not self.index_lock.acquire(blocking=False):
            raise ValueError("正在建立索引，请等待当前任务完成。")
        try:
            config = self.settings.snapshot()
            chunks = self.corpus.chunks
            vectors = self.embedder(config, [c["search_text"] for c in chunks])
            data = dict(corpus_digest=self.corpus.digest, embedding_config=self.fingerprint(config),
                        vectors={c["chunk_id"]:v for c,v in zip(chunks,vectors)})
            self.vector_path.parent.mkdir(exist_ok=True,parents=True)
            temporary = self.vector_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data))
            temporary.replace(self.vector_path)
            self.vectors=data
            return dict(chunks=len(chunks),snapshot=self.corpus.snapshot)
        finally:
            self.index_lock.release()

    def search(self, question, principal, *, include_archived=False, task_id=None, top_k=6):
        candidates = self.corpus.candidates(principal,include_archived,task_id)
        revisions = {v.lower() for v in re.findall(r"rev\s*([ab])(?![a-z0-9])",question,re.I)}
        if revisions:
            candidates = [c for c in candidates if not c["document_id"].startswith("SYN-SPEC") or c["version"].lower() in revisions]
        if revisions == {"a"}:
            # Current mock norms explicitly adopt RevB. Do not use them as a
            # historical RevA requirement, even if they share the same terms.
            candidates = [c for c in candidates if c["document_id"] != "SYN-QA-SC-1.0"]
        ranked = rank_bm25(question,candidates)
        method = "bm25"
        warning = None
        config = self.settings.snapshot()
        if self.vector_ready(config):
            try:
                vector = self.embedder(config,[question])[0]
                available = [(c,self.vectors["vectors"][c["chunk_id"]]) for c in candidates if c["chunk_id"] in self.vectors["vectors"]]
                if any(len(v)!=len(vector) for _,v in available):
                    raise ProviderError("向量维度变化，请重建索引。")
                dense = sorted([(c,sum(x*y for x,y in zip(v,vector))) for c,v in available],key=lambda t:-t[1])
                scores = Counter()
                for ranking in [ranked,dense]:
                    for n,(c,_) in enumerate(ranking[:12]):
                        scores[c["chunk_id"]]+=1/(60+n+1)
                ranked = [(self.corpus.by_id[cid],s) for cid,s in scores.most_common()]
                method = "bm25+embedding-rrf"
            except ProviderError as exc:
                warning = str(exc)
        # Explicit policies supplement evidence where a metadata source is limited.
        supplements = []
        if standards(question) or any(t in question for t in ["未执行","没做","无依据","缺记录"]):
            supplements.append("POL-EVIDENCE")
        if any(t in question for t in ["未配置","放行","证书"]):
            supplements.append("POL-DECISION")
        by_id={c["chunk_id"]:c for c in candidates}
        selected=[c for c,_ in ranked[:top_k]]
        for cid in supplements:
            if cid in by_id and cid not in {c["chunk_id"] for c in selected}:
                selected=selected[:top_k-1]+[by_id[cid]]
        return selected,method,warning

    def ask(self, question, principal, *, mode="search", include_archived=False, task_id=None):
        if not isinstance(question,str) or not question.strip() or len(question)>1500:
            raise ValueError("请输入1至1500字的问题。")
        if mode not in {"search","answer"} or type(include_archived) is not bool:
            raise ValueError("请求模式或版本范围无效。")
        if task_id is not None and (not isinstance(task_id,str) or task_id not in principal.task_ids):
            raise PermissionError("当前身份无权访问所选任务。")
        start=time.monotonic()
        question=question.strip()
        evidence,method,warning=self.search(question,principal,include_archived=include_archived,task_id=task_id)
        result=dict(request_id=str(uuid4()),status="search_results" if evidence else "insufficient_evidence",mode=mode,
            query=question,claims=[],limitations=[],sources=[card(c) for c in evidence],
            snapshot=self.corpus.snapshot,corpus_digest=self.corpus.digest,
            scope=dict(include_archived=include_archived,task_id=task_id),
            trace=dict(retrieval_method=method,retrieved_chunk_ids=[c["chunk_id"] for c in evidence],
                       generation="not_requested",prompt_version="grounded-qa-v0.1",citation_check="not_run",semantic_review="pending"),usage={})
        if warning:
            result["limitations"].append("向量查询失败，已使用关键词检索。"+warning)
        guard=None
        if not evidence:
            guard="在当前授权范围内未找到相关证据，请补充资料名称或具体问题。"
        elif re.search(r"reva(?![a-z0-9])",compact(question)) and not include_archived:
            result["status"]="needs_scope"
            guard="本次未启用历史资料查询；请明确包含归档版本后再检索。"
        elif principal.role=="employee" and any(x in question for x in ["内部模拟规范","内部规格","内部规范"]):
            guard="当前授权资料不足以回答该内部要求，不能提供其具体数值。"
        elif not task_id and (re.search(r"(?<![a-z0-9])R\d{2}(?![a-z0-9])",question,re.I) or any(x in question for x in ["实测值","报告里","报告中的数值"])):
            result["status"]="needs_scope"
            guard="当前没有选择可访问的任务报告，无法回答报告实测内容。"
        elif standards(question) and not any(set(standards(question)) & set(standards(c["title"])) for c in evidence):
            guard="当前未找到该标准的可用资料，不能用其他标准的内容替代。"
        elif (standards(question) or any(t in question for t in ["国标","国家标准"])) and any(t in question for t in ["条款","限值","阈值","准确要求"]):
            guard="当前标准资料仅为题录或公告摘要，未收录完整技术条款，无法确认条款原文与数值限值。"
        if guard:
            if result["status"] not in {"needs_scope"}:
                result["status"]="insufficient_evidence"
            result["limitations"].append(guard)
            result["trace"]["generation"]="skipped_insufficient_scope_or_evidence"
        elif mode=="answer":
            config=self.settings.snapshot()
            if not config:
                result["status"]="model_not_configured"
                result["limitations"].append("已找到以下资料。连接模型后可基于这些证据生成回答；当前未调用模型。")
                result["trace"]["generation"]="not_configured"
            else:
                result["trace"]["provider"]=config["provider"]
                result["trace"]["model"]=config["model"]
                try:
                    raw,usage=self.generator(config,question,evidence,result["scope"])
                    answer=validate_answer(raw,evidence)
                    result.update(status=answer["status"],claims=answer["claims"])
                    result["limitations"].extend(answer["limitations"])
                    result["trace"]["prompt_sha256"]=usage.pop("_prompt_sha256",None)
                    result["trace"]["canonical_payload_sha256"]=usage.pop("_canonical_payload_sha256",None)
                    result["usage"]=usage
                    result["trace"].update(generation="completed",citation_check="ids_and_quotes_verified")
                except ProviderError as exc:
                    result["status"]="generation_failed"
                    result["limitations"].append(str(exc))
                    result["trace"]["generation"]="failed"
        result["elapsed_ms"]=round((time.monotonic()-start)*1000)
        return result
