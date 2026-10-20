"""Usage ledgers: model calls (tokens, allowance or USD) and sandbox operations.

Persistence (19 Oct 2026): a ledger can carry a journal sink (`ledger.jsonl` in the run directory). Every reservation is
appended BEFORE the request is sent and every call record is appended as soon as it is known, so a process that dies
mid-run leaves a journal from which the known costs and the still-open reservations can be read back (`read_journal`).
`ledger.json` (the totals) is still written at the end of a run; the journal is what survives an interruption.

Durability (audit finding AC-03, 19 Oct 2026): a USD reservation is money the batch has committed to, so `reserve` succeeds only
once its journal line has been written, flushed and fsynced. With no sink attached, or when the append fails at any step (open,
write, flush, fsync, close), it raises `LedgerError` and records nothing: no request may be sent without a durable reservation.
Settlement records (`add_call`, `add_op`) are appended best-effort: when their append fails the in-memory record is kept, the
journal still holds the open reservation (which `read_journal` then counts at its bound, the conservative reading) and the
failure is counted in `journal_failures`. Durability here means "survives the death of this process"; the fsync additionally
asks the operating system to put the line on the device, which covers a host crash as far as the device honours fsync.

Tail recovery (review finding R5-01, 19 Oct 2026): an append that fails after writing part of its line leaves the journal with an
unframed tail (no final newline). Left alone, the next successful append would land on that same line, a restart's parser would
lose both records, and `reserve` would still have reported success. Every append therefore first reads the last byte of the
journal: a non-empty file that does not end in a newline is repaired, durably, by terminating the cut line and appending a
`journal_repair` record (the cut record is lost and is not reconstructed; a reservation it would have settled stays open at its
bound, the conservative reading). Every append is then verified by reading its bytes back from the offset where it started; the
byte before that offset must be a newline (or the offset must be 0). A reservation whose repair, write or verification fails
raises `LedgerError` and records nothing. A settlement whose append fails is counted in `journal_failures` and marks the ledger
`journal_degraded`; the next `reserve` runs the same repair and verification and clears the flag only when its own line read back
intact. `read_journal` reads bytes with replacement, so a tail cut inside a multi-byte character never raises.

Stop for reconciliation (revision 9, 20 Oct 2026): the ledger is the one object the provider, the executor and the pipeline of a run
share, so it carries the run's stop state. `halt` records why the run stopped (an operation whose outcome is uncertain, a journal
record that could not be made durable, a generated answer that could not be priced) and from then on `admit`, which every client
calls immediately before each request it sends (each attempt, each poll), refuses with `RunHalted`: nothing is sent after the stop.
A request admitted before the halt was sent before the stop condition, even if its bytes leave slightly later. The first halt is the
run's; later ones are kept in `halt_events`. `reconciliation_items` lists everything whose outcome is unknown, from the records
themselves, with the read-only check that settles it; nothing in it is ever sent again.

Operation records (revision 9): a sandbox operation is journaled as PENDING, durably and read back, before its spawn is sent
(`add_op`), and every later state, the accepted id first, is journaled the same way before the client goes on (`update_op`). Unlike
settlement records these must persist: when the append fails `LedgerError` is raised, the caller dispatches or polls nothing further
and halts the run with what it knows (the stage, the image and, once accepted, the operation id), which also goes to the
`attest.ledger` log as one `ATTEST-HALT` line, so it survives a journal on a full disk. A ledger without a journal sink does not dispatch
sandbox operations at all. Every model call of a provider without a USD price (the development gateway) takes a zero-USD reservation
the same way, so a call in flight when the process stops is visible after a restart as an open reservation.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

LOG = logging.getLogger("attest.ledger")


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class LedgerError(RuntimeError):
    """The journal could not take a record that must be durable before money is committed: no sink is attached, the append failed
    at open, write, flush, fsync or close, the cut tail before it could not be repaired, or the line did not read back as written.
    `reserve` raises it and records nothing; the caller must not send the request."""

    stops_run = True


class RunHalted(RuntimeError):
    """A request was refused before it was sent because the run has stopped for reconciliation (`Ledger.halt`). `record` is the
    run's halt record: why it stopped, where, and the operation that caused it."""

    stops_run = True
    uncertain = False

    def __init__(self, record: dict):
        self.record = dict(record or {})
        super().__init__(f"the run stopped for reconciliation ({self.record.get('kind')} at {self.record.get('stage') or 'an earlier stage'}): "
                         f"{self.record.get('reason') or 'no reason recorded'}; nothing further is sent")


# Sandbox operation states that leave the account's state unknown: a spawn sent without a known outcome, and an accepted operation
# whose final state was not read. None is the state of records written before revision 9 that never received one.
SPAWN_UNRESOLVED = ("PENDING", "UNCERTAIN", None)
OPERATION_UNREAD = ("ACCEPTED", "ACCEPTED_UNREAD")
TERMINAL_OPERATION = ("SUCCESS", "FAILED", "CANCELLED")
DEFINITE_SPAWN = ("NOT_SENT", "REJECTED")


def _call_uncertain(call: dict) -> bool:
    """A model call whose request may have been executed and whose outcome is unknown. Revision-9 records say so in `outcome`;
    earlier records are recognised by their public error text and a request that was (or may have been) sent."""
    outcome = call.get("outcome")
    if outcome is not None:
        return outcome == "uncertain"
    return (not call.get("ok") and call.get("request_sent") is not False and "uncertain" in (call.get("error") or "").lower())


def reconciliation_items_from(model_calls: list, sandbox_ops: list, halt: dict | None = None, halt_events: list | None = None,
                              open_reservations: list | None = None) -> list[dict]:
    """Everything a run leaves whose outcome is unknown, from its records (dicts), with the read-only check that settles it. The same
    function serves the live ledger, the bundle's record (`attest check` recomputes it) and the journal read after a restart."""
    items: list[dict] = []
    for call in model_calls or []:
        if not isinstance(call, dict):
            continue
        if _call_uncertain(call):
            items.append({"kind": "model_call", "service": "inference", "provider": call.get("provider"), "stage": call.get("stage"),
                          "started_at_utc": call.get("started_at_utc"), "elapsed_ms": call.get("elapsed_ms"), "phase": call.get("transport_phase"),
                          "http_status": call.get("http_status"), "reserved_usd": call.get("reserved_usd"),
                          "how": "look for a request received in [started_at, started_at + elapsed] in the provider's ingress log or billing; "
                                 "it was never sent again"})
        elif call.get("ok") and call.get("settlement") == "unsettled":
            items.append({"kind": "model_call_billing", "service": "inference", "provider": call.get("provider"), "stage": call.get("stage"),
                          "started_at_utc": call.get("started_at_utc"), "reserved_usd": call.get("reserved_usd"),
                          "how": "the answer arrived but could not be priced from its usage; read the call's cost from the provider's billing "
                                 "(the reservation stays committed until then)"})
    for reservation in open_reservations or []:
        if isinstance(reservation, dict):
            items.append({"kind": "model_call_in_flight", "service": "inference", "provider": reservation.get("provider"), "stage": reservation.get("stage"),
                          "started_at_utc": reservation.get("at_utc"), "reserved_usd": reservation.get("reserved_usd"), "reservation_id": reservation.get("id"),
                          "how": "a reservation without a call record: the request may have been sent when the process stopped; look for it in the "
                                 "provider's ingress log or billing after started_at (it stays committed at its bound)"})
    known_uuids = set()
    for op in sandbox_ops or []:
        if not isinstance(op, dict):
            continue
        status = op.get("status")
        base = {"service": "sandboxes", "stage": op.get("stage"), "op_id": op.get("op_id"), "status": status, "image_uuid": op.get("image_uuid"),
                "started_at_utc": op.get("started_at_utc"), "ended_at_utc": op.get("ended_at_utc"), "attempts": op.get("attempts"),
                "http_status": op.get("http_status"), "transport_failures": op.get("transport_failures") or []}
        if op.get("operation_uuid"):
            known_uuids.add(op["operation_uuid"])
        if status in OPERATION_UNREAD and op.get("operation_uuid"):
            items.append({"kind": "sandbox_operation", **base, "operation_uuid": op["operation_uuid"],
                          "how": f"GET /operations/{op['operation_uuid']} for its final status (read-only); it is never spawned again"})
        elif status in SPAWN_UNRESOLVED or (status in OPERATION_UNREAD and not op.get("operation_uuid")):
            items.append({"kind": "sandbox_spawn", **base, "operation_uuid": None,
                          "how": "GET /operations?kind=instance with since/until around started_at, matching image_uuid (the spawn request carries "
                                 "no client id); it is never sent again"})
    for record in ([halt] if halt else []) + list(halt_events or []):
        operation = (record or {}).get("operation") or {}
        if not operation:
            continue
        uuid = operation.get("operation_uuid")
        if operation.get("service") == "tavily":
            items.append({"kind": "search", "service": "tavily", "stage": record.get("stage"), "query_index": operation.get("query_index"),
                          "started_at_utc": operation.get("started_at_utc"),
                          "how": "compare the account's usage before the search (recorded in grounding) with the Tavily dashboard: at most one "
                                 "credit; the search was never sent again"})
        elif uuid and uuid not in known_uuids:
            known_uuids.add(uuid)
            items.append({"kind": "sandbox_operation", "service": "sandboxes", "stage": record.get("stage"), "op_id": operation.get("op_id"),
                          "status": operation.get("status"), "operation_uuid": uuid, "image_uuid": operation.get("image_uuid"),
                          "started_at_utc": operation.get("started_at_utc"),
                          "how": f"GET /operations/{uuid} for its final status (read-only); its id is known from the halt record because the "
                                 "journal could not take it; it is never spawned again"})
        elif record.get("kind") == "journal_failure" and not uuid and operation.get("dispatched") is False:
            items.append({"kind": "journal", "service": operation.get("service") or "journal", "stage": record.get("stage"), "op_id": operation.get("op_id"),
                          "how": "nothing was dispatched for this record; the run's journal could not take it (see the halt reason), so check the "
                                 "volume (space, I/O errors) before the service runs again"})
        elif (record.get("kind") == "uncertain_operation" and not uuid
              and not any(i.get("stage") == record.get("stage") and i.get("service") == operation.get("service") for i in items)):
            # the halt names an operation that no record of the run represents (a client that keeps no records): it is listed from the
            # halt itself, so a stop for an uncertain operation never leaves an empty list
            items.append({"kind": "unrecorded_operation", "service": operation.get("service"), "stage": record.get("stage"), "op_id": operation.get("op_id"),
                          "started_at_utc": operation.get("started_at_utc") or record.get("at_utc"),
                          "how": "the client recorded no request for this operation: look for it in the provider's records around the halt time "
                                 "(sandboxes: GET /operations?kind=instance with since/until; inference: the ingress log or billing); it was never "
                                 "sent again"})
    return items


def item_key(item: dict) -> tuple:
    """How a reconciliation item is identified when a recorded list is compared with a recomputed one."""
    return (item.get("kind"), item.get("stage"), item.get("op_id") or item.get("operation_uuid") or item.get("reservation_id") or item.get("started_at_utc"))


def _open_journal(path: Path):
    """One append handle on the journal. A module-level seam so tests can inject failures at the handle level; it goes through
    `Path.open` so a failure injected there (the audit's reproduction patches `Path.open`) reaches the real write path."""
    return Path(path).open("a", encoding="utf-8")


def _write_durably(path: Path, lines: list[str]) -> None:
    """Append `lines` and make them durable: write, flush, fsync, close. Every failure propagates (OSError, or ValueError from a
    handle that was closed under us) so the caller can decide whether the record was one that must not be lost."""
    handle = _open_journal(path)
    try:
        for line in lines:
            handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()


TAIL_SCAN_BYTES = 65_536  # how far back a repair looks for the start of a cut line (its length and head go into the repair record)


def _tail_state(path: Path) -> tuple[int, bytes]:
    """The journal's size and the bytes of its unterminated last line: empty when the file is missing, empty or ends with a
    newline. A binary read of the last byte decides; the cut line itself is read back at most TAIL_SCAN_BYTES. Raises OSError."""
    path = Path(path)
    if not path.exists():
        return 0, b""
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size == 0:
            return 0, b""
        handle.seek(size - 1)
        if handle.read(1) == b"\n":
            return size, b""
        start = max(0, size - TAIL_SCAN_BYTES)
        handle.seek(start)
        chunk = handle.read(size - start)
    return size, chunk.rsplit(b"\n", 1)[-1]


def _write_verified(path: Path, lines: list[str], framed_before: bool = True) -> int:
    """Append `lines` durably (write, flush, fsync, close), then read them back from the offset where the append started: the bytes
    on disk must equal what was written and, unless `framed_before` is False (the repair of a cut tail), the byte before the offset
    must be a newline or the offset must be 0. Returns the offset. Raises OSError or ValueError from the write and LedgerError when
    the read-back differs."""
    path = Path(path)
    offset = path.stat().st_size if path.exists() else 0
    data = "".join(lines).encode("utf-8")
    _write_durably(path, lines)
    with path.open("rb") as handle:
        if offset and framed_before:
            handle.seek(offset - 1)
            before = handle.read(1)
            if before != b"\n":
                raise LedgerError(f"journal verification failed: the byte before offset {offset} is {before!r}, not a newline, so the record "
                                  f"would share its line with a cut record")
        else:
            handle.seek(offset)
        on_disk = handle.read(len(data))
    if on_disk != data:
        raise LedgerError(f"journal verification failed: the {len(data)} bytes appended at offset {offset} read back differently "
                          f"({len(on_disk)} bytes read{'' if len(on_disk) == len(data) else ', short'})")
    return offset


def _repair_tail(path: Path) -> dict | None:
    """Frame an unterminated last line (a write cut short) so that later records start on their own line: append a newline and a
    `journal_repair` record, durably and verified. Returns the repair record, or None when the tail was already framed. The cut
    record is lost and is not reconstructed: a reservation it would have settled stays open at its bound. Raises OSError or
    ValueError from the write and LedgerError when the repair does not read back."""
    size, partial = _tail_state(path)
    if size == 0 or not partial:
        return None
    record = {"event": "journal_repair", "at_utc": utcnow(),
              "note": "the previous line was cut short (no final newline) and has been terminated here; its record is lost and is not "
                      "reconstructed, so a reservation it would have settled stays open at its bound and is reconciled against the provider's billing",
              "cut_line_bytes": len(partial), "cut_line_head": partial[:120].decode("utf-8", "replace")}
    _write_verified(path, ["\n", json.dumps(record, ensure_ascii=False) + "\n"], framed_before=False)
    return record


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
    # Transport (revision 8): whether any byte of the request was written (False only when the connection, the proxy tunnel or
    # the TLS handshake failed first, so the provider cannot have received it; such an attempt costs nothing and may be sent
    # again), and the phase a failed request reached ("connect", "send", "response"). None on records made before revision 8.
    request_sent: bool | None = None
    transport_phase: str | None = None
    # Answer class (revision 9): "answered" (the provider answered 2xx, whether the output was usable or not), "rejected" (a definite
    # refusal, HTTP 4xx), "not_sent" (no byte was written), "refused" (not sent because the run had stopped or a cap applied) or
    # "uncertain" (the request may have been executed: an HTTP 5xx, or a failure after it was written). None on earlier records.
    outcome: str | None = None
    http_status: int | None = None


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
    # Transport (revision 8): spawn attempts (an attempt that failed before any byte of the request was written is sent again,
    # bounded) and the public text of each failed attempt with the phase it reached
    attempts: int = 1
    transport_failures: list = field(default_factory=list)
    # Revision 9: the client-side id that links the PENDING record to its later states (the spawn request carries no client id, so the
    # service never sees it), the HTTP status of a refused or failed spawn, when the outcome became known, and why polling ended early
    op_id: str | None = None
    http_status: int | None = None
    ended_at_utc: str | None = None
    outcome_note: str | None = None


@dataclass
class Ledger:
    model_calls: list[ModelCall] = field(default_factory=list)
    sandbox_ops: list[SandboxOp] = field(default_factory=list)
    # reservations taken for requests whose call record has not been written yet (in flight, or lost with the process)
    open_reservations: list[dict] = field(default_factory=list)
    sink: Path | None = field(default=None, repr=False, compare=False)
    on_change: object = field(default=None, repr=False, compare=False)  # callable(totals) after every change
    # settlement records the journal did not take (the run went on; the in-memory record and the reservation already in the
    # journal keep the accounting conservative); reported in totals so a bundle shows that its journal is incomplete
    journal_failures: list[dict] = field(default_factory=list, repr=False, compare=False)
    # cut tails this ledger terminated before appending (the `journal_repair` records it wrote), reported in totals
    journal_repairs: list[dict] = field(default_factory=list, repr=False, compare=False)
    # why the last settlement append failed, until a reservation line is appended and read back intact after the tail was repaired
    journal_degraded: str | None = field(default=None, repr=False, compare=False)
    # private diagnostics sink (attest.core.diagnostics.Diagnostics, attached by the pipeline): providers route the raw text of a
    # failed call through public_error() so that call records, the journal and the bundle carry only the public vocabulary (R5-04)
    diagnostics: object = field(default=None, repr=False, compare=False)
    # the run's stop state (revision 9): the first halt record, later ones, and an observer called once when the run first halts
    halted: dict | None = field(default=None, compare=False)
    halt_events: list[dict] = field(default_factory=list, compare=False)
    on_halt: object = field(default=None, repr=False, compare=False)
    admitted: int = field(default=0, repr=False, compare=False)  # requests admitted by `admit` (every attempt and poll)
    refused: int = field(default=0, repr=False, compare=False)   # requests refused by `admit` because the run had stopped
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    _halt_lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)
    _reservation_seq: int = field(default=0, repr=False, compare=False)
    _op_seq: int = field(default=0, repr=False, compare=False)

    # ------------------------------------------------------------------ journal
    def attach_sink(self, path: Path) -> None:
        """Start journaling into `path`; anything already recorded is written first so the journal is complete. Raises LedgerError
        when the journal cannot be created (or an existing file's cut tail cannot be repaired, or the header does not read back): a
        run whose journal does not exist must not start paid work."""
        with self._lock:
            sink = Path(path)
            lines = [json.dumps({"event": "ledger", "at_utc": utcnow(), "version": 1,
                                 "note": "append-only journal: reservations are written (and fsynced) before a request is sent, call records as soon as "
                                         "they are known; an open reservation without a call record is a request whose outcome was lost "
                                         "with the process and stays committed at its bound; a journal_repair record terminates a line that a "
                                         "failed append cut short (that record is lost, the reservation it would have settled stays open)"}) + "\n"]
            lines += [json.dumps({"event": "call", **asdict(call)}, ensure_ascii=False) + "\n" for call in self.model_calls]
            lines += [json.dumps({"event": "sandbox_op", **asdict(op)}, ensure_ascii=False) + "\n" for op in self.sandbox_ops]
            if self.halted:
                lines += [json.dumps({"event": "halt", **record}, ensure_ascii=False) + "\n" for record in [self.halted] + self.halt_events]
            lines += [json.dumps({"event": "reserve", **reservation}) + "\n" for reservation in self.open_reservations]
            try:
                sink.parent.mkdir(parents=True, exist_ok=True)
                repair = _repair_tail(sink)
                if repair is not None:
                    self.journal_repairs.append(repair)
                _write_verified(sink, lines)
            except (OSError, ValueError, LedgerError) as error:
                raise LedgerError(f"cannot create the ledger journal {sink}: {type(error).__name__}: {error}") from error
            self.sink = sink

    def detach_sink(self) -> None:
        """Stop journaling: called when the run directory is sealed by its manifest, so operations recorded afterwards by the
        caller (for example the evaluation harness's judge) stay in memory and in the caller's own records, not in a file whose
        digest the manifest already fixed."""
        with self._lock:
            self.sink = None

    def _append(self, record: dict, must_persist: bool = False) -> None:
        """Append one journal line: repair a cut tail first, then write, flush, fsync, close, then read the line back (R5-01).
        `must_persist` is set for reservations: any failure, including a missing sink, becomes LedgerError and nothing is recorded.
        A settlement record that fails is counted, marks the journal degraded and the run goes on, because the in-memory record and
        the reservation already in the journal keep the accounting conservative."""
        if self.sink is None:
            if must_persist:
                raise LedgerError("no journal sink is attached: a USD reservation must be journaled before its request is sent")
            return
        try:
            repair = _repair_tail(self.sink)
            if repair is not None:
                self.journal_repairs.append(repair)
            _write_verified(self.sink, [json.dumps(record, ensure_ascii=False) + "\n"])
        except (OSError, ValueError, LedgerError) as error:
            reason = f"{type(error).__name__}: {error}"[:300]
            self.journal_failures.append({"event": record.get("event"), "at_utc": utcnow(), "error": reason})
            if must_persist:
                raise LedgerError(f"the ledger journal {self.sink} did not take the reservation ({reason}); "
                                  f"nothing was recorded and the request must not be sent") from error
            self.journal_degraded = (f"the {record.get('event')} record failed to journal at {utcnow()} ({reason}); the journal tail is repaired "
                                     f"and the next reservation line verified before any further request is dispatched")

    def _changed(self) -> None:
        if self.on_change is not None:
            try:
                self.on_change(self.totals())
            except Exception:  # noqa: BLE001 - observers never break accounting
                pass

    # ------------------------------------------------------------------ records
    def reserve(self, provider: str, role: str, stage: str, model: str, reserved_usd: float) -> str:
        """Record a USD reservation before a request is sent and return its id (`add_call` closes it). The reservation exists only
        once its journal line is durable and read back intact after any cut tail was repaired: with no sink, a failed repair, a
        failed append or a failed verification LedgerError is raised and nothing is recorded in memory either (no request will be
        sent, so nothing is owed); the caller must not dispatch. A ledger degraded by an earlier settlement failure is cleared here
        and only here, once this line is verified."""
        with self._lock:
            self._reservation_seq += 1
            reservation = {"id": f"r{self._reservation_seq}", "provider": provider, "role": role, "stage": stage, "model": model,
                           "reserved_usd": round(float(reserved_usd), 6), "at_utc": utcnow()}
            self._append({"event": "reserve", **reservation}, must_persist=True)
            self.open_reservations.append(reservation)
            self.journal_degraded = None  # the tail is framed and this line read back as written: the journal takes records again
        self._changed()
        return reservation["id"]

    def public_error(self, stage: str, error: BaseException | str, context: dict | None = None) -> str:
        """The only form in which a failed call's error enters a call record (and so the journal and the bundle): a fixed public
        sentence, with a correlation reference when a diagnostics sink is attached (the raw text goes to its private sidecar)."""
        sink = self.diagnostics
        if sink is not None:
            try:
                return sink.public_text(stage, error, context)
            except Exception:  # noqa: BLE001 - diagnostics must never break accounting
                pass
        from .core.diagnostics import classify_error  # local import: core imports this module
        return classify_error(error)[1]

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
        """Journal a sandbox operation BEFORE its spawn is sent: it gets its client-side id and the state PENDING, and the line must be
        durable and read back (revision 9). On any failure, including a ledger without a journal sink, `LedgerError` is raised and the
        operation is not recorded; the caller must not send the spawn."""
        with self._lock:
            self._op_seq += 1
            if not op.op_id:
                op.op_id = f"s{self._op_seq}"
            if op.status is None:
                op.status = "PENDING"
            self._append({"event": "sandbox_op", **asdict(op)}, must_persist=True)
            self.sandbox_ops.append(op)

    def update_op(self, op: SandboxOp) -> None:
        """Journal the current state of an operation already added: the operation id the service accepted (before polling starts), then
        its final or uncertain status. It must be durable (revision 9): on failure `LedgerError` is raised and the caller goes no further
        (no poll, no next stage) and halts the run with what it knows. The in-memory record is the same object and already holds the state."""
        with self._lock:
            self._append({"event": "sandbox_op_update", **asdict(op)}, must_persist=True)

    # ------------------------------------------------------------------ stop for reconciliation (revision 9)
    def halt(self, kind: str, reason: str, stage: str | None = None, operation: dict | None = None, detail: str | None = None) -> dict:
        """Stop the run: from now on `admit` refuses every request. `kind` is `uncertain_operation`, `journal_failure`,
        `metering_unknown` or `batch_stop`; `reason` is public text (it enters the journal and the bundle); `operation` names what has
        to be reconciled (stage, op_id, operation_uuid, image_uuid, started_at_utc, service); `detail` is the raw error text, which only
        the private log line receives. The first halt is the run's (`halted`); later ones are appended to `halt_events`. The record is
        journaled (best effort), except when the journal itself is the cause: a journal that just failed is not tried again, and its own
        records (a PENDING operation without an outcome, a cut tail) already show after a restart what was left open. Every halt is
        logged as one `ATTEST-HALT` line. Returns the run's halt record."""
        record = {"kind": kind, "reason": str(reason)[:600], "stage": stage, "operation": dict(operation or {}) or None, "at_utc": utcnow()}
        with self._halt_lock:
            first = self.halted is None
            if first:
                self.halted = record
            else:
                self.halt_events.append(record)
        if kind != "journal_failure":
            with self._lock:
                self._append({"event": "halt", **record})
        LOG.error("ATTEST-HALT %s%s", json.dumps(record, ensure_ascii=False, default=str), f" detail: {str(detail)[:2000]}" if detail else "")
        if first and self.on_halt is not None:
            try:
                self.on_halt(self, record)
            except Exception:  # noqa: BLE001 - an observer never prevents the stop itself
                LOG.exception("halt observer failed")
        self._changed()
        return self.halted

    def admit(self, service: str, stage: str | None = None) -> None:
        """Called by every client immediately before each request it sends (every attempt, every poll, every read). Raises `RunHalted`
        once the run has stopped, so nothing is sent after the stop condition; a request admitted before the halt is one the run had
        already sent when it stopped."""
        with self._halt_lock:
            if self.halted is not None:
                self.refused += 1
                raise RunHalted(self.halted)
            self.admitted += 1

    def reconciliation_items(self) -> list[dict]:
        """Everything this run leaves whose outcome is unknown (see `reconciliation_items_from`)."""
        with self._halt_lock:
            halt, events = self.halted, list(self.halt_events)
        return reconciliation_items_from([asdict(c) for c in self.model_calls], [asdict(o) for o in self.sandbox_ops], halt, events,
                                         list(self.open_reservations))

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
            "journal_failures": len(self.journal_failures),
            "journal_repairs": len(self.journal_repairs),
            "journal_degraded": self.journal_degraded,
            "rate_limited_calls": sum(1 for c in self.model_calls if not c.ok and "HTTP 429" in (c.error or "")),
            "pacing_wait_ms": sum(c.pacing_wait_ms or 0 for c in self.model_calls),
            "by_model": by_model,
            "calls_not_sent": sum(1 for c in self.model_calls if c.request_sent is False),
            "calls_uncertain": sum(1 for c in self.model_calls if _call_uncertain(asdict(c))),
            "halted": self.halted is not None,
            "reconciliation_items": len(self.reconciliation_items()),
            "sandbox_operations": len(self.sandbox_ops),
            "sandbox_spawn_retries": sum(max(0, (o.attempts or 1) - 1) for o in self.sandbox_ops),
            "sandbox_uncertain": sum(1 for o in self.sandbox_ops if o.status in ("UNCERTAIN", "ACCEPTED_UNREAD")),
            "sandbox_rejected": sum(1 for o in self.sandbox_ops if o.status == "REJECTED"),
            "sandbox_duration_s": round(sum(o.duration_s or 0 for o in self.sandbox_ops), 3),
            "sandbox_retained_images": [o.result_image_uuid for o in self.sandbox_ops if o.result_image_uuid],
            "sandbox_raw_cost_diag_sum": round(sum(o.raw_cost_diag or 0 for o in self.sandbox_ops), 8),
        }

    def to_dict(self) -> dict:
        return {"model_calls": [asdict(c) for c in self.model_calls],
                "sandbox_ops": [asdict(o) for o in self.sandbox_ops],
                "open_reservations": list(self.open_reservations),
                "journal_failures": list(self.journal_failures),
                "journal_repairs": list(self.journal_repairs),
                "journal_degraded": self.journal_degraded,
                "halt": self.halted, "halt_events": list(self.halt_events), "reconciliation": self.reconciliation_items(),
                "totals": self.totals()}


JOURNAL_FILE = "ledger.jsonl"


def read_journal(path: Path) -> dict | None:
    """Read a run's ledger journal back: known costs, calls, and reservations never closed by a call record. Returns None
    when the file is missing or holds no ledger header. Lines that do not parse (a write cut short by the interruption)
    are skipped and counted, `journal_repair` records are counted, and the bytes are decoded with replacement so a tail cut
    inside a multi-byte character never raises; `tail_framed` says whether the file ends with a newline.

    Revision 9: sandbox operations are followed by their client-side id from the PENDING record to their last journaled state, so a
    spawn that was sent but never answered (`spawns_unresolved`) and an accepted operation never read to its end (`operations_unread`)
    are both named; so are the halt records, the model calls whose outcome is uncertain, and every reservation never closed (a call in
    flight when the process stopped). `reconciliation_items` is the same list the live ledger would give, and
    `reconciliation_required` says whether anything is on it or the run had halted."""
    path = Path(path)
    if not path.is_file():
        return None
    calls, reservations, closed, ops, bad, repairs = [], {}, set(), 0, 0, 0
    accepted: dict[str, dict] = {}  # operation id -> its latest journaled state (revision 8: written before polling)
    by_op_id: dict[str, dict] = {}  # client-side id -> the operation's latest journaled record (revision 9)
    halts: list[dict] = []
    header = False
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size:
            handle.seek(size - 1)
        tail_framed = size == 0 or handle.read(1) == b"\n"
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            kind = record.get("event") if isinstance(record, dict) else None
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
                if record.get("op_id"):
                    by_op_id[record["op_id"]] = record
            elif kind == "sandbox_op_update":
                if record.get("op_id"):
                    by_op_id[record["op_id"]] = record
                if record.get("operation_uuid"):
                    accepted[record["operation_uuid"]] = {"stage": record.get("stage"), "status": record.get("status")}
            elif kind == "halt":
                halts.append({k: v for k, v in record.items() if k != "event"})
            elif kind == "journal_repair":
                repairs += 1
    if not header and not calls and not reservations:
        return None
    open_reservations = [r for rid, r in reservations.items() if rid not in closed]
    tracked = [{k: v for k, v in record.items() if k != "event"} for record in by_op_id.values()]
    items = reconciliation_items_from(calls, tracked, halts[0] if halts else None, halts[1:], open_reservations)
    tracked_uuids = {op.get("operation_uuid") for op in tracked if op.get("operation_uuid")}
    for uuid, state in sorted(accepted.items()):  # records written before revision 9 carry no client-side id
        if uuid not in tracked_uuids and state.get("status") not in TERMINAL_OPERATION:
            items.append({"kind": "sandbox_operation", "service": "sandboxes", "stage": state.get("stage"), "op_id": None, "status": state.get("status"),
                          "operation_uuid": uuid, "how": f"GET /operations/{uuid} for its final status (read-only); it is never spawned again"})
    known = [c["cost_usd"] for c in calls if c.get("cost_usd") is not None]
    committed = sum(c["cost_usd"] if c.get("cost_usd") is not None else (c.get("reserved_usd") or 0.0) for c in calls)
    committed += sum(r.get("reserved_usd") or 0.0 for r in open_reservations)
    return {"model_calls": len(calls), "cost_usd": round(sum(known), 6) if known else None, "cost_usd_committed": round(committed, 6),
            "uncertain_unpriced_calls": sum(1 for c in calls if c.get("cost_usd") is None and (c.get("reserved_usd") or 0.0) > 0),
            "open_reservations": len(open_reservations), "open_reserved_usd": round(sum(r.get("reserved_usd") or 0.0 for r in open_reservations), 6),
            "sandbox_operations": ops, "unparsable_lines": bad, "journal_repairs": repairs, "tail_framed": tail_framed,
            # accepted operations whose final status was never journaled (the process stopped while polling): reconcile them
            "operations_unread": sorted(uuid for uuid, state in accepted.items() if state.get("status") not in TERMINAL_OPERATION),
            "spawns_unresolved": [{"op_id": op.get("op_id"), "stage": op.get("stage"), "status": op.get("status"), "image_uuid": op.get("image_uuid"),
                                   "started_at_utc": op.get("started_at_utc")} for op in tracked
                                  if op.get("status") in SPAWN_UNRESOLVED and not op.get("operation_uuid")],
            "calls_uncertain": sum(1 for c in calls if _call_uncertain(c)),
            "halt": halts[0] if halts else None, "halt_events": halts[1:],
            "reconciliation_items": items, "reconciliation_required": bool(items) or bool(halts),
            "tokens_in": sum(c.get("tokens_in") or 0 for c in calls), "tokens_out": sum(c.get("tokens_out") or 0 for c in calls)}
