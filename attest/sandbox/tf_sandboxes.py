"""Nebius Token Factory Sandboxes (ConTree) REST adapter.

Verified primitives (2026-10-15 smoke): POST /instances, GET /operations/{id},
retained checkpoints, disposable branches, networking.enabled=false.

Transport of inputs: a JSON job is gzip-compressed and sent as base64 stdin to a
small guest runner (Python, stdlib only) that writes files, runs steps with
subprocess, and prints a marker-delimited JSON report. Accepted operation UUIDs
are recorded before polling and a POST that may have reached the service is never replayed.

Request size (measured 17 Oct 2026): the API accepted a 534 KB request body, answered
HTTP 413 at about 860 KB and stalled the write at about 1 MB. Jobs are therefore
compressed and capped at MAX_REQUEST_BYTES; a checkpoint whose files do not fit in one
request is built as a chain of retained images (files first, the install and baseline
steps in the final operation). Disposable branches carry only changed files and test
modules and must fit in one request.

Guest output (BOUND-04, audit of 19 Oct 2026): the runner drains each step's stdout and stderr concurrently into bounded
head-and-tail buffers while the step runs, counts every byte, starts each step in its own session and kills the whole
process group on the step's deadline or when a stream passes the output limit, bounds every wait, and records a truthful
failure (`timed_out`, `output_exhausted`, `cleanup`) in the step report. The report format read here is unchanged.

Transport (revision 8, 19 Oct 2026): GET (image lookup, operation polls) and DELETE (cancel) are retried on any transport failure,
bounded. A spawn (POST /instances) is sent again only when the previous attempt failed before any byte of it was written (its
connection, proxy tunnel or TLS handshake failed), at most NOT_SENT_RETRIES times; the attempts are recorded on the operation. A
spawn whose bytes were written and whose answer was lost is UNCERTAIN and never sent again. The operation id the service accepts is
journaled before polling starts; when the outcome of an accepted operation cannot be read, the operation is ACCEPTED_UNREAD and the
id is kept for reconciliation (GET /operations/{id}). The spawn request carries no client-chosen id (the API has none), so an
uncertain spawn is reconciled by listing the account's operations around its time and source image (GET /operations).

Revision 9 (20 Oct 2026): every operation is journaled as PENDING, durably and read back, before its spawn is sent, and its accepted id
before the first poll; if either record cannot be made durable nothing further is dispatched or polled and the run halts with what is
known (stage, image, accepted id) in the halt record and the `attest.ledger` log. A spawn answered with an HTTP 4xx is REJECTED (a
definite refusal); one answered with an HTTP 5xx, a 2xx without an operation id, or a failure after its bytes were written is
UNCERTAIN: the run halts (`Ledger.halt`) and nothing is sent again. Polls and reads are retried, bounded, on a transport failure or an
answer that asks for a retry (404 for a just-accepted id, 408, 429, 5xx); an accepted operation whose outcome is still not read, or that
never reaches a terminal state, is ACCEPTED_UNREAD and listed for reconciliation. Every request is admitted by the ledger first, so
once the run has halted (here or in a parallel branch) no spawn, poll or cancel leaves; an operation being polled at that moment is
ACCEPTED_UNREAD with its id kept.
"""

from __future__ import annotations

import base64
import gzip
import json
import time

from ..http import (NOT_SENT_BACKOFF_S, NOT_SENT_RETRIES, READ_BACKOFF_S, READ_RETRIES, HttpError, TransportError, backoff, post_outcome,
                    read_retryable, request_json, retry_after_s)
from ..ledger import Ledger, LedgerError, RunHalted, SandboxOp, utcnow
from .base import RunResult, StepResult

BASE = "https://api.tokenfactory.nebius.com/sandboxes/v1"
TERMINAL = {"SUCCESS", "FAILED", "CANCELLED"}
MAX_REQUEST_BYTES = 400_000  # base64 text of the compressed job; the measured acceptance point was 534 KB, refusal at ~860 KB
MARK_BEGIN = "ATTEST-RESULT-BEGIN"
MARK_END = "ATTEST-RESULT-END"
GUEST_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8",
             "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}

GUEST_RUNNER = r'''
import base64, gzip, json, os, signal, subprocess, sys, threading, time
GRACE_S = 2.0  # bounded wait for a killed group to be reaped and for its pipes to close (at most three such waits per step)

class Drain(threading.Thread):
    # Reads one pipe to EOF while the step runs. Keeps only the first and the last cap//2 bytes, counts every byte and sets
    # `exhausted` once the stream passes the output limit, so a noisy step never grows the runner's memory.
    def __init__(self, fd, cap, limit, exhausted):
        threading.Thread.__init__(self, daemon=True)
        self.fd, self.cap, self.limit, self.exhausted = fd, cap, limit, exhausted
        self.half = max(1, cap // 2)
        self.head, self.tail, self.total = bytearray(), bytearray(), 0
    def run(self):
        try:
            while True:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                self.total += len(chunk)
                if len(self.head) < self.half:
                    self.head += chunk[: self.half - len(self.head)]
                self.tail += chunk
                if len(self.tail) > self.cap + self.half:
                    del self.tail[: len(self.tail) - self.half]
                if self.total > self.limit:
                    self.exhausted.set()
        finally:
            try:
                os.close(self.fd)
            except OSError:
                pass
    def text(self):
        if self.total <= self.cap:
            return bytes(self.tail).decode("utf-8", "replace")
        omitted = self.total - len(self.head) - self.half
        return (bytes(self.head).decode("utf-8", "replace") + "\n...[truncated: %d of %d bytes omitted]...\n" % (omitted, self.total)
                + bytes(self.tail[-self.half:]).decode("utf-8", "replace"))

def kill_group(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
        return True
    except OSError:
        return False

def sweep_session(sid):
    # Linux: SIGKILL whatever is left in the step's session (read from /proc), so a descendant that moved to its own process
    # group does not outlive the step. Without /proc nothing is swept and 0 is reported.
    killed = 0
    if not os.path.isdir("/proc"):
        return killed
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            with open("/proc/" + name + "/stat", "rb") as handle:
                fields = handle.read().rsplit(b")", 1)[1].split()
            if int(fields[3]) == sid:
                os.kill(int(name), signal.SIGKILL)
                killed += 1
        except (OSError, ValueError, IndexError):
            continue
    return killed

def join_all(threads, seconds):
    until = time.monotonic() + seconds
    for thread in threads:
        thread.join(max(0.0, until - time.monotonic()))
    return not any(thread.is_alive() for thread in threads)

def run_step(step, cap, output_limit):
    started = time.monotonic()
    timeout = float(step.get("timeout", 60))
    record = {"name": step.get("name"), "cmd": step["cmd"], "cwd": step.get("cwd")}
    env = dict(os.environ)
    env.update(step.get("env") or {})
    exhausted = threading.Event()
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()
    try:
        proc = subprocess.Popen(step["cmd"], cwd=step.get("cwd"), env=env, stdin=subprocess.DEVNULL,
                                stdout=out_w, stderr=err_w, start_new_session=True)
    except Exception as error:
        for fd in (out_r, out_w, err_r, err_w):
            os.close(fd)
        record.update(exit_code=None, timed_out=False, output_exhausted=False, stdout="", stderr="", stdout_bytes=0, stderr_bytes=0,
                      stdout_truncated=False, stderr_truncated=False, error=type(error).__name__ + ": " + str(error)[:300],
                      duration_s=round(time.monotonic() - started, 3))
        return record
    os.close(out_w)
    os.close(err_w)
    drains = [Drain(out_r, cap, output_limit, exhausted), Drain(err_r, cap, output_limit, exhausted)]
    for drain in drains:
        drain.start()
    deadline = started + timeout
    while proc.poll() is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or exhausted.is_set():
            break
        exhausted.wait(min(0.05, remaining))
    running = proc.poll() is None
    timed_out = running and time.monotonic() >= deadline
    cleanup = {"killed_group": False, "reaped": True, "pipes_closed": True, "descendants_killed": 0}
    if running:  # deadline or output exhaustion: the whole session goes, then one bounded wait for the leader
        cleanup["killed_group"] = kill_group(proc.pid)
        try:
            proc.wait(timeout=GRACE_S)
        except subprocess.TimeoutExpired:
            cleanup["reaped"] = False
    if not join_all(drains, GRACE_S):
        # the step exited but a descendant still holds its pipes: kill the group it left behind, then wait once more
        cleanup["killed_group"] = kill_group(proc.pid) or cleanup["killed_group"]
        cleanup["pipes_closed"] = join_all(drains, GRACE_S)
    cleanup["descendants_killed"] = sweep_session(proc.pid)
    record.update(exit_code=(None if running or not cleanup["reaped"] else proc.returncode), timed_out=timed_out,
                  output_exhausted=exhausted.is_set(), stdout=drains[0].text(), stderr=drains[1].text(),
                  stdout_bytes=drains[0].total, stderr_bytes=drains[1].total, stdout_truncated=drains[0].total > cap,
                  stderr_truncated=drains[1].total > cap, cleanup=cleanup, duration_s=round(time.monotonic() - started, 3))
    return record

raw = sys.stdin.buffer.read()
# The API decodes the request's base64 stdin before it reaches this process, so the bytes here are the gzip stream
# itself; the other branches keep plain JSON and still-base64 text working.
if raw[:2] == b"\x1f\x8b":
    raw = gzip.decompress(raw)
try:
    job = json.loads(raw.decode("utf-8"))
except Exception:
    decoded = base64.b64decode(raw)
    if decoded[:2] == b"\x1f\x8b":
        decoded = gzip.decompress(decoded)
    job = json.loads(decoded.decode("utf-8"))
report = {"runner": "attest-guest/3", "python": sys.version.split()[0], "uid": os.getuid(),
          "writes": [], "deletes": [], "steps": []}
for path, encoded in (job.get("write") or {}).items():
    data = base64.b64decode(encoded)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)
    report["writes"].append({"path": path, "bytes": len(data)})
for path in job.get("delete") or []:
    try:
        os.remove(path)
        report["deletes"].append({"path": path, "removed": True})
    except FileNotFoundError:
        report["deletes"].append({"path": path, "removed": False})
cap = int(job.get("stream_cap_bytes") or 65536)                 # bytes of each stream kept for the report (head and tail)
output_limit = int(job.get("output_limit_bytes") or 64000000)   # bytes a stream may produce before the step is killed
for step in job.get("steps") or []:
    try:
        record = run_step(step, cap, output_limit)
    except Exception as error:
        record = {"name": step.get("name"), "cmd": step.get("cmd"), "cwd": step.get("cwd"), "exit_code": None, "timed_out": False,
                  "output_exhausted": False, "stdout": "", "stderr": "", "error": type(error).__name__ + ": " + str(error)[:300],
                  "duration_s": 0.0}
    report["steps"].append(record)
    if step.get("stop_on_failure") and record.get("exit_code") != 0:
        report["stopped_early"] = True
        break
sys.stdout.write(MARK_BEGIN + "\n" + json.dumps(report) + "\n" + MARK_END + "\n")
sys.stdout.flush()
'''.replace("MARK_BEGIN", repr(MARK_BEGIN)).replace("MARK_END", repr(MARK_END))


class SandboxError(RuntimeError):
    def __init__(self, message: str, uncertain: bool = False, unreachable: bool = False, accepted_unread: bool = False,
                 operation_uuid: str | None = None, rejected: bool = False, journal_failed: bool = False, halted: bool = False,
                 http_status: int | None = None, op_id: str | None = None):
        super().__init__(message)
        self.uncertain = uncertain or accepted_unread  # the operation may exist or may have run: never replayed
        self.unreachable = unreachable  # every attempt failed before any byte of the request was sent: nothing exists
        self.accepted_unread = accepted_unread  # accepted (operation_uuid known), outcome not read
        self.operation_uuid = operation_uuid
        self.rejected = rejected  # the service refused the spawn with an HTTP 4xx: nothing exists (revision 9)
        self.journal_failed = journal_failed  # a record of this operation could not be made durable: the run halts (revision 9)
        self.halted = halted  # refused, or polling stopped, because the run had halted for reconciliation (revision 9)
        self.http_status = http_status
        self.op_id = op_id

    @property
    def stops_run(self) -> bool:
        """The run sends nothing further after this error and is held for reconciliation (revision 9)."""
        return bool(self.uncertain or self.accepted_unread or self.journal_failed or self.halted)


def _decode_stream(stream: dict | None) -> tuple[str, bool]:
    stream = stream or {}
    value = stream.get("value", "") or ""
    if stream.get("encoding") == "base64":
        value = base64.b64decode(value).decode("utf-8", "replace")
    return value, bool(stream.get("truncated"))


class TokenFactorySandboxes:
    name = "tf_sandboxes"

    def __init__(self, api_key: str, project_id: str, ledger: Ledger, base_url: str = BASE,
                 uid: int = 0, gid: int = 0, max_layer_bytes: int = 268_435_456,
                 truncate_output_at: int = 2_000_000, poll_interval: float = 1.0):
        self._key = api_key
        self.project_id = project_id
        self.base = base_url.rstrip("/")
        self.ledger = ledger
        self.uid, self.gid = uid, gid
        self.max_layer_bytes = max_layer_bytes
        self.truncate_output_at = truncate_output_at
        self.poll_interval = poll_interval
        self.requests_log: list[dict] = []
        self._sleep = time.sleep  # transport waits (tests replace it)

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key, "Project": self.project_id}

    def _request(self, method: str, path: str, payload=None, timeout: float = 30, op: SandboxOp | None = None, stage: str | None = None,
                 retry_statuses: tuple[int, ...] = ()):
        """One API request with the bounded retries its method allows; every attempt is admitted by the ledger first (`RunHalted` once
        the run has stopped). GET and DELETE are idempotent here (a read, a cancel), so a transport failure or an answer that asks for
        a retry (408, 429, 5xx, plus `retry_statuses`) is retried, bounded, and the last failure is raised as it came (HttpError or
        TransportError). A POST (a spawn creates an operation) is sent again only after an attempt that failed before any byte of it was
        written; any other failure is raised for the caller to classify, and nothing is ever replayed."""
        record = {"at_utc": utcnow(), "method": method, "path": path.split("?")[0]}
        self.requests_log.append(record)
        idempotent = method in ("GET", "DELETE")
        retries = READ_RETRIES if idempotent else NOT_SENT_RETRIES
        for attempt in range(retries + 1):
            self.ledger.admit("sandboxes", stage or (op.stage if op is not None else None))
            try:
                status, body, headers = request_json(method, self.base + path, self._headers(), payload, timeout=timeout)
            except HttpError as error:
                record["http_status"] = error.status
                retryable = idempotent and (read_retryable(error) or error.status in retry_statuses)
                if not retryable or attempt == retries:
                    raise
                record["retries"] = attempt + 1
                self._sleep(retry_after_s(error) or backoff(READ_BACKOFF_S, attempt))
                continue
            except TransportError as error:
                record["transport_error"] = str(error)
                record.setdefault("transport_failures", []).append({"phase": error.phase, "request_sent": error.request_sent})
                if op is not None:  # a spawn attempt: its public text says whether it was never sent or is uncertain
                    public = self.ledger.public_error(f"{op.stage}-transport", error if not error.request_sent
                                                      else SandboxError(str(error), uncertain=True))
                    op.transport_failures.append({"at_utc": utcnow(), "phase": error.phase, "request_sent": error.request_sent,
                                                  "error": public})
                retryable = idempotent or not error.request_sent
                if not retryable or attempt == retries:
                    raise
                self._sleep(backoff(READ_BACKOFF_S if idempotent else NOT_SENT_BACKOFF_S, attempt))
                if op is not None:
                    op.attempts += 1
                continue
            record["http_status"] = status
            record["retry_after"] = headers.get("retry-after")
            if attempt:
                record["retries"] = attempt
            return body, headers
        raise SandboxError("unreachable: the retry loop always returns or raises")

    def describe(self) -> dict:
        return {"executor": self.name, "base_url": self.base, "project_id": self.project_id,
                "journal_policy": ("every operation is journaled as PENDING (fsync, read back) before its spawn is sent and its accepted id before "
                                   "the first poll; when either fails nothing further is dispatched and the run halts for reconciliation"),
                "answer_policy": ("a spawn answered HTTP 4xx is REJECTED; HTTP 5xx, a 2xx without an operation id or a failure after the spawn was "
                                  "written is UNCERTAIN and halts the run; polls are retried (bounded) and an accepted operation whose outcome "
                                  "is not read is ACCEPTED_UNREAD; nothing is sent after the run halts"),
                "operation_uid_gid": [self.uid, self.gid],
                "test_child_uid": 65534 if self.uid == 0 else self.uid,
                "privilege_separation": self.uid == 0,
                "max_layer_bytes": self.max_layer_bytes,
                "networking_enabled": False, "transport": "base64 stdin JSON job -> guest runner (root); sealed tests run per-test as uid 65534",
                "post_replay": False,
                "retry_policy": (f"GET and DELETE retried on any transport failure (at most {READ_RETRIES} times); a spawn sent again only when "
                                 f"the attempt failed before any byte of it was written (at most {NOT_SENT_RETRIES} times); an uncertain spawn is "
                                 "never sent again; accepted operation ids are journaled before polling")}

    def _read(self, path: str, stage: str | None = None, retry_statuses: tuple[int, ...] = ()) -> dict:
        """A read whose last failure becomes a definite SandboxError (it changed nothing); a stopped run raises RunHalted."""
        try:
            body, _ = self._request("GET", path, stage=stage, retry_statuses=retry_statuses)
        except (HttpError, TransportError) as error:
            raise SandboxError(f"read {path.split('?')[0]} failed: {error}", http_status=getattr(error, "status", None)) from None
        return body or {}

    def whoami(self) -> dict:
        return self._read("/whoami")

    def resolve_image(self, tag: str) -> str:
        body = self._read(f"/images?tag={tag}&limit=100", stage="resolve-image")
        matches = [i for i in (body or {}).get("images", []) if i.get("tag") == tag]
        if len(matches) != 1:
            raise SandboxError(f"expected exactly one public image tagged {tag!r}, found {len(matches)}")
        return matches[0]["uuid"]

    def get_operation(self, operation_uuid: str, stage: str | None = None) -> dict:
        """One poll; HTTP 404 is retried with the other transient answers, because a just-accepted id can be briefly unknown to reads.
        Raises the last HttpError or TransportError when every attempt failed, RunHalted once the run has stopped."""
        body, _ = self._request("GET", "/operations/" + operation_uuid, stage=stage, retry_statuses=(404,))
        return body or {}

    def cancel(self, operation_uuid: str, stage: str | None = None) -> bool:
        """Ask the service to stop an operation (idempotent). Returns whether the request was answered; a stopped run sends nothing."""
        try:
            self._request("DELETE", "/operations/" + operation_uuid, stage=stage)  # idempotent: a repeated cancel changes nothing
            return True
        except (HttpError, TransportError, RunHalted, SandboxError):
            return False

    def _wait(self, operation_uuid: str, deadline_s: float, stage: str | None = None) -> dict:
        """Poll an accepted operation until it is terminal. Past the deadline it is cancelled and polled a little longer; one that is
        still not terminal raises SandboxError(accepted_unread) and the caller keeps its id for reconciliation."""
        deadline = time.monotonic() + deadline_s
        while time.monotonic() < deadline:
            data = self.get_operation(operation_uuid, stage)
            if data.get("status") in TERMINAL:
                return data
            retry_after = self.requests_log[-1].get("retry_after")
            try:
                delay = max(self.poll_interval, float(retry_after)) if retry_after else self.poll_interval
            except ValueError:
                delay = self.poll_interval
            self._sleep(min(delay, max(0.0, deadline - time.monotonic())))
        self.cancel(operation_uuid, stage)
        for _ in range(15):
            data = self.get_operation(operation_uuid, stage)
            if data.get("status") in TERMINAL:
                return data
            self._sleep(1)
        raise SandboxError(f"operation {operation_uuid} did not reach a terminal state after cancellation; reconcile with GET "
                           f"/operations/{operation_uuid}", accepted_unread=True, operation_uuid=operation_uuid)

    @staticmethod
    def _operation(op: SandboxOp) -> dict:
        return {"service": "sandboxes", "op_id": op.op_id, "operation_uuid": op.operation_uuid, "image_uuid": op.image_uuid,
                "status": op.status, "started_at_utc": op.started_at_utc}

    def _settle(self, op: SandboxOp, status: str, note: str | None = None, halt: str | None = None, detail: str | None = None) -> None:
        """Record a final or unknown outcome of `op`: the state in memory first, then (for an unknown outcome, `halt`) the run's halt
        with this cause, then the journal line. A journal that cannot take the line halts the run as well (the in-memory record keeps
        the state, and the halt record names the operation)."""
        op.status = status
        op.outcome_note = note
        op.ended_at_utc = utcnow()
        if halt:
            self.ledger.halt("uncertain_operation", halt, stage=op.stage, operation=self._operation(op), detail=detail)
        try:
            self.ledger.update_op(op)
        except LedgerError as error:
            self.ledger.halt("journal_failure", f"the {status} state of the {op.stage} sandbox operation could not be journaled",
                             stage=op.stage, operation=self._operation(op), detail=str(error))

    @staticmethod
    def encode_job(job: dict) -> str:
        """gzip + base64 text of the job (what the request carries); the guest runner detects the gzip magic."""
        return base64.b64encode(gzip.compress(json.dumps(job).encode("utf-8"), 6)).decode("ascii")

    def _execute(self, image: str, job: dict, stage: str, disposable: bool, timeout: int,
                 networking: bool = False) -> RunResult:
        stdin_value = self.encode_job(job)
        if len(stdin_value) > MAX_REQUEST_BYTES:
            raise SandboxError(f"sandbox request for stage {stage!r} would be {len(stdin_value)} bytes after compression; the API accepts about "
                               f"{MAX_REQUEST_BYTES} bytes per request (measured limit), so the files of this operation must be reduced or chained")
        payload = {
            "command": "/usr/local/bin/python", "args": ["-c", GUEST_RUNNER], "image": image, "shell": False,
            "uid": self.uid, "gid": self.gid, "cwd": "/tmp", "env": dict(GUEST_ENV), "preserve_env": False,
            "stdin": {"value": stdin_value, "encoding": "base64", "close": True},
            "timeout": timeout, "truncate_output_at": self.truncate_output_at,
            "networking": {"enabled": bool(networking)},
            "resources_limits": {"max_layer_bytes": self.max_layer_bytes},
            "disposable": disposable,
        }
        op = SandboxOp(stage=stage, operation_uuid=None, image_uuid=image, result_image_uuid=None,
                       disposable=disposable, networking_enabled=bool(networking), status=None, exit_code=None,
                       timed_out=None, signal=None, duration_s=None, raw_cost_diag=None, stdout_truncated=None,
                       started_at_utc=utcnow())
        try:
            self.ledger.add_op(op)  # PENDING, durable and read back, before any byte of the spawn is sent (revision 9)
        except LedgerError as error:
            self.ledger.halt("journal_failure", f"the pending record of the {stage} sandbox operation could not be journaled; nothing was dispatched",
                             stage=stage, detail=str(error),
                             operation={"service": "sandboxes", "op_id": op.op_id, "image_uuid": image, "started_at_utc": op.started_at_utc,
                                        "dispatched": False})
            raise SandboxError(f"the {stage} sandbox operation was not dispatched: its pending record could not be journaled ({error})",
                               journal_failed=True, op_id=op.op_id) from None
        try:
            accepted, _ = self._request("POST", "/instances", payload, timeout=60, op=op)
        except RunHalted as halted:
            # the run stopped (a parallel branch) after this operation was journaled and before its first attempt: nothing was sent
            self._settle(op, "NOT_SENT", note="not sent: the run had stopped for reconciliation")
            raise SandboxError(f"the {stage} sandbox operation was not sent: {halted}", halted=True, op_id=op.op_id) from None
        except (TransportError, HttpError) as error:
            outcome = post_outcome(error)
            op.http_status = getattr(error, "status", None)
            if outcome == "not_sent":
                self._settle(op, "NOT_SENT", note="no attempt got as far as sending the spawn")
                raise SandboxError(f"the sandbox service could not be reached: {op.attempts} attempt(s), none got as far as sending the "
                                   f"spawn ({error})", unreachable=True, op_id=op.op_id) from None
            if outcome == "rejected":
                self._settle(op, "REJECTED", note=f"the service refused the spawn (HTTP {op.http_status})")
                raise SandboxError(f"the sandbox service refused the {stage} spawn: {error}", rejected=True, http_status=op.http_status,
                                   op_id=op.op_id) from None
            self._settle(op, "UNCERTAIN", note=("the spawn was answered HTTP %s after it was sent" % op.http_status) if isinstance(error, HttpError)
                         else f"the spawn's answer was lost after it was sent ({error.phase} phase)",
                         halt=f"the outcome of the {stage} spawn is uncertain: {self.ledger.public_error(f'{stage}-spawn', SandboxError(str(error), uncertain=True, http_status=op.http_status))}; "
                              "it was not sent again", detail=str(error))
            raise SandboxError(f"spawn outcome uncertain ({error}); inspect account operations, do not replay", uncertain=True,
                               http_status=op.http_status, op_id=op.op_id) from None
        op.operation_uuid = (accepted or {}).get("uuid")
        if not op.operation_uuid:
            # a success answer without an id: an operation may exist, and nothing identifies it
            self._settle(op, "UNCERTAIN", note="the spawn was answered without an operation id; an operation may exist",
                         halt=f"the {stage} spawn was answered without an operation id; an operation may exist")
            raise SandboxError("spawn response had no operation uuid; an operation may exist: inspect account operations, do not replay",
                               uncertain=True, op_id=op.op_id)
        op.status = "ACCEPTED"
        try:
            self.ledger.update_op(op)  # the accepted id is durable before polling starts, so no interruption can lose it
        except LedgerError as error:
            self.ledger.halt("journal_failure", f"operation {op.operation_uuid} ({stage}) was accepted but its id could not be journaled; it was "
                                                "not polled", stage=stage, operation=self._operation(op), detail=str(error))
            raise SandboxError(f"operation {op.operation_uuid} was accepted but its id could not be journaled ({error}); it was not polled; "
                               f"reconcile with GET /operations/{op.operation_uuid}", accepted_unread=True, journal_failed=True,
                               operation_uuid=op.operation_uuid, op_id=op.op_id) from None
        try:
            result = self._wait(op.operation_uuid, deadline_s=timeout + 90, stage=stage)
        except (TransportError, HttpError, SandboxError, RunHalted) as error:
            # the polls failed even after their retries, the operation never reached a terminal state, or the run stopped while it
            # was being polled: it exists and may still run; it is never spawned again
            stopped = isinstance(error, RunHalted)
            note = ("polling stopped: the run halted for reconciliation" if stopped else f"its outcome could not be read ({type(error).__name__})")
            self._settle(op, "ACCEPTED_UNREAD", note=note,
                         halt=None if stopped else f"operation {op.operation_uuid} ({stage}) was accepted but {note}; it was not spawned again",
                         detail=str(error))
            raise SandboxError(f"operation {op.operation_uuid} was accepted but {note}; reconcile with GET /operations/{op.operation_uuid}; "
                               "not replayed", accepted_unread=True, halted=stopped, operation_uuid=op.operation_uuid, op_id=op.op_id) from None
        execution = (result.get("metadata") or {}).get("result") or {}
        state = execution.get("state") or {}
        stdout, stdout_truncated = _decode_stream(execution.get("stdout"))
        stderr, _ = _decode_stream(execution.get("stderr"))
        op.status = result.get("status")
        op.exit_code = state.get("exit_code")
        op.timed_out = state.get("timed_out")
        op.signal = state.get("signal")
        op.duration_s = result.get("duration")
        op.result_image_uuid = result.get("result_image_uuid") or ((result.get("result") or {}).get("image"))
        op.raw_cost_diag = (execution.get("resources") or {}).get("cost")
        op.stdout_truncated = stdout_truncated
        op.ended_at_utc = utcnow()
        try:
            self.ledger.update_op(op)
        except LedgerError as error:
            # the outcome is known here but not durable: the run goes no further
            self.ledger.halt("journal_failure", f"the final state of operation {op.operation_uuid} ({stage}) could not be journaled",
                             stage=stage, operation=self._operation(op), detail=str(error))
            raise SandboxError(f"the final state of operation {op.operation_uuid} could not be journaled ({error}); the run stops",
                               journal_failed=True, operation_uuid=op.operation_uuid, op_id=op.op_id) from None
        run = RunResult(stage=stage, operation_uuid=op.operation_uuid, status=op.status, exit_code=op.exit_code,
                        timed_out=op.timed_out, signal=op.signal, duration_s=op.duration_s, image_uuid=image,
                        result_image_uuid=op.result_image_uuid, stdout_truncated=stdout_truncated,
                        raw_stdout_excerpt=stdout[:2000], raw_stderr_excerpt=stderr[:2000])
        if op.status != "SUCCESS":
            run.runner_error = f"operation status {op.status}: {result.get('error')}"
            return run
        begin, end = stdout.find(MARK_BEGIN), stdout.rfind(MARK_END)
        if begin < 0 or end < 0 or stdout_truncated:
            run.runner_error = "guest report markers missing or output truncated"
            return run
        try:
            report = json.loads(stdout[begin + len(MARK_BEGIN):end].strip())
        except json.JSONDecodeError as error:
            run.runner_error = f"guest report unparsable: {error}"
            return run
        for record in report.get("steps", []):
            error = record.get("error")
            if record.get("output_exhausted") and not error:
                error = (f"output exhausted: the step wrote more than the guest's output limit (stdout {record.get('stdout_bytes')} bytes, "
                         f"stderr {record.get('stderr_bytes')} bytes) and its process group was killed")
            run.steps.append(StepResult(name=record.get("name") or "", cmd=record.get("cmd") or [],
                                        exit_code=record.get("exit_code"), timed_out=bool(record.get("timed_out")),
                                        duration_s=record.get("duration_s"), stdout=record.get("stdout") or "",
                                        stderr=record.get("stderr") or "", error=error))
        return run

    @staticmethod
    def _job(files: dict[str, bytes], steps: list[dict], deletes: list[str] | None = None) -> dict:
        return {"write": {path: base64.b64encode(data).decode("ascii") for path, data in files.items()},
                "delete": list(deletes or []), "steps": steps, "stream_cap_bytes": 65536, "output_limit_bytes": 64_000_000}

    def plan_chunks(self, files: dict[str, bytes]) -> list[dict[str, bytes]]:
        """Split the files into groups whose encoded job fits one request (halving by sorted path until it fits)."""
        if len(self.encode_job(self._job(files, []))) <= MAX_REQUEST_BYTES or len(files) <= 1:
            if files and len(self.encode_job(self._job(files, []))) > MAX_REQUEST_BYTES:
                path = next(iter(files))
                raise SandboxError(f"{path} alone ({len(files[path])} bytes) exceeds the sandbox request limit of about {MAX_REQUEST_BYTES} bytes after compression")
            return [files] if files else [{}]
        keys = sorted(files)
        half = len(keys) // 2
        return self.plan_chunks({k: files[k] for k in keys[:half]}) + self.plan_chunks({k: files[k] for k in keys[half:]})

    def create_checkpoint(self, image: str, files: dict[str, bytes], steps: list[dict], stage: str,
                          timeout: int = 120, networking: bool = False) -> RunResult:
        """Retained checkpoint. When the repository does not fit in one request, earlier chunks are written by their own
        retained operations (no steps, networking off) and the final operation adds the last chunk and runs the steps."""
        chunks = self.plan_chunks(files)
        chain: list[str] = []
        current = image
        for index, chunk in enumerate(chunks[:-1]):
            run = self._execute(current, self._job(chunk, []), f"{stage}-files-{index + 1}", disposable=False, timeout=min(timeout, 180))
            if not run.ok or not run.result_image_uuid:
                run.runner_error = run.runner_error or f"checkpoint chunk {index + 1} of {len(chunks)} returned no retained image"
                run.chain = chain
                return run
            chain.append(run.operation_uuid or "")
            current = run.result_image_uuid
        run = self._execute(current, self._job(chunks[-1], steps), stage, disposable=False, timeout=timeout, networking=networking)
        run.chain = chain
        if run.ok and not run.result_image_uuid:
            run.runner_error = "checkpoint operation returned no retained image"
        return run

    def run_branch(self, image: str, files: dict[str, bytes], steps: list[dict], stage: str,
                   deletes: list[str] | None = None, timeout: int = 120, networking: bool = False) -> RunResult:
        return self._execute(image, self._job(files, steps, deletes), stage, disposable=True, timeout=timeout,
                             networking=networking)
