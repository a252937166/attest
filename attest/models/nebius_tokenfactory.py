"""Submission-profile provider: NVIDIA Nemotron on Nebius Token Factory.

OpenAI-compatible chat completions with a JSON-schema response format. Cost is
computed from the public price table and capped per run. Unverified until the
native pilot runs; keep results labeled separately from Codex development runs.

Answer classes (revision 9, 20 Oct 2026): an HTTP 4xx answer is a definite rejection (nothing generated, nothing billed); an HTTP 5xx
answer may come after the generation was metered, so like a lost answer it keeps its reservation committed, is never sent again and
halts the run for reconciliation (`Ledger.halt`). A reservation that cannot be journaled and a generation that cannot be priced halt
the run the same way, and every attempt is admitted by the ledger right before it is sent, so nothing leaves after the stop.
"""

from __future__ import annotations

import json
import os
import re
import time

from ..http import NOT_SENT_BACKOFF_S, NOT_SENT_RETRIES, HttpError, TransportError, backoff, post_outcome, request_json
from ..ledger import Ledger, LedgerError, ModelCall, RunHalted, utcnow
from .base import ModelError, ModelResult, extract_usage, usage_problem, validate_json

# USD per 1M tokens (input, output), read from tokenfactory.nebius.com/api/public/models_info on 2026-10-14.
PRICES = {
    "nvidia/Nemotron-3-Ultra-550b-a55b": (1.00, 3.00),
    "nvidia/nemotron-3-super-120b-a12b": (0.30, 0.90),
    "nvidia/Nemotron-3_5-Lightning": (0.06, 0.24),
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B": (0.06, 0.24),
}
DEFAULT_ROLES = {
    "spec": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "seal": "nvidia/nemotron-3-super-120b-a12b",
    "implement": "nvidia/nemotron-3-super-120b-a12b",
    "break": "nvidia/nemotron-3-super-120b-a12b",
    "audit": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "arbitrate": "nvidia/Nemotron-3-Ultra-550b-a55b",
    "summary": "nvidia/Nemotron-3_5-Lightning",
}
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def roles_from_env(default: dict) -> dict:
    roles = dict(default)
    for item in filter(None, (s.strip() for s in os.environ.get("ATTEST_NEBIUS_ROLES", "").split(","))):
        role, _, model = item.partition("=")
        roles[role.strip()] = model.strip()
    return roles


class NebiusTokenFactory:
    name = "nebius_tokenfactory"

    def __init__(self, api_key: str, ledger: Ledger, base_url: str = "https://api.tokenfactory.nebius.com/v1",
                 roles: dict | None = None, usd_cap: float = 0.50, thinking_roles: tuple[str, ...] = ("spec", "audit", "arbitrate"),
                 max_tokens: int = 16000, timeout: int = 300, send_thinking_flag: bool | None = None,
                 max_calls: int | None = None, reasoning_effort: dict | None = None):
        self._key = api_key
        self.base = base_url.rstrip("/")
        self.ledger = ledger
        self.roles = roles_from_env(roles or DEFAULT_ROLES)
        self.usd_cap = usd_cap
        # Hard cap on the number of calls one run may make (None = only the USD cap). Every entry point that builds this provider for a
        # paid run passes the cap it promises (the harness, the CLI and the console worker all default to 22, review finding R5-05);
        # the call that would exceed it is refused before dispatch with a definite ModelError naming the cap.
        self.max_calls = max_calls
        self.thinking_roles = thinking_roles
        self.max_tokens = max_tokens
        self.timeout = timeout
        # Reasoning is bounded explicitly since 17 Oct 2026: the smoke test of the frozen suite saw Nemotron Super spend all
        # 16,000 completion tokens on reasoning with no visible output (twice), where the same prompts had worked the day
        # before. Live probes (reasoning-probe*.json in the evaluation folder) showed two honoured controls: `reasoning_effort`
        # bounds the reasoning (the real sealing prompt: 42 tokens at low, 4,716 at medium, valid JSON both times) and
        # `chat_template_kwargs.enable_thinking=false` removes it, which cost the implementer its quality in the second smoke
        # test. The Super and Lightning roles therefore run with a bounded effort (default medium) and the Ultra roles with
        # the model default that has been working. ATTEST_NEBIUS_THINKING_FLAG=1 additionally sends the enable_thinking flag
        # (on for thinking_roles, off otherwise). Everything is recorded in sampling provenance.
        if send_thinking_flag is None:
            send_thinking_flag = os.environ.get("ATTEST_NEBIUS_THINKING_FLAG", "0") == "1"
        self.send_thinking_flag = send_thinking_flag
        default_effort = os.environ.get("ATTEST_NEBIUS_REASONING_EFFORT", "medium")
        # seal and break at low effort: on the real sealing prompt, medium still ran away once (16,000 reasoning tokens in the
        # fourth smoke test, rescued by the repair retry) while low used 42; the implementer keeps medium (its calls stayed
        # well under the cap and it benefits from reasoning)
        self.reasoning_effort = reasoning_effort if reasoning_effort is not None else {
            "seal": "low", "implement": default_effort, "break": "low", "summary": "low"}
        # Audit findings AC-03 and AC-04 (19 Oct 2026): once this instance could not journal a reservation, or settled a generated
        # answer without usable metering, it refuses every further paid request (the reason is kept here). Nothing is dispatched
        # blind, and the per-run cap never binds on a guess; a human reconciles the run against the provider's billing. Review
        # finding R5-01: a reservation is journaled only after the ledger repaired any cut journal tail and read the new line back
        # (attest/ledger.py); when that fails the LedgerError below halts this instance the same way.
        self.halted: str | None = None
        self._sleep = time.sleep  # waits before resending a request that was never sent (tests replace it)

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def _refuse_if_halted(self) -> None:
        if self.halted:
            raise ModelError(f"refusing the request: {self.halted}", halted=True)
        run_halt = getattr(self.ledger, "halted", None)
        if run_halt:
            raise ModelError(f"refusing the request: {RunHalted(run_halt)}", halted=True)

    def _halt(self, kind: str, reason: str, stage: str, public: str | None = None, **operation) -> None:
        """Stop this instance's paid calls and the whole run (revision 9): `reason` (it may carry raw error text) is kept on the
        instance and in the private log line; the ledger's halt record, which the bundle carries, gets `public` (or the reason when it
        is already public)."""
        self.halted = self.halted or reason
        if hasattr(self.ledger, "halt"):
            self.ledger.halt(kind, public or reason, stage=stage, detail=reason if public else None,
                             operation={"service": "inference", "provider": self.name, **operation})

    def describe(self) -> dict:
        """The effective configuration of this instance (recorded as the bundle's `profile.provider`; the evaluation harness freezes
        its stable keys as the registered provider profile) plus its current state: `max_calls` is the cap that governs the run,
        `halted` the reason paid calls stopped, `journal_degraded`/`journal_failures`/`journal_repairs` the state of the ledger journal."""
        return {"provider": self.name, "base_url": self.base, "roles": dict(self.roles), "usd_cap": self.usd_cap, "max_calls": self.max_calls, "reasoning_effort": dict(self.reasoning_effort),
                "temperature": self.TEMPERATURE,
                "thinking_roles": list(self.thinking_roles) if self.send_thinking_flag else [],
                "send_thinking_flag": self.send_thinking_flag, "response_format": "json_schema wrapper {name, schema, strict} (raw schema is rejected with 422 despite the docs)",
                "schema_in_prompt": True, "auto_retry": False, "pre_request_reservation": True,
                "transport_retry_policy": (f"a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it "
                                           f"was written) closes its reservation at a known $0 and is sent again at most {NOT_SENT_RETRIES} times after "
                                           f"{'/'.join(f'{w:g}' for w in NOT_SENT_BACKOFF_S)} s, each attempt under a new reservation, each recorded and "
                                           "counted against the call cap; a request whose bytes were written is never sent again (its reservation stays committed)"),
                "reservation_policy": "the USD reservation is journaled durably (fsync) and read back before dispatch, after any cut journal tail has been "
                                      "terminated with a journal_repair record; if it cannot be, the request is not sent and the run stops paid calls",
                "metering_policy": "an HTTP 200 whose usage cannot price the generation (missing, empty, partial or malformed counters) keeps its "
                                   "reservation unsettled and stops further paid calls of the run pending reconciliation; explicit zero counters settle as 0",
                "answer_policy": "HTTP 4xx: a definite rejection at a known $0; HTTP 5xx or a failure after the request was written: uncertain, the "
                                 "reservation stays committed, nothing is sent again and the run stops for reconciliation",
                "call_cap_policy": (f"at most {self.max_calls} model calls per run (failed calls and retries count); the call that would exceed it is refused "
                                    f"before dispatch" if self.max_calls is not None else "no per-run call cap; only the USD cap binds"),
                "halted": self.halted,
                "journal_degraded": getattr(self.ledger, "journal_degraded", None),
                "journal_failures": len(getattr(self.ledger, "journal_failures", None) or []),
                "journal_repairs": len(getattr(self.ledger, "journal_repairs", None) or []),
                "max_prompt_chars": self.MAX_PROMPT_CHARS, "max_tokens": self.max_tokens}

    CHARS_PER_TOKEN = 3.0  # conservative for English plus code; real ratio is usually higher
    MAX_PROMPT_CHARS = 120_000
    TEMPERATURE = 0.2

    def calls_made(self) -> int:
        return sum(1 for c in self.ledger.model_calls if c.provider == self.name)

    def spent_usd(self) -> float:
        """Committed USD of this provider within the run: known costs, the reservation of every call whose outcome is unknown,
        and every reservation still open (a request in flight). The per-run cap binds on this conservative figure."""
        known = sum(c.cost_usd if c.cost_usd is not None else (c.reserved_usd or 0.0) for c in self.ledger.model_calls if c.provider == self.name)
        open_reserved = sum(r.get("reserved_usd") or 0.0 for r in self.ledger.open_reservations if r.get("provider") == self.name)
        return known + open_reserved

    def reserve_usd(self, model: str, prompt_chars: int) -> float:
        """Upper-bound cost of one call: every prompt char at 1/3 token plus the full max_tokens output."""
        price_in, price_out = PRICES[model]
        est_in = prompt_chars / self.CHARS_PER_TOKEN + 1_000
        return est_in / 1e6 * price_in + self.max_tokens / 1e6 * price_out

    def structured(self, role: str, prompt: str, schema: dict, stage: str) -> ModelResult:
        self._refuse_if_halted()
        model = self.roles.get(role) or self.roles["implement"]
        if model not in PRICES:
            raise ModelError(f"no price entry for {model!r}; refusing to spend without accounting")
        if len(prompt) > self.MAX_PROMPT_CHARS:
            raise ModelError(f"prompt of {len(prompt)} chars exceeds the {self.MAX_PROMPT_CHARS}-char input bound")
        reservation = self.reserve_usd(model, len(prompt))
        spent = self.spent_usd()
        if spent + reservation > self.usd_cap:
            raise ModelError(f"per-run USD cap {self.usd_cap:.2f} would be exceeded: spent {spent:.4f} + reserved {reservation:.4f}; aborting before the call")
        if self.max_calls is not None and self.calls_made() >= self.max_calls:
            # a definite refusal before dispatch: the cap counts every call record of this run (failed calls and retries included)
            raise ModelError(f"per-run call cap {self.max_calls} reached ({self.calls_made()} calls recorded in this run); the request was not sent")
        thinking = self.send_thinking_flag and role in self.thinking_roles
        schema_text = json.dumps(schema, separators=(",", ":"))
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a careful software engineering assistant. "
                                              "Reply with a single JSON object that matches the provided schema and nothing else."},
                {"role": "user", "content": prompt + "\n\nRespond with one JSON object that validates against this JSON Schema:\n" + schema_text},
            ],
            # Live API (2026-10-15) returns 422 without json_schema.name; it expects the OpenAI-style wrapper,
            # unlike the raw-schema example in the Token Factory docs. Recorded as a documentation feedback item.
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": re.sub(r"[^A-Za-z0-9_]", "_", stage)[:60], "schema": schema, "strict": True}},
            "temperature": self.TEMPERATURE,
            "max_tokens": self.max_tokens,
        }
        if self.send_thinking_flag:
            payload["chat_template_kwargs"] = {"enable_thinking": thinking}
        effort = self.reasoning_effort.get(role)
        if effort:
            payload["reasoning_effort"] = effort
        return self._send(role, prompt, schema, stage, model, payload, reservation, attempt=1)

    def _send(self, role, prompt, schema, stage, model, payload, reservation, attempt: int, unsent: int = 0) -> ModelResult:
        """One request; a `finish_reason=length` answer with no visible content (the model spent its whole completion budget on
        reasoning) is a definite failure and is retried once at low reasoning effort, both attempts recorded. The reservation
        is journaled before the request leaves and closed by the call record, so an interrupted process leaves the bound behind."""
        self._refuse_if_halted()
        try:
            reservation_id = self.ledger.reserve(self.name, role, stage if attempt == 1 else f"{stage}-lowretry", model, reservation)
        except LedgerError as error:
            # a definite refusal (nothing left the process): without a durable reservation the request is not sent, and this
            # instance sends nothing further, so no call of the run can ever be billed without a record that survives the process
            self._halt("journal_failure", f"the USD reservation for {stage} could not be journaled ({error}); the request was not sent, and this provider "
                                          f"instance accepts no further paid requests because nothing may be dispatched without a durable reservation",
                       stage, public=f"the USD reservation for {stage} could not be journaled; the request was not sent", dispatched=False)
            raise ModelError(self.halted, halted=True) from None
        started = utcnow()
        t0 = time.monotonic()
        flags = payload.get("chat_template_kwargs") or {}
        effort_label = payload.get("reasoning_effort") or ("thinking" if flags.get("enable_thinking") else "no-thinking" if flags else "default")
        call = ModelCall(provider=self.name, role=role, stage=stage if attempt == 1 else f"{stage}-lowretry", requested_model=model,
                         requested_effort=effort_label, returned_model=None,
                         returned_effort=None, started_at_utc=started, elapsed_ms=0, gateway_duration_ms=None,
                         prompt_chars=len(prompt), tokens_in=None, tokens_out=None, tokens_cached=None,
                         usage_raw={}, cost_usd=None, cost_note="USD from public Token Factory price table", ok=False,
                         reserved_usd=round(reservation, 6), attempt=unsent + 1)
        try:
            self.ledger.admit("inference", stage)  # immediately before the request: a stopped run sends nothing (revision 9)
        except RunHalted as halted:
            call.request_sent, call.outcome, call.cost_usd, call.settlement = False, "refused", 0.0, "known"
            call.cost_note = "not sent: the run had stopped for reconciliation; nothing was billed"
            self.ledger.add_call(call, reservation_id)
            raise ModelError(f"refusing the request: {halted}", halted=True) from None
        try:
            _, body, _ = request_json("POST", self.base + "/chat/completions", self._headers(), payload,
                                      timeout=self.timeout)
        except TransportError as error:
            call.elapsed_ms = int((time.monotonic() - t0) * 1000)
            call.request_sent, call.transport_phase, call.http_status = error.request_sent, error.phase, getattr(error, "status", None)
            call.error = self.ledger.public_error(f"{stage}-transport", error)
            call.outcome = post_outcome(error)
            if not error.request_sent:
                # no byte of the request was written (the connection, the proxy tunnel or the TLS handshake failed first), so the
                # provider cannot have received it: nothing was generated or billed, the reservation closes at a known zero, and the
                # request may be sent again under a new reservation while the per-run caps allow it
                call.cost_usd = 0.0
                call.settlement = "known"
                call.cost_note = "not sent: the connection failed before any byte of the request was written; nothing was billed"
                self.ledger.add_call(call, reservation_id)
                if (unsent < NOT_SENT_RETRIES and self.spent_usd() + reservation <= self.usd_cap
                        and (self.max_calls is None or self.calls_made() < self.max_calls)):
                    self._sleep(backoff(NOT_SENT_BACKOFF_S, unsent))
                    return self._send(role, prompt, schema, stage, model, payload, reservation, attempt, unsent=unsent + 1)
                raise ModelError(f"the model provider could not be reached: {unsent + 1} attempt(s), none got as far as sending the request "
                                 f"({error})", unreachable=True) from None
            call.settlement = "unsettled"  # the request may have been billed: the reservation stays committed until reconciled
            self.ledger.add_call(call, reservation_id)
            self._halt("uncertain_operation", f"the outcome of the {stage} call is uncertain (failure in the {error.phase} phase after the request "
                                              "was written); its reservation stays committed and it was not sent again", stage,
                       started_at_utc=started, reserved_usd=round(reservation, 6))
            raise ModelError(f"inference outcome uncertain ({error}); not retried", uncertain=True, http_status=getattr(error, "status", None)) from None
        except HttpError as error:
            call.elapsed_ms = int((time.monotonic() - t0) * 1000)
            call.request_sent, call.transport_phase, call.http_status = True, "response", error.status
            call.error = self.ledger.public_error(f"{stage}-http", error)
            call.outcome = post_outcome(error)
            if call.outcome == "rejected":
                call.cost_usd = 0.0  # the provider refused the request (quota, schema, auth): nothing was generated, nothing is billed
                call.settlement = "known"
                self.ledger.add_call(call, reservation_id)
                raise ModelError(str(error), rate_limited=error.status == 429, http_status=error.status) from None
            call.settlement = "unsettled"  # a server-side failure may or may not have been metered: the reservation stays committed
            self.ledger.add_call(call, reservation_id)
            self._halt("uncertain_operation", f"the provider answered HTTP {error.status} to the {stage} call after the request was sent; it may "
                                              "have been metered, so its reservation stays committed and it was not sent again", stage,
                       started_at_utc=started, reserved_usd=round(reservation, 6), http_status=error.status)
            raise ModelError(f"inference outcome uncertain (HTTP {error.status} after the request was sent); not retried", uncertain=True,
                             http_status=error.status) from None
        call.elapsed_ms = int((time.monotonic() - t0) * 1000)
        call.request_sent = True
        call.outcome = "answered"
        body = body or {}
        call.returned_model = body.get("model")
        usage = body.get("usage")
        call.usage_raw = usage if isinstance(usage, dict) else ({} if usage is None else {"malformed_usage": repr(usage)[:200]})
        call.tokens_in, call.tokens_out, call.tokens_cached = extract_usage(usage)
        metering = usage_problem(usage, call.tokens_in, call.tokens_out)
        if metering is None:
            price_in, price_out = PRICES[model]
            call.cost_usd = round(call.tokens_in / 1e6 * price_in + call.tokens_out / 1e6 * price_out, 6)
        else:
            # the provider generated an answer, so the call was not free; without usable counters its price is unknown and the
            # reservation stays committed (unsettled). No further paid call of this run: the per-run cap must not bind on guesses.
            # The answer itself is still returned below (it was generated and is validated like any other).
            call.cost_usd = None
            call.settlement = "unsettled"
            call.cost_note = (f"metering failed: {metering}; the reservation (${reservation:.6f}) stays committed pending reconciliation "
                              f"against the provider's billing")
            self._halt("metering_unknown", f"metering failed on {call.stage} ({metering}); paid calls of this run stop pending reconciliation",
                       call.stage, started_at_utc=started, reserved_usd=round(reservation, 6))
        choices = body.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        text = message.get("content") or ""
        cleaned = THINK_RE.sub("", text).strip()
        parsed = None
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    parsed = None
        problem = "no JSON output" if parsed is None else validate_json(parsed, schema)
        if problem:
            call.malformed_output = True
            head = (text or "").strip().replace("\n", " ")[:240]
            finish = (choices[0].get("finish_reason") if choices else None)
            call.error = f"schema violation: {problem}; finish_reason={finish}"  # the content head stays out of the record (R5-04)
            self.ledger.add_call(call, reservation_id)
            if finish == "length" and not (head or "").strip() and attempt == 1 and not self.halted:
                # the model spent the whole completion budget on reasoning: a definite failure (nothing to replay), retried once at
                # low effort if the per-run cap still allows the reservation (and the run is not halted on a metering failure)
                if self.spent_usd() + reservation <= self.usd_cap and (self.max_calls is None or self.calls_made() < self.max_calls):
                    low = dict(payload, reasoning_effort="low")
                    return self._send(role, prompt, schema, stage, model, low, reservation, attempt=2)
            raise ModelError(f"model output violated the schema: {problem} (finish_reason={finish}, content head: {head[:120]!r})")
        call.ok = True
        self.ledger.add_call(call, reservation_id)
        return ModelResult(json=parsed, text=text, call=call)
