"""Development provider: the self-hosted Codex gateway (POST /v1/run with output_schema).

No native tool calls, no streaming. Allowance usage is recorded in tokens; it is not a Nebius dollar cost.

Pacing (17 Oct 2026): every request takes a slot from the process-wide RateGovernor of its key (attest/models/pacing.py), so
all roles and all worker threads share one hourly budget and at most a couple of requests are in flight. A definite
rejection (HTTP 429, nothing executed) is recorded as a failed call, blocks the key, and the request is retried after a
bounded wait; a transport-uncertain failure is never retried. When the bounded wait is exceeded the call fails visibly with
ModelError(rate_limited=True); nothing here ever selects another provider.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from ..http import HttpError, TransportError, request_json
from ..ledger import Ledger, ModelCall, utcnow
from .base import ModelError, ModelResult, extract_usage, validate_json
from .pacing import MAX_429_RETRIES, PacingError, RateGovernor, governor_for

DEFAULT_ROLES = {
    "spec": ("gpt-6-astra", "low"),
    "seal": ("gpt-6-sol", "medium"),
    "implement": ("gpt-6-sol", "medium"),
    "break": ("gpt-6-sol", "medium"),
    "audit": ("gpt-6-astra", "low"),
    "arbitrate": ("gpt-6-astra", "medium"),
    "summary": ("gpt-6-luna", "low"),
}


def roles_from_env(default: dict) -> dict:
    spec = os.environ.get("ATTEST_CODEX_ROLES", "")
    roles = dict(default)
    for item in filter(None, (s.strip() for s in spec.split(","))):
        role, _, selection = item.partition("=")
        model, _, effort = selection.partition(":")
        roles[role.strip()] = (model.strip(), effort.strip() or None)
    return roles


class CodexGateway:
    name = "codex_gateway"

    DEFAULT_BASE_URL = os.environ.get("ATTEST_CODEX_BASE_URL", "https://development-gateway.invalid")  # the team's private gateway; set the variable elsewhere

    def __init__(self, api_key: str, ledger: Ledger, base_url: str | None = None,
                 roles: dict | None = None, timeout_s: int = 300, deadline_s: int = 420, governor: RateGovernor | None = None,
                 notify=None):
        self._key = api_key
        self.base = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.ledger = ledger
        self.roles = roles_from_env(roles or DEFAULT_ROLES)
        self.timeout_s = timeout_s
        self.deadline_s = deadline_s
        self._catalog: dict | None = None
        self.governor = governor or governor_for(api_key)  # shared by every instance built for this key in the process
        self.notify = notify  # optional callable(str) for pacing messages (pipeline log, console events, harness output)

    POLICY_REFRESH_S = 900

    def adopt_gateway_policy(self, force: bool = False) -> None:
        """Read `GET /v1/status` once per policy window and let the governor adopt the declared limits. Unreadable status
        keeps the conservative default; the outcome is recorded in the governor's snapshot (provenance)."""
        checked = self.governor.policy_checked_at
        if not force and checked is not None and time.time() - checked < self.POLICY_REFRESH_S:
            return
        try:
            self.governor.configure_from_status(self.status(), source="gateway status")
        except (HttpError, TransportError) as error:
            self.governor.policy_checked_at = time.time()
            self.governor.policy_source = f"status unreadable ({type(error).__name__}); keeping {self.governor.policy_source}"

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def status(self) -> dict:
        _, body, _ = request_json("GET", self.base + "/status", self._headers(), timeout=30)
        return body or {}

    def catalog(self) -> dict:
        if self._catalog is None:
            _, body, _ = request_json("GET", self.base + "/models", self._headers(), timeout=30)
            self._catalog = {item.get("id"): item.get("supported_reasoning_efforts") or []
                             for item in (body or {}).get("data", [])}
        return self._catalog

    def resolve(self, role: str) -> tuple[str, str | None]:
        model, effort = self.roles.get(role) or self.roles["implement"]
        catalog = self.catalog()
        if model not in catalog:
            raise ModelError(f"model {model!r} for role {role!r} is not in the gateway catalog {sorted(catalog)}")
        if effort and catalog[model] and effort not in catalog[model]:
            raise ModelError(f"effort {effort!r} unsupported for {model!r}; supported: {catalog[model]}")
        return model, effort

    def _public(self, text: str) -> str:
        """Error text for ledgers and verdicts: the gateway's host name never enters a bundle (bundles are downloadable)."""
        return text.replace(self.base, "development-gateway")

    def describe(self) -> dict:
        self.adopt_gateway_policy()  # so the provenance recorded at pipeline start shows the policy the run will use
        pacing = self.governor.snapshot()
        # the gateway is private: bundles record a digest of its URL, not the host name
        return {"provider": self.name, "base_url": None, "base_url_sha256": hashlib.sha256(self.base.encode("utf-8")).hexdigest()[:16],
                "roles": {k: list(v) for k, v in self.roles.items()},
                "structured_endpoint": "/run", "native_tools": False, "streaming": False, "auto_retry": False,
                "retry_policy": "HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried",
                "pacing": {k: pacing[k] for k in ("model", "policy_source", "hourly_limit_assumed", "budget", "max_concurrency", "max_wait_s",
                                                   "state_shared_across_processes")}}

    MAX_PROMPT_CHARS = 120_000

    @staticmethod
    def _retry_after(error: HttpError) -> float | None:
        value = (error.headers or {}).get("retry-after")
        try:
            return float(value) if value is not None else None
        except ValueError:
            return None

    def structured(self, role: str, prompt: str, schema: dict, stage: str) -> ModelResult:
        if len(prompt) > self.MAX_PROMPT_CHARS:
            raise ModelError(f"prompt of {len(prompt)} chars exceeds the {self.MAX_PROMPT_CHARS}-char input bound")
        model, effort = self.resolve(role)
        payload = {"model": model, "prompt": prompt, "output_schema": schema,
                   "timeout_s": self.timeout_s, "deadline_s": self.deadline_s}
        if effort:
            payload["effort"] = effort
        self.adopt_gateway_policy()
        for attempt in range(1, MAX_429_RETRIES + 2):
            try:
                slot = self.governor.acquire(self.notify)
            except PacingError as error:
                raise ModelError(f"codex gateway hourly budget exhausted: {error}", rate_limited=True) from None
            started = utcnow()
            t0 = time.monotonic()
            call = ModelCall(provider=self.name, role=role, stage=stage, requested_model=model,
                             requested_effort=effort, returned_model=None, returned_effort=None,
                             started_at_utc=started, elapsed_ms=0, gateway_duration_ms=None,
                             prompt_chars=len(prompt), tokens_in=None, tokens_out=None, tokens_cached=None,
                             usage_raw={}, cost_usd=None, cost_note="ChatGPT allowance via Codex gateway; not USD",
                             ok=False, pacing_wait_ms=int(slot["waited_s"] * 1000) or None, attempt=attempt)
            try:
                _, body, _ = request_json("POST", self.base + "/run", self._headers(), payload,
                                          timeout=self.deadline_s + 90)
            except TransportError as error:
                call.elapsed_ms = int((time.monotonic() - t0) * 1000)
                call.error = self._public(f"transport: {error}")
                self.ledger.add_call(call)
                raise ModelError(self._public(f"inference outcome uncertain ({error}); not retried"), uncertain=True) from None
            except HttpError as error:
                call.elapsed_ms = int((time.monotonic() - t0) * 1000)
                call.error = self._public(str(error))
                self.ledger.add_call(call)
                if error.status == 429:
                    # a definite rejection: nothing executed and no allowance was consumed upstream, so the same request may
                    # be sent again once the key's budget reopens; the rejected attempt stays in the ledger
                    until = self.governor.record_rejection(self._retry_after(error))
                    if self.notify:
                        self.notify(self._public(f"pacing: the gateway rejected the request ({str(error)[:120]}); blocked for about "
                                                 f"{max(0, until - time.time()):.0f} s, attempt {attempt} of {MAX_429_RETRIES + 1}"))
                    if attempt <= MAX_429_RETRIES:
                        continue
                    raise ModelError(self._public(f"{error} (after {attempt} attempts; bounded wait exhausted)"), rate_limited=True) from None
                raise ModelError(self._public(str(error))) from None
            finally:
                self.governor.release()
            break
        call.elapsed_ms = int((time.monotonic() - t0) * 1000)
        body = body or {}
        call.returned_model = body.get("model")
        call.returned_effort = body.get("effort")
        call.gateway_duration_ms = body.get("duration_ms")
        call.usage_raw = body.get("usage") or {}
        call.tokens_in, call.tokens_out, call.tokens_cached = extract_usage(call.usage_raw)
        parsed = body.get("json")
        text = body.get("output")
        if parsed is None and isinstance(text, str):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
        problem = "no JSON output" if parsed is None else validate_json(parsed, schema)
        if problem:
            call.malformed_output = True
            call.error = f"schema violation: {problem}"
            self.ledger.add_call(call)
            raise ModelError(f"model output violated the schema: {problem}")
        call.ok = True
        self.ledger.add_call(call)
        return ModelResult(json=parsed, text=text, call=call)
