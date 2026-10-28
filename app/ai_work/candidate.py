"""Isolated supplementary retrieval. No gold files, provider settings or database access.

Callers supply a confirmed task, principal and original source texts. The existing
rule result is retained verbatim; supplementary evidence never changes a verdict.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import re
import time

from app.knowledge_assistant.core import rank_bm25

VERSION = "candidate-retrieval-0.4"
IDENTITY = ("namespace", "source_role", "source_path", "page", "section", "version", "task_id", "conditions")
FIELDS = {
    "response": r"保护响应|响应时间|短接.*(?:切断|耗时)",
    "recovery": r"恢复电压|输出回到",
    "temperature": r"壳温|壳体温度|末值|起值|温差",
    "appearance": r"外观观察|无起火|无爆炸|无漏液",
    "method": r"恢复方式",
}


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compact(text):
    return re.sub(r"\s+", "", text)


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 5
    per_method: int = 12
    rrf_constant: int = 60
    min_bm25_ratio: float = 0.0
    max_blocks: int = 80
    max_context_per_seed: int = 1
    structured_routing: bool = True

    def __post_init__(self):
        if not (1 <= self.top_k <= 5 and self.per_method == 12 and self.rrf_constant == 60
                and 0 <= self.min_bm25_ratio <= 1 and self.max_blocks == 80 and self.max_context_per_seed == 1):
            raise ValueError("检索参数超出当前协议。")


def seed(c, kind="seed"):
    return {"chunk_id": c["chunk_id"], "kind": kind, "quote": c["text"],
            **{k: deepcopy(c[k]) for k in IDENTITY}}


def normalized_vectors(rows, count):
    if not isinstance(rows, list) or len(rows) != count:
        raise ValueError("embedding_count")
    dimension = None
    result = []
    for row in rows:
        if not isinstance(row, list) or not 16 <= len(row) <= 4096 or (dimension and len(row) != dimension):
            raise ValueError("embedding_dimension")
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in row):
            raise ValueError("embedding_number")
        norm = math.sqrt(sum(x*x for x in row))
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("embedding_norm")
        dimension = len(row)
        result.append([x/norm for x in row])
    return result


def rrf(keyword_ids, vector_ids, constant=60):
    scores = {}
    for order in (keyword_ids, vector_ids):
        for rank, ident in enumerate(order, 1):
            scores[ident] = scores.get(ident, 0) + 1/(constant+rank)
    return sorted(scores, key=lambda ident: (-scores[ident], ident)), scores


def route_candidates(query, candidates, namespace):
    """Shared lexical metadata routing, before either retrieval method.

    Uses only query fields, source roles and original words/context links. No
    numeric thresholds, case IDs, gold labels or rule-result guesses are used.
    """
    field,port=query["field"],query["port"]
    version_query=field=="consistency" and bool(re.search("版本|规格",query["text"]))
    if namespace=="requirement":
        return [c for c in candidates if (
            "仅A1、C1的5 V输出角色" in c["text"]
            or (field in FIELDS and re.search(FIELDS[field],c["text"]))
            or (field=="consistency" and re.search("摘要|一致|冲突",c["text"]))) ]
    observations=[]
    for c in candidates:
        if c["source_role"]!="report_observation" or version_query:continue
        ports=set(re.findall(r"(?<![A-Za-z0-9])(?:A1|C1)(?![A-Za-z0-9])",c["text"]))
        if field=="consistency" or (ports=={port} and re.search(FIELDS[field],c["text"])):
            observations.append(c)
    context_ids={i for c in observations for i in c.get("context_ids",[])}
    ids={c["chunk_id"] for c in observations}
    return [c for c in candidates if c["chunk_id"] in ids or (
        c["source_role"]=="report_context" and observations and (c["chunk_id"] in context_ids or c["conditions"] is not None)) or (
        c["source_role"]=="report_declaration" and version_query) or (
        c["source_role"]=="background" and field=="consistency" and not version_query and "背景摘要" in c["text"])]


class CandidateRetriever:
    """An embedder is optional and explicit: .embed(texts) -> vectors + model_id.

    No implicit model configuration or external calls. Production provider
    preflight and authorization belong to the caller, before injection.
    """
    def __init__(self, chunks, task, principal, originals, *, config=None, embedder=None):
        self.chunks = deepcopy(chunks)
        self.task = deepcopy(task)
        self.principal = principal
        self.originals = originals
        self.config = config or RetrievalConfig()
        self.embedder = embedder
        self._vector_cache = {}
        ids = [c["chunk_id"] for c in self.chunks]
        if len(ids) != len(set(ids)) or len(ids) > self.config.max_blocks:
            raise ValueError("语料ID重复或超出80块限制。")

    def _authorized(self, c, namespace):
        return (self.task.get("task_authorized") is True and self.task["task_id"] in self.principal.task_ids
                and self.principal.role in c["allowed_roles"] and c["task_id"] == self.task["task_id"]
                and c["namespace"] == namespace and c["publication_status"] == "active"
                and c["material_type"] == "synthetic"
                and (namespace != "requirement" or (c["source_role"] == "selected_requirement"
                     and c["chunk_id"] in self.task["selected_requirement_chunks"]
                     and c["version"] == self.task["selected_versions"].get(c["chunk_id"]))))

    def _gate(self):
        if not self.task.get("task_authorized") or self.task["task_id"] not in self.principal.task_ids:
            raise PermissionError("当前身份无权访问任务。")
        # Selected but inactive/inaccessible sources block a new experiment.
        selected = set(self.task["selected_requirement_chunks"])
        available = {c["chunk_id"] for c in self.chunks if self._authorized(c, "requirement") and self._located(c)}
        if not selected <= available:
            raise PermissionError("当前选定依据不可用于新检查。")

    def _located(self, c):
        original = self.originals.get((c["source_path"], c["page"]))
        return isinstance(original, str) and bool(compact(c["text"])) and compact(c["text"]) in compact(original)

    def verify(self, s, namespace):
        c = next((c for c in self.chunks if c["chunk_id"] == s.get("chunk_id")), None)
        return bool(c and self._authorized(c, namespace) and self._located(c)
                    and all(s.get(k) == c[k] for k in IDENTITY) and s.get("quote") == c["text"])

    def retrieve(self, query, namespace, *, method="bm25"):
        started = time.perf_counter()
        self._gate()
        if namespace not in {"requirement", "report"} or method not in {"bm25", "hybrid"}:
            raise ValueError("未知检索来源或方法。")
        if query.get("field") not in {*FIELDS, "consistency"} or query.get("port") not in {"A1", "C1", None}:
            raise ValueError("查询对象或字段不受支持。")
        if not isinstance(query.get("text"), str) or not 0 < len(query["text"]) <= 1000:
            raise ValueError("查询文本无效。")
        if not isinstance(query.get("conditions"),dict):
            raise ValueError("查询条件须显式给出，未知值保留为null。")
        authorized = [c for c in self.chunks if self._authorized(c, namespace)]
        # Verify originals before indexing or sending any provider text.
        candidates = [dict(c, search_text=c["text"], title=c["source_path"], document_id=c["source_path"])
                      for c in authorized if self._located(c)]
        original_valid_count=len(candidates)
        if self.config.structured_routing:
            candidates=route_candidates(query,candidates,namespace)
        corpus_hash = digest([{k:v for k,v in c.items() if k not in {"search_text","title","document_id"}} for c in candidates])
        retrieval_text=query["text"]
        if self.config.structured_routing:
            # Domain vocabulary expansion, identical for keyword and vector arms.
            retrieval_text += " "+dict(response="响应时间 短接 切断 耗时",recovery="恢复电压 输出回到",
                temperature="壳温 起值 末值 温差",appearance="外观观察 起火 爆炸 漏液",
                method="恢复方式",consistency="摘要 原始记录 矛盾")[query["field"]]
        keyword = rank_bm25(retrieval_text, candidates)[:self.config.per_method]
        if keyword:
            keyword = [(c,s) for c,s in keyword if s >= keyword[0][1]*self.config.min_bm25_ratio]
        order = [c["chunk_id"] for c,_ in keyword]
        scores = dict((c["chunk_id"],s) for c,s in keyword)
        vector_order, vector_scores, provider_calls, provider_identity = [], {}, 0, None
        effective, degradation = "bm25", None
        if method == "hybrid":
            if self.embedder is None:
                degradation = "embedding_not_configured"
            elif candidates:
                try:
                    # Model identity and complete task/ACL/source snapshot isolate cache.
                    key = digest([self.task, self.principal.role, self.principal.task_ids,
                                  corpus_hash, self.embedder.identity])
                    cached = self._vector_cache.get(key)
                    if cached is None:
                        provider_calls += 1
                        response = self.embedder.embed([c["text"] for c in candidates])
                        vectors = normalized_vectors(response["vectors"], len(candidates))
                        identity = response["model_id"]
                        if not isinstance(identity, str) or not identity:
                            raise ValueError("embedding_identity")
                        cached = (vectors, identity)
                        self._vector_cache[key] = cached
                    vectors, provider_identity = cached
                    provider_calls += 1
                    response = self.embedder.embed([retrieval_text])
                    qv = normalized_vectors(response["vectors"], 1)[0]
                    if len(qv) != len(vectors[0]) or response["model_id"] != provider_identity:
                        raise ValueError("embedding_model_or_dimension_drift")
                    pairs = [(c["chunk_id"], sum(a*b for a,b in zip(v,qv))) for c,v in zip(candidates,vectors)]
                    pairs.sort(key=lambda x:(-x[1],x[0]))
                    pairs = [x for x in pairs if x[1] > 0][:self.config.per_method]
                    vector_order, vector_scores = [x[0] for x in pairs], dict(pairs)
                    order, scores = rrf(order, vector_order, self.config.rrf_constant)
                    effective = "bm25_embedding_rrf"
                except Exception:
                    # Do not leak transport messages, keys, payloads or config.
                    degradation = "embedding_failure_or_identity_drift"
                    self._vector_cache.clear()
            else:
                degradation="no_eligible_candidates"
        by_id = {c["chunk_id"]:c for c in candidates}
        raw = [seed(by_id[ident]) for ident in order[:self.config.top_k]]
        extensions = []
        seen = {s["chunk_id"] for s in raw}
        for s in raw:
            for ident in by_id[s["chunk_id"]].get("context_ids", [])[:self.config.max_context_per_seed]:
                c = by_id.get(ident)
                if c and ident not in seen and self._authorized(c, namespace) and self._located(c):
                    extensions.append({**seed(c, "context_expansion"), "parent_seed_id":s["chunk_id"]})
                    seen.add(ident)
        accepted, rejected = self._accept(query, raw+extensions, namespace)
        return dict(version=VERSION, namespace=namespace, requested_method=method, effective_method=effective,
                    degradation=degradation, query=deepcopy(query), raw_seeds=raw, context_expansions=extensions,
                    accepted=accepted, rejected=rejected,
                    outcome=dict(state="candidate_evidence_pending_review" if accepted else "evidence_insufficient",
                                 accepted_evidence_ids=[s["chunk_id"] for s in accepted], absence_proof_citation=None,
                                 claims_test_not_performed=False),
                    trace=dict(config=asdict(self.config), retrieval_text=retrieval_text, task_id=self.task["task_id"], actor_role=self.principal.role,
                               filtered_count=len(self.chunks)-len(authorized), source_validation_rejections=len(authorized)-original_valid_count,
                               upstream_routing_exclusions=original_valid_count-len(candidates),
                               candidate_count=len(candidates), corpus_sha256=corpus_hash,
                               keyword_ranking=[dict(chunk_id=c["chunk_id"], score=s) for c,s in keyword],
                               vector_ranking=[dict(chunk_id=i, score=vector_scores[i]) for i in vector_order],
                               fused_ranking=[dict(chunk_id=i,score=scores[i]) for i in order],
                               embedder_calls=provider_calls, embedding_model_identity=provider_identity,
                               elapsed_ms=round((time.perf_counter()-started)*1000,3)))

    def _accept(self, query, evidence, namespace):
        accepted, rejected, contexts = [], [], []
        for s in evidence:
            reason, role = None, "support"
            if not self.verify(s, namespace):
                reason = "identity_original_or_authorization"
            elif namespace == "report":
                if s["source_role"] == "report_context":
                    contexts.append(s);continue
                if query["field"] != "consistency":
                    ports = set(re.findall(r"(?<![A-Za-z0-9])(?:A1|C1)(?![A-Za-z0-9])", s["quote"]))
                    if s["source_role"] != "report_observation":reason = "not_measurement_evidence"
                    elif ports != {query["port"]}:reason = "port_unverified_or_mismatch"
                    elif not re.search(FIELDS[query["field"]], s["quote"]):reason = "field_unverified_or_mismatch"
                    elif not s["conditions"] or any(s["conditions"].get(k)!=v for k,v in query["conditions"].items()):
                        role = "condition_contrast_only"
                elif s["source_role"] not in {"report_observation", "report_declaration", "background"}:
                    reason = "unsupported_consistency_source"
                else:role = "consistency_only"
            if reason:rejected.append(dict(chunk_id=s["chunk_id"],reason=reason))
            else:accepted.append({**s,"evidence_use":role})
        for s in contexts:
            if accepted:accepted.append({**s,"evidence_use":"context_only"})
            else:rejected.append(dict(chunk_id=s["chunk_id"],reason="context_without_support"))
        return accepted,rejected


def augment_baseline(baseline, retrievals):
    original = digest(baseline)
    result = deepcopy(baseline)
    result["candidate_retrieval"] = dict(version=VERSION, original_payload_sha256=original,
                                         evidence=deepcopy(retrievals), adoption="pending_development_validation")
    if digest({k:v for k,v in result.items() if k != "candidate_retrieval"}) != original:
        raise AssertionError("原规则载荷发生变化。")
    return result


def controlled_explanation(original, evidence, provider, *, now_ms, started_ms=0):
    """Bounded adapter for offline fault contracts; no live model transport supplied.

    A supported ID is only structural validation. Accepted drafts remain pending
    semantic review; this helper never changes the system result.
    """
    baseline = deepcopy(original)
    allowed = {s.get("chunk_id", s.get("id")) for s in evidence}
    attempts = []
    for attempt in range(2):
        remaining = 45000-(now_ms()-started_ms)
        if remaining <= 0:break
        timeout = min(20000,remaining)
        entry = dict(attempt=attempt+1,timeout_ms=timeout)
        try:
            raw = provider(evidence=deepcopy(evidence),timeout_ms=timeout,attempt=attempt+1)
            entry["raw_response"] = deepcopy(raw)
            valid = (isinstance(raw,dict) and set(raw)=={"explanation","citation_ids"}
                     and isinstance(raw["explanation"],str) and 0<len(raw["explanation"])<=4000
                     and isinstance(raw["citation_ids"],list) and bool(raw["citation_ids"])
                     and all(isinstance(i,str) and i in allowed for i in raw["citation_ids"]))
            if now_ms()-started_ms >= 45000:raise TimeoutError()
            entry["accepted_structure"] = valid
            attempts.append(entry)
            if valid:return dict(original=baseline,terminal="draft_pending_semantic_review",draft=raw,attempts=attempts)
        except TimeoutError:
            entry.update(error="timeout",accepted_structure=False);attempts.append(entry);break
        except Exception:
            entry.update(error="provider_failure",accepted_structure=False);attempts.append(entry);break
    return dict(original=baseline,terminal="template_fallback",draft=None,attempts=attempts)
