"""Usage ledgers: model calls (tokens, allowance or USD) and sandbox operations."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


@dataclass
class ModelCall:
    provider: str
    role: str
    stage: str
    requested_model: str
    requested_effort: str | None
    returned_model: str | None
    returned_effort: str | None
    started_at_utc: str
    elapsed_ms: int
    gateway_duration_ms: int | None
    prompt_chars: int
    tokens_in: int | None
    tokens_out: int | None
    tokens_cached: int | None
    usage_raw: dict
    cost_usd: float | None
    cost_note: str
    ok: bool
    malformed_output: bool = False
    error: str | None = None
    # Conservative upper bound reserved for this call before it was sent; used for budgeting when the actual
    # cost is unknown (for example a transport-uncertain call whose tokens never came back).
    reserved_usd: float | None = None
    # Pacing (Codex gateway): time this call waited for the shared hourly budget before it was sent, and which attempt it
    # was (a request rejected with HTTP 429 is recorded as its own failed call; the retry after the wait is attempt 2).
    pacing_wait_ms: int | None = None
    attempt: int = 1


@dataclass
class SandboxOp:
    stage: str
    operation_uuid: str | None
    image_uuid: str
    result_image_uuid: str | None
    disposable: bool
    networking_enabled: bool
    status: str | None
    exit_code: int | None
    timed_out: bool | None
    signal: int | None
    duration_s: float | None
    raw_cost_diag: float | None
    stdout_truncated: bool | None
    started_at_utc: str
    note: str = "raw_cost_diag has no confirmed currency semantics; not a USD charge"


@dataclass
class Ledger:
    model_calls: list[ModelCall] = field(default_factory=list)
    sandbox_ops: list[SandboxOp] = field(default_factory=list)

    def add_call(self, call: ModelCall) -> None:
        self.model_calls.append(call)

    def add_op(self, op: SandboxOp) -> None:
        self.sandbox_ops.append(op)

    def totals(self) -> dict:
        tokens_in = sum(c.tokens_in or 0 for c in self.model_calls)
        tokens_out = sum(c.tokens_out or 0 for c in self.model_calls)
        tokens_cached = sum(c.tokens_cached or 0 for c in self.model_calls)
        usd = [c.cost_usd for c in self.model_calls if c.cost_usd is not None]
        # Conservative total: known cost where we have it, otherwise the reservation (uncertain calls never undercount).
        committed = sum(c.cost_usd if c.cost_usd is not None else (c.reserved_usd or 0.0) for c in self.model_calls)
        uncertain = sum(1 for c in self.model_calls if c.cost_usd is None and (c.reserved_usd or 0.0) > 0)
        by_model: dict[str, dict] = {}
        for c in self.model_calls:
            key = f"{c.provider}:{c.requested_model}"
            entry = by_model.setdefault(key, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "tokens_cached": 0,
                                               "cost_usd": 0.0 if c.cost_usd is not None else None,
                                               "elapsed_ms": 0, "failed": 0})
            entry["calls"] += 1
            entry["tokens_in"] += c.tokens_in or 0
            entry["tokens_out"] += c.tokens_out or 0
            entry["tokens_cached"] += c.tokens_cached or 0
            entry["elapsed_ms"] += c.elapsed_ms
            if c.cost_usd is not None:
                entry["cost_usd"] = (entry["cost_usd"] or 0.0) + c.cost_usd
            if not c.ok:
                entry["failed"] += 1
        return {
            "model_calls": len(self.model_calls),
            "model_calls_failed": sum(1 for c in self.model_calls if not c.ok),
            "malformed_outputs": sum(1 for c in self.model_calls if c.malformed_output),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_cached": tokens_cached,
            "model_elapsed_ms": sum(c.elapsed_ms for c in self.model_calls),
            "cost_usd": round(sum(usd), 6) if usd else None,
            "cost_usd_committed": round(committed, 6),
            "uncertain_unpriced_calls": uncertain,
            "rate_limited_calls": sum(1 for c in self.model_calls if not c.ok and "HTTP 429" in (c.error or "")),
            "pacing_wait_ms": sum(c.pacing_wait_ms or 0 for c in self.model_calls),
            "by_model": by_model,
            "sandbox_operations": len(self.sandbox_ops),
            "sandbox_duration_s": round(sum(o.duration_s or 0 for o in self.sandbox_ops), 3),
            "sandbox_retained_images": [o.result_image_uuid for o in self.sandbox_ops if o.result_image_uuid],
            "sandbox_raw_cost_diag_sum": round(sum(o.raw_cost_diag or 0 for o in self.sandbox_ops), 8),
        }

    def to_dict(self) -> dict:
        return {"model_calls": [asdict(c) for c in self.model_calls],
                "sandbox_ops": [asdict(o) for o in self.sandbox_ops],
                "totals": self.totals()}
