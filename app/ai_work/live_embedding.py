"""Metered, fail-closed embedding adapter for the isolated development runner.

Uses the existing provider's validation, single-attempt HTTPS transport and
vector validation. Neither credentials nor endpoint URLs enter the ledger.
"""
from decimal import Decimal
from hashlib import sha256
import json
import re
import time
from urllib.parse import urlparse

from app.knowledge_assistant.providers import embeddings, post, validate_config


MODEL = "text-embedding-v4"
DIMENSIONS = 1024
RATE_PER_MILLION = Decimal("0.5")


class EmbeddingStopped(RuntimeError):
    pass


class MeteredEmbedding:
    def __init__(self, config, *, transport=post, max_cny="1", max_requests=600,
                 deadline_seconds=1800, clock=time.perf_counter, checkpoint=None):
        self._config = validate_config(config)
        host = urlparse(self._config["base_url"]).hostname
        if (self._config["provider"] != "bailian" or
                self._config["embedding_model"] != MODEL or
                not (host == "dashscope.aliyuncs.com" or host.endswith(".cn-beijing.maas.aliyuncs.com"))):
            raise ValueError("verified_beijing_embedding_configuration_required")
        self.identity = f"bailian:cn-beijing:{MODEL}:{DIMENSIONS}:float"
        self._transport = transport
        self._clock = clock
        self._started = clock()
        self.max_cny = Decimal(max_cny)
        self.max_requests = max_requests
        self.deadline_seconds = deadline_seconds
        self.records = []
        self.stopped = None
        self.context = {}
        self._checkpoint = checkpoint

    def _stop(self, code):
        self.stopped = code
        raise EmbeddingStopped(code)

    def _send(self, config, path, payload):
        if self.stopped:
            raise EmbeddingStopped(self.stopped)
        batch = payload["input"]
        # Reserve the documented maximum tokens per accepted text, including
        # unmetered failed attempts. This is deliberately independent of a
        # character/token estimate.
        reserve = 8192 * len(batch)
        charged = sum(r["total_tokens"] if r["total_tokens"] is not None
                      else r["reserved_tokens"] for r in self.records)
        if len(self.records) >= self.max_requests:
            self._stop("request_budget")
        if Decimal(charged + reserve) * RATE_PER_MILLION / 1_000_000 > self.max_cny:
            self._stop("cost_budget")
        if self._clock() - self._started >= self.deadline_seconds:
            self._stop("campaign_deadline")
        entry = dict(sequence=len(self.records)+1, context=dict(self.context),
                     input_count=len(batch), input_sha256=[sha256(t.encode()).hexdigest() for t in batch],
                     input_utf8_bytes=sum(len(t.encode()) for t in batch), reserved_tokens=reserve,
                     total_tokens=None, list_price_cny=None, returned_model=None,
                     request_id=None, status="attempted", attempts=1)
        self.records.append(entry)
        if self._checkpoint:
            self._checkpoint(self.ledger())
        started = self._clock()
        try:
            response = self._transport(config, path, {**payload, "dimensions": DIMENSIONS})
            if not isinstance(response, dict):
                self._stop("invalid_response")
            usage = response.get("usage", {}).get("total_tokens") if isinstance(response.get("usage"), dict) else None
            if type(usage) is int and usage >= 0:
                entry["total_tokens"] = usage
                entry["list_price_cny"] = str(Decimal(usage)*RATE_PER_MILLION/1_000_000)
            model = response.get("model")
            entry["returned_model"] = model if isinstance(model, str) and re.fullmatch(r"[\w./:-]{1,100}", model) else None
            request_id = response.get("id")
            entry["request_id"] = request_id if isinstance(request_id, str) and re.fullmatch(r"[\w-]{1,160}", request_id) else None
            if entry["total_tokens"] is None:
                self._stop("missing_or_invalid_usage")
            if usage > reserve:
                self._stop("usage_exceeds_documented_limit")
            if model != MODEL:
                self._stop("returned_model_mismatch_or_missing")
            data = response.get("data")
            if not isinstance(data, list) or any(not isinstance(x, dict) or not isinstance(x.get("embedding"), list) or len(x["embedding"]) != DIMENSIONS for x in data):
                self._stop("returned_dimension_or_format_mismatch")
            entry["vector_response_sha256"] = sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            entry["status"] = "response_received"
            return response
        except Exception:
            entry["status"] = "failed"
            self.stopped = self.stopped or "provider_failure"
            entry["failure_code"] = self.stopped
            raise EmbeddingStopped(self.stopped) from None
        finally:
            entry["elapsed_ms"] = round((self._clock()-started)*1000, 3)
            if self._checkpoint:
                self._checkpoint(self.ledger())

    def embed(self, texts):
        if self.stopped:
            raise EmbeddingStopped(self.stopped)
        if not isinstance(texts, list) or not texts or any(not isinstance(t, str) or not t or len(t.encode()) > 8192 for t in texts):
            self._stop("invalid_or_oversized_input")
        start = len(self.records)
        try:
            vectors = embeddings(self._config, texts, transport=self._send)
            for row in self.records[start:]:
                row["status"] = "validated"
            return dict(vectors=vectors, model_id=MODEL)
        except Exception:
            self.stopped = self.stopped or "vector_validation_failure"
            # Received usage remains payable even if the vector is rejected.
            for row in self.records[start:]:
                row.update(status="failed", failure_code=self.stopped)
            raise EmbeddingStopped(self.stopped) from None
        finally:
            if self._checkpoint:
                self._checkpoint(self.ledger())

    def ledger(self):
        known = sum(r["total_tokens"] or 0 for r in self.records)
        unknown = [r for r in self.records if r["total_tokens"] is None]
        return dict(model=MODEL, region="cn-beijing", dimensions=DIMENSIONS,
                    model_identity_provenance="requested_and_response_model_alias_matched_not_immutable_revision",
                    price_cny_per_million_input_tokens=str(RATE_PER_MILLION),
                    price_mode="synchronous_online_list_price_before_free_quota_or_discount",
                    request_count=len(self.records), known_total_tokens=known,
                    unknown_usage_requests=len(unknown),
                    known_list_price_cny=str(Decimal(known)*RATE_PER_MILLION/1_000_000),
                    unmetered_reserved_cny=str(Decimal(sum(r["reserved_tokens"] for r in unknown))*RATE_PER_MILLION/1_000_000),
                    actual_account_bill="not_queried", max_cny=str(self.max_cny),
                    max_requests=self.max_requests, stopped=self.stopped, records=self.records)
