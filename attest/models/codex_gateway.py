"""Development provider: the self-hosted Codex gateway (POST /v1/run with output_schema).

No native tool calls, no streaming. Allowance usage is recorded in tokens; it is not a Nebius dollar cost.

Pacing (17 Oct 2026): every request takes a slot from the process-wide RateGovernor of its key (attest/models/pacing.py), so
all roles and all worker threads share one hourly budget and at most a couple of requests are in flight. A definite
rejection (HTTP 429, nothing executed) is recorded as a failed call, blocks the key, and the request is retried after a
bounded wait; a transport-uncertain failure is never retried. When the bounded wait is exceeded the call fails visibly with
ModelError(rate_limited=True); nothing here ever selects another provider.

Transport (revision 8, 19 Oct 2026): a request whose connection, proxy tunnel or TLS handshake failed before any byte of it was
written never reached the gateway, so it is sent again, at most NOT_SENT_RETRIES times after a short wait; each attempt is its own
failed call record (`request_sent` false). Reads (status, catalog) have no side effect and are retried on any transport failure.
A request whose bytes were written stays uncertain and is never sent again: the run stops for reconciliation.

Answer classes (revision 9, 20 Oct 2026): an HTTP 4xx answer to a run is a definite rejection (nothing ran) and fails the call; an
HTTP 5xx answer is uncertain like a lost answer, because the gateway's proxy answers 502 or 504 when the backend is slow or drops the
connection after the request was forwarded, and the backend may still have run it: the call is recorded with its status and phase,
the run is halted (`Ledger.halt`) and nothing is sent again. Every call takes a zero-USD pending record before it is sent (a
reservation journaled durably and read back; when that fails nothing is sent and the run halts) and is admitted by the ledger
immediately before each attempt, so nothing leaves after the run has stopped. Reads (status, catalog) are retried, bounded, on a
transport failure or an answer that asks for it (408, 429, 5xx). The policy refresh window uses the governor's clock.

Malformed answers (revision 10, 20 Oct 2026): an answer to a run that cannot be read (not UTF-8, not JSON, not an object, or an object
without `output`/`json` or with fields of the wrong type; `run_answer_problem`) is recorded as a call whose outcome is uncertain (the
gateway answered, so the request ran, and what it produced cannot be read), with its status and the answer's `id` when one could be
read, and the run halts at once: no repair request, nothing further. A malformed answer to a read halts the run as well (kind
`malformed_response`): the catalog decides which model answers, so the run does not go on without it, and an unreadable status leaves
the conservative pacing in force and stops the run before its next request. Malformed answers are never retried.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from ..http import (NOT_SENT_BACKOFF_S, NOT_SENT_RETRIES, READ_BACKOFF_S, READ_RETRIES, HttpError, MalformedResponse, TransportError, backoff,
                    is_number, kind_of, post_outcome, read_retryable, request_json, retry_after_s, safe_text, unreadable_text)
from ..ledger import Ledger, LedgerError, ModelCall, RunHalted, utcnow
from ..secrets import config_value
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


def run_answer_problem(body) -> str | None:
    """Why a 2xx answer to POST /v1/run cannot be read, or None (revision 10). The recorded answers carry `id`, `model`, `effort`,
    `duration_ms`, `usage`, `output` (the text) and `json` (the parsed structured output); at least one of the last two must be there."""
    if not isinstance(body, dict):
        return f"the answer is {kind_of(body)}, not an object"
    if "output" not in body and "json" not in body:
        return "the answer carries neither output nor json"
    for key in ("output", "id", "model", "effort"):
        if body.get(key) is not None and not isinstance(body[key], str):
            return f"the answer's {key} is {kind_of(body[key])}, not a string"
    if body.get("duration_ms") is not None and not is_number(body["duration_ms"]):
        return f"the answer's duration_ms is {kind_of(body['duration_ms'])}, not a number"
    if body.get("usage") is not None and not isinstance(body["usage"], dict):
        return f"the answer's usage is {kind_of(body['usage'])}, not an object"
    return None


def catalog_problem(body) -> str | None:
    """Why a model catalog answer (GET /v1/models) cannot be read, or None (revision 10)."""
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        return "the catalog is not an object with a data array"
    for item in body["data"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            return "a catalog entry is not an object with a string id"
        efforts = item.get("supported_reasoning_efforts")
        if efforts is not None and (not isinstance(efforts, list) or any(not isinstance(e, str) for e in efforts)):
            return "a catalog entry's supported_reasoning_efforts is not a list of strings"
    return None


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

    def __init__(self, api_key: str, ledger: Ledger, base_url: str | None = None,
                 roles: dict | None = None, timeout_s: int = 300, deadline_s: int = 420, governor: RateGovernor | None = None,
                 notify=None):
        self._key = api_key
        # The gateway is the team's private service: its URL comes from ATTEST_CODEX_BASE_URL or the private config, never
        # from this file, so the public repository and the deployed tree carry no host name.
        base = base_url or config_value("CODEX_BASE_URL")
        if not base:
            raise ModelError("the development gateway URL is not configured (set ATTEST_CODEX_BASE_URL); the development profile is for the project team")
        self.base = base.rstrip("/")
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
        if getattr(self.ledger, "halted", None):
            return  # the run has stopped: nothing is sent, not even a read
        checked = self.governor.policy_checked_at
        now = self.governor._time()  # the clock that stamped policy_checked_at (a test's fake clock included)
        if not force and checked is not None and now - checked < self.POLICY_REFRESH_S:
            return
        try:
            self.governor.configure_from_status(self.status(), source="gateway status")
        except (HttpError, TransportError, ModelError) as error:
            # an unreadable status keeps the conservative default; a malformed one has also halted the run (`_read`), so the run's next
            # request is refused (describe() calls this at pipeline start and must not raise)
            self.governor.policy_checked_at = self.governor._time()
            self.governor.policy_source = f"status unreadable ({type(error).__name__}); keeping {self.governor.policy_source}"

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def _sleep(self, seconds: float) -> None:
        self.governor._sleep(seconds)  # the governor's clock, so a test's fake clock covers the transport waits too

    def _admit(self, stage: str) -> None:
        """The ledger's admission right before a request leaves; a stopped run refuses it (ModelError with `halted`)."""
        try:
            self.ledger.admit("inference", stage)
        except RunHalted as halted:
            raise ModelError(self._public(str(halted)), halted=True) from None

    def _malformed_read(self, path: str, problem: str, status: int | None = 200) -> ModelError:
        """A read answered outside its documented shape (revision 10): nothing ran, but the run stops (kind `malformed_response`)."""
        self.ledger.halt("malformed_response", f"the development gateway's answer to GET {path} could not be read ({problem}); nothing further is sent",
                         stage=f"read {path}", operation={"service": "inference", "provider": self.name, "read": path, "http_status": status})
        return ModelError(self._public(f"the development gateway's answer to GET {path} could not be read ({problem}); the run stops"), halted=True,
                          malformed=True, http_status=status)

    def _read(self, path: str) -> dict:
        """A GET (status, catalog): it has no side effect, so a transport failure or an answer that asks for a retry (408, 429, 5xx) is
        retried, bounded; the last failure is raised. A malformed answer is not retried and halts the run (revision 10). Each attempt is
        admitted by the ledger first."""
        for retry in range(READ_RETRIES + 1):
            self._admit(f"read {path}")
            try:
                _, body, _ = request_json("GET", self.base + path, self._headers(), timeout=30)
                return body
            except MalformedResponse as error:
                raise self._malformed_read(path, error.problem, error.status) from None
            except (TransportError, HttpError) as error:
                if not read_retryable(error) or retry == READ_RETRIES:
                    raise
                self._sleep(retry_after_s(error) or backoff(READ_BACKOFF_S, retry))
        return {}

    def status(self) -> dict:
        return self._read("/status")

    def catalog(self) -> dict:
        if self._catalog is None:
            try:
                body = self._read("/models")
            except (HttpError, TransportError) as error:
                raise ModelError(self._public(f"the gateway's model catalog could not be read ({error})")) from None
            problem = catalog_problem(body)
            if problem:
                raise self._malformed_read("/models", problem)
            self._catalog = {item["id"]: item.get("supported_reasoning_efforts") or [] for item in body["data"]}
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
                "retry_policy": (f"HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, "
                                 f"proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most {NOT_SENT_RETRIES} "
                                 f"times after {'/'.join(f'{w:g}' for w in NOT_SENT_BACKOFF_S)} s, each attempt recorded; transport-uncertain "
                                 "failures (the request was written) never retried"),
                "answer_policy": ("HTTP 4xx: a definite rejection, the call fails; HTTP 5xx or a failure after the request was written: uncertain, "
                                  "recorded with its status and phase, never sent again, and the run stops for reconciliation"),
                "journal_policy": "every call takes a zero-USD pending record, journaled durably and read back, before it is sent",
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
        if getattr(self.ledger, "halted", None):
            raise ModelError(self._public(str(RunHalted(self.ledger.halted))), halted=True)
        model, effort = self.resolve(role)
        payload = {"model": model, "prompt": prompt, "output_schema": schema,
                   "timeout_s": self.timeout_s, "deadline_s": self.deadline_s}
        if effort:
            payload["effort"] = effort
        self.adopt_gateway_policy()
        attempt, rejections, unsent, wait_s = 0, 0, 0, 0.0
        while True:
            attempt += 1
            if wait_s:
                self._sleep(wait_s)  # before a resend of a request that was never sent; no permit is held while waiting
                wait_s = 0.0
            try:
                slot = self.governor.acquire(self.notify)
            except PacingError as error:
                raise ModelError(f"codex gateway hourly budget exhausted: {error}", rate_limited=True) from None
            try:
                try:
                    # the pending record (revision 9): a zero-USD reservation, durable and read back before anything is sent
                    reservation_id = self.ledger.reserve(self.name, role, stage, model, 0.0)
                except LedgerError as error:
                    self.ledger.halt("journal_failure", f"the pending record of the {stage} call could not be journaled; the request was not sent",
                                     stage=stage, detail=str(error), operation={"service": "inference", "provider": self.name, "dispatched": False})
                    raise ModelError(f"refusing the request: the pending record of the {stage} call could not be journaled; the request was not "
                                     "sent and the run stops", halted=True) from None
                started = utcnow()
                t0 = time.monotonic()
                call = ModelCall(provider=self.name, role=role, stage=stage, requested_model=model,
                                 requested_effort=effort, returned_model=None, returned_effort=None,
                                 started_at_utc=started, elapsed_ms=0, gateway_duration_ms=None,
                                 prompt_chars=len(prompt), tokens_in=None, tokens_out=None, tokens_cached=None,
                                 usage_raw={}, cost_usd=None, cost_note="ChatGPT allowance via Codex gateway; not USD",
                                 ok=False, pacing_wait_ms=int(slot["waited_s"] * 1000) or None, attempt=attempt)
                try:
                    self.ledger.admit("inference", stage)
                except RunHalted as halted:
                    call.request_sent, call.outcome = False, "refused"
                    call.error = "not sent: the run had stopped for reconciliation"
                    self.ledger.add_call(call, reservation_id)
                    raise ModelError(self._public(str(halted)), halted=True) from None
                try:
                    _, body, _ = request_json("POST", self.base + "/run", self._headers(), payload, timeout=self.deadline_s + 90)
                    problem = run_answer_problem(body)
                    if problem:
                        raise MalformedResponse(problem, status=200, known={"answer_id": body.get("id") if isinstance(body, dict) else None})
                except MalformedResponse as error:
                    # the gateway answered, so the request ran, and its answer cannot be read (revision 10): the call's outcome is uncertain,
                    # it is never sent again (not even as a repair request) and the run stops at once
                    call.elapsed_ms = int((time.monotonic() - t0) * 1000)
                    call.request_sent, call.transport_phase, call.http_status = True, "response", error.status
                    call.error = self.ledger.public_error(f"{stage}-malformed", error)
                    call.outcome = "uncertain"
                    self.ledger.add_call(call, reservation_id)
                    answer_id = error.known.get("answer_id")
                    self.ledger.halt("uncertain_operation", f"the development gateway's answer to the {stage} call could not be read ({error.problem}); it ran "
                                                            "upstream, so it was not sent again", stage=stage,
                                     operation={"service": "inference", "provider": self.name, "started_at_utc": started, "http_status": error.status,
                                                "answer_id": answer_id}, detail=self._public(f"{error}; body sha256 {error.body_sha256}; starts {error.excerpt!r}"))
                    raise ModelError(self._public(f"inference answer unreadable ({error.problem}); not retried"), uncertain=True, malformed=True,
                                     http_status=error.status) from None
                except TransportError as error:
                    call.elapsed_ms = int((time.monotonic() - t0) * 1000)
                    call.request_sent, call.transport_phase, call.http_status = error.request_sent, error.phase, getattr(error, "status", None)
                    call.error = self.ledger.public_error(f"{stage}-transport", error)
                    call.outcome = post_outcome(error)
                    self.ledger.add_call(call, reservation_id)
                    if call.outcome == "not_sent":
                        # nothing reached the gateway (the failure came before any byte of the request was written), so sending it
                        # again cannot run anything twice; bounded, and every attempt keeps its own record
                        if unsent < NOT_SENT_RETRIES:
                            wait_s = backoff(NOT_SENT_BACKOFF_S, unsent)
                            unsent += 1
                            if self.notify:
                                self.notify(f"transport: the request was never sent ({error.phase} failed); sending it again in {wait_s:.0f} s "
                                            f"(attempt {attempt + 1})")
                            continue
                        raise ModelError(self._public(f"the development gateway could not be reached: {attempt} attempts, none got as far as "
                                                      f"sending the request ({error})"), unreachable=True) from None
                    self.ledger.halt("uncertain_operation", f"the outcome of the {stage} call to the development gateway is uncertain (failure in the "
                                                            f"{error.phase} phase after the request was written); it was not sent again", stage=stage,
                                     operation={"service": "inference", "provider": self.name, "started_at_utc": started}, detail=self._public(str(error)))
                    raise ModelError(self._public(f"inference outcome uncertain ({error}); not retried"), uncertain=True,
                                     http_status=getattr(error, "status", None)) from None
                except HttpError as error:
                    call.elapsed_ms = int((time.monotonic() - t0) * 1000)
                    call.request_sent, call.transport_phase, call.http_status = True, "response", error.status
                    call.error = self.ledger.public_error(f"{stage}-http", error)
                    call.outcome = post_outcome(error)
                    self.ledger.add_call(call, reservation_id)
                    if error.status == 429:
                        # a definite rejection: nothing executed and no allowance was consumed upstream, so the same request may
                        # be sent again once the key's budget reopens; the rejected attempt stays in the ledger
                        rejections += 1
                        until = self.governor.record_rejection(self._retry_after(error))
                        if self.notify:
                            self.notify(self._public(f"pacing: the gateway rejected the request ({str(error)[:120]}); blocked for about "
                                                     f"{max(0, until - time.time()):.0f} s, rejection {rejections} of {MAX_429_RETRIES + 1}"))
                        if rejections <= MAX_429_RETRIES:
                            continue
                        raise ModelError(self._public(f"{error} (after {attempt} attempts; bounded wait exhausted)"), rate_limited=True,
                                         http_status=429) from None
                    if call.outcome == "rejected":
                        raise ModelError(self._public(str(error)), http_status=error.status) from None
                    # an HTTP 5xx: the gateway's proxy answers 502/504 when the backend is slow or drops the connection after the request was
                    # forwarded, so the backend may have run it: uncertain, never sent again, and the run stops (revision 9)
                    self.ledger.halt("uncertain_operation", f"the development gateway answered HTTP {error.status} to the {stage} call; it may have "
                                                            "run upstream, so it was not sent again", stage=stage,
                                     operation={"service": "inference", "provider": self.name, "started_at_utc": started, "http_status": error.status})
                    raise ModelError(self._public(f"inference outcome uncertain (HTTP {error.status} from the gateway after the request was sent); "
                                                  "not retried"), uncertain=True, http_status=error.status) from None
            finally:
                self.governor.release()
            break
        call.elapsed_ms = int((time.monotonic() - t0) * 1000)
        call.request_sent = True
        call.outcome = "answered"
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
            except (json.JSONDecodeError, RecursionError):
                parsed = None
        # the model's output (not the gateway's envelope): text that is not valid Unicode is a schema violation like any other bad output
        problem = ("no JSON output" if parsed is None else "the output holds text that is not valid Unicode" if unreadable_text(parsed)
                   else validate_json(parsed, schema))
        if problem:
            call.malformed_output = True
            call.error = f"schema violation: {problem}"
            self.ledger.add_call(call, reservation_id)
            raise ModelError(f"model output violated the schema: {problem}")
        call.ok = True
        self.ledger.add_call(call, reservation_id)
        return ModelResult(json=parsed, text=text, call=call)
