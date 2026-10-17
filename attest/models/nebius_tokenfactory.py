"""Submission-profile provider: NVIDIA Nemotron on Nebius Token Factory.

OpenAI-compatible chat completions with a JSON-schema response format. Cost is
computed from the public price table and capped per run. Unverified until the
native pilot runs; keep results labeled separately from Codex development runs.
"""

from __future__ import annotations

import json
import os
import re
import time

from ..http import HttpError, TransportError, request_json
from ..ledger import Ledger, ModelCall, utcnow
from .base import ModelError, ModelResult, extract_usage, validate_json

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
        self.max_calls = max_calls  # optional hard cap on the number of calls one run may make (None = only the USD cap)
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
        self.reasoning_effort = reasoning_effort if reasoning_effort is not None else {
            "seal": default_effort, "implement": default_effort, "break": default_effort, "summary": "low"}

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key}

    def describe(self) -> dict:
        return {"provider": self.name, "base_url": self.base, "roles": dict(self.roles), "usd_cap": self.usd_cap, "max_calls": self.max_calls, "reasoning_effort": dict(self.reasoning_effort),
                "temperature": self.TEMPERATURE,
                "thinking_roles": list(self.thinking_roles) if self.send_thinking_flag else [],
                "send_thinking_flag": self.send_thinking_flag, "response_format": "json_schema wrapper {name, schema, strict} (raw schema is rejected with 422 despite the docs)",
                "schema_in_prompt": True, "auto_retry": False, "pre_request_reservation": True,
                "max_prompt_chars": self.MAX_PROMPT_CHARS, "max_tokens": self.max_tokens}

    CHARS_PER_TOKEN = 3.0  # conservative for English plus code; real ratio is usually higher
    MAX_PROMPT_CHARS = 120_000
    TEMPERATURE = 0.2

    def calls_made(self) -> int:
        return sum(1 for c in self.ledger.model_calls if c.provider == self.name)

    def spent_usd(self) -> float:
        return sum(c.cost_usd or 0.0 for c in self.ledger.model_calls if c.provider == self.name)

    def reserve_usd(self, model: str, prompt_chars: int) -> float:
        """Upper-bound cost of one call: every prompt char at 1/3 token plus the full max_tokens output."""
        price_in, price_out = PRICES[model]
        est_in = prompt_chars / self.CHARS_PER_TOKEN + 1_000
        return est_in / 1e6 * price_in + self.max_tokens / 1e6 * price_out

    def structured(self, role: str, prompt: str, schema: dict, stage: str) -> ModelResult:
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
            raise ModelError(f"per-run call cap {self.max_calls} reached; aborting before the call")
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
        started = utcnow()
        t0 = time.monotonic()
        call = ModelCall(provider=self.name, role=role, stage=stage, requested_model=model,
                         requested_effort=("thinking" if thinking else "no-thinking") if self.send_thinking_flag else "default", returned_model=None,
                         returned_effort=None, started_at_utc=started, elapsed_ms=0, gateway_duration_ms=None,
                         prompt_chars=len(prompt), tokens_in=None, tokens_out=None, tokens_cached=None,
                         usage_raw={}, cost_usd=None, cost_note="USD from public Token Factory price table", ok=False,
                         reserved_usd=round(reservation, 6))
        try:
            _, body, _ = request_json("POST", self.base + "/chat/completions", self._headers(), payload,
                                      timeout=self.timeout)
        except TransportError as error:
            call.elapsed_ms = int((time.monotonic() - t0) * 1000)
            call.error = f"transport: {error}"
            self.ledger.add_call(call)
            raise ModelError(f"inference outcome uncertain ({error}); not retried", uncertain=True) from None
        except HttpError as error:
            call.elapsed_ms = int((time.monotonic() - t0) * 1000)
            call.error = str(error)
            self.ledger.add_call(call)
            raise ModelError(str(error)) from None
        call.elapsed_ms = int((time.monotonic() - t0) * 1000)
        body = body or {}
        call.returned_model = body.get("model")
        call.usage_raw = body.get("usage") or {}
        call.tokens_in, call.tokens_out, call.tokens_cached = extract_usage(call.usage_raw)
        price_in, price_out = PRICES[model]
        call.cost_usd = round((call.tokens_in or 0) / 1e6 * price_in + (call.tokens_out or 0) / 1e6 * price_out, 6)
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
            call.error = f"schema violation: {problem}; finish_reason={finish}; content head: {head!r}"
            self.ledger.add_call(call)
            raise ModelError(f"model output violated the schema: {problem} (finish_reason={finish}, content head: {head[:120]!r})")
        call.ok = True
        self.ledger.add_call(call)
        return ModelResult(json=parsed, text=text, call=call)
