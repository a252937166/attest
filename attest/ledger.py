"""Usage ledgers: model calls (tokens, allowance or USD) and sandbox operations.

Persistence (19 Oct 2026): a ledger can carry a journal sink (`ledger.jsonl` in the run directory). Every reservation is
appended BEFORE the request is sent and every call record is appended as soon as it is known, so a process that dies
mid-run leaves a journal from which the known costs and the still-open reservations can be read back (`read_journal`).
`ledger.json` (the totals) is still written at the end of a run; the journal is what survives an interruption.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path


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
    # Settlement of the reservation: "known" (the provider returned usage), "unsettled" (the outcome of the request is
    # unknown, so the reservation stays committed until a human reconciles it against the provider's billing), or
    # "none" (no USD reservation, for example the development gateway's allowance).
    settlement: str = "none"


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
    # reservations taken for requests whose call record has not been written yet (in flight, or lost with the process)
    open_reservations: list[dict] = field(default_factory=list)
    sink: Path | None = field(default=None, repr=False, compare=False)
    on_change: object = field(default=None, repr=False, compare=False)  # callable(totals) after every change
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    _reservation_seq: int = field(default=0, repr=False, compare=False)

    # ------------------------------------------------------------------ journal
    def attach_sink(self, path: Path) -> None:
        """Start journaling into `path`; anything already recorded is written first so the journal is complete."""
        with self._lock:
            self.sink = Path(path)
            self.sink.parent.mkdir(parents=True, exist_ok=True)
            with self.sink.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"event": "ledger", "at_utc": utcnow(), "version": 1,
                                         "note": "append-only journal: reservations are written before a request is sent, call records as soon as "
                                                 "they are known; an open reservation without a call record is a request whose outcome was lost "
                                                 "with the process and stays committed at its bound"}) + "\n")
                for call in self.model_calls:
                    handle.write(json.dumps({"event": "call", **asdict(call)}, ensure_ascii=False) + "\n")
                for op in self.sandbox_ops:
                    handle.write(json.dumps({"event": "sandbox_op", **asdict(op)}, ensure_ascii=False) + "\n")
                for reservation in self.open_reservations:
                    handle.write(json.dumps({"event": "reserve", **reservation}) + "\n")

    def detach_sink(self) -> None:
        """Stop journaling: called when the run directory is sealed by its manifest, so operations recorded afterwards by the
        caller (for example the evaluation harness's judge) stay in memory and in the caller's own records, not in a file whose
        digest the manifest already fixed."""
        with self._lock:
            self.sink = None

    def _append(self, record: dict) -> None:
        if self.sink is None:
            return
        try:
            with self.sink.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass  # the journal is a safety net; a failing disk must not stop the run itself (the totals are still written at the end)

    def _changed(self) -> None:
        if self.on_change is not None:
            try:
                self.on_change(self.totals())
            except Exception:  # noqa: BLE001 - observers never break accounting
                pass

    # ------------------------------------------------------------------ records
    def reserve(self, provider: str, role: str, stage: str, model: str, reserved_usd: float) -> str:
        """Record a USD reservation before a request is sent. Returns its id; `add_call` closes it."""
        with self._lock:
            self._reservation_seq += 1
            reservation = {"id": f"r{self._reservation_seq}", "provider": provider, "role": role, "stage": stage, "model": model,
                           "reserved_usd": round(float(reserved_usd), 6), "at_utc": utcnow()}
            self.open_reservations.append(reservation)
            self._append({"event": "reserve", **reservation})
        self._changed()
        return reservation["id"]

    def add_call(self, call: ModelCall, reservation_id: str | None = None) -> None:
        with self._lock:
            if reservation_id is not None:
                self.open_reservations = [r for r in self.open_reservations if r["id"] != reservation_id]
            if call.reserved_usd is not None and call.settlement == "none":
                call.settlement = "known" if call.cost_usd is not None else "unsettled"
            self.model_calls.append(call)
            self._append({"event": "call", "reservation_id": reservation_id, **asdict(call)})
        self._changed()

    def add_op(self, op: SandboxOp) -> None:
        with self._lock:
            self.sandbox_ops.append(op)
            self._append({"event": "sandbox_op", **asdict(op)})

    # ------------------------------------------------------------------ totals
    def totals(self) -> dict:
        tokens_in = sum(c.tokens_in or 0 for c in self.model_calls)
        tokens_out = sum(c.tokens_out or 0 for c in self.model_calls)
        tokens_cached = sum(c.tokens_cached or 0 for c in self.model_calls)
        usd = [c.cost_usd for c in self.model_calls if c.cost_usd is not None]
        # Conservative total: known cost where we have it, otherwise the reservation (uncertain calls never undercount),
        # plus every reservation whose request has no call record yet.
        committed = sum(c.cost_usd if c.cost_usd is not None else (c.reserved_usd or 0.0) for c in self.model_calls)
        open_reserved = sum(r.get("reserved_usd") or 0.0 for r in self.open_reservations)
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
            "cost_usd_committed": round(committed + open_reserved, 6),
            "uncertain_unpriced_calls": uncertain,
            "open_reservations": len(self.open_reservations),
            "open_reserved_usd": round(open_reserved, 6),
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
                "open_reservations": list(self.open_reservations),
                "totals": self.totals()}


JOURNAL_FILE = "ledger.jsonl"


def read_journal(path: Path) -> dict | None:
    """Read a run's ledger journal back: known costs, calls, and reservations never closed by a call record. Returns None
    when the file is missing or holds no ledger header. Lines that do not parse (a write cut short by the interruption)
    are skipped and counted."""
    path = Path(path)
    if not path.is_file():
        return None
    calls, reservations, closed, ops, bad = [], {}, set(), 0, 0
    header = False
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            kind = record.get("event")
            if kind == "ledger":
                header = True
            elif kind == "reserve":
                reservations[record.get("id")] = record
            elif kind == "call":
                calls.append(record)
                if record.get("reservation_id"):
                    closed.add(record["reservation_id"])
            elif kind == "sandbox_op":
                ops += 1
    if not header and not calls and not reservations:
        return None
    open_reservations = [r for rid, r in reservations.items() if rid not in closed]
    known = [c["cost_usd"] for c in calls if c.get("cost_usd") is not None]
    committed = sum(c["cost_usd"] if c.get("cost_usd") is not None else (c.get("reserved_usd") or 0.0) for c in calls)
    committed += sum(r.get("reserved_usd") or 0.0 for r in open_reservations)
    return {"model_calls": len(calls), "cost_usd": round(sum(known), 6) if known else None, "cost_usd_committed": round(committed, 6),
            "uncertain_unpriced_calls": sum(1 for c in calls if c.get("cost_usd") is None and (c.get("reserved_usd") or 0.0) > 0),
            "open_reservations": len(open_reservations), "open_reserved_usd": round(sum(r.get("reserved_usd") or 0.0 for r in open_reservations), 6),
            "sandbox_operations": ops, "unparsable_lines": bad,
            "tokens_in": sum(c.get("tokens_in") or 0 for c in calls), "tokens_out": sum(c.get("tokens_out") or 0 for c in calls)}
