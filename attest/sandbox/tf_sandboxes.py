"""Nebius Token Factory Sandboxes (ConTree) REST adapter.

Verified primitives (2026-10-15 smoke): POST /instances, GET /operations/{id},
retained checkpoints, disposable branches, networking.enabled=false.

Transport of inputs: a JSON job is gzip-compressed and sent as base64 stdin to a
small guest runner (Python, stdlib only) that writes files, runs steps with
subprocess, and prints a marker-delimited JSON report. Accepted operation UUIDs
are recorded before polling and a POST is never replayed.

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
"""

from __future__ import annotations

import base64
import gzip
import json
import time

from ..http import HttpError, TransportError, request_json
from ..ledger import Ledger, SandboxOp, utcnow
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
    pass


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

    def _headers(self) -> dict:
        return {"Authorization": "Bearer " + self._key, "Project": self.project_id}

    def _request(self, method: str, path: str, payload=None, timeout: float = 30):
        record = {"at_utc": utcnow(), "method": method, "path": path.split("?")[0]}
        self.requests_log.append(record)
        # Idempotent GETs (image lookup, operation polling) may be retried on a transient transport failure; a POST that
        # creates a sandbox instance is NEVER retried (the no-replay rule), so an uncertain spawn stays uncertain.
        attempts = 3 if method == "GET" else 1
        last: TransportError | None = None
        for attempt in range(attempts):
            try:
                status, body, headers = request_json(method, self.base + path, self._headers(), payload, timeout=timeout)
            except HttpError as error:
                record["http_status"] = error.status
                raise SandboxError(str(error)) from None
            except TransportError as error:
                last = error
                record["transport_error"] = str(error)
                if method != "GET" or attempt == attempts - 1:
                    raise
                time.sleep(1.0 * (attempt + 1))
                continue
            record["http_status"] = status
            record["retry_after"] = headers.get("retry-after")
            if attempt:
                record["get_retries"] = attempt
            return body, headers
        raise last  # unreachable: GET either returned or re-raised on the last attempt

    def describe(self) -> dict:
        return {"executor": self.name, "base_url": self.base, "project_id": self.project_id,
                "operation_uid_gid": [self.uid, self.gid],
                "test_child_uid": 65534 if self.uid == 0 else self.uid,
                "privilege_separation": self.uid == 0,
                "max_layer_bytes": self.max_layer_bytes,
                "networking_enabled": False, "transport": "base64 stdin JSON job -> guest runner (root); sealed tests run per-test as uid 65534",
                "post_replay": False}

    def whoami(self) -> dict:
        body, _ = self._request("GET", "/whoami")
        return body or {}

    def resolve_image(self, tag: str) -> str:
        body, _ = self._request("GET", f"/images?tag={tag}&limit=100")
        matches = [i for i in (body or {}).get("images", []) if i.get("tag") == tag]
        if len(matches) != 1:
            raise SandboxError(f"expected exactly one public image tagged {tag!r}, found {len(matches)}")
        return matches[0]["uuid"]

    def get_operation(self, operation_uuid: str) -> dict:
        body, _ = self._request("GET", "/operations/" + operation_uuid)
        return body or {}

    def cancel(self, operation_uuid: str) -> None:
        try:
            self._request("DELETE", "/operations/" + operation_uuid)
        except (SandboxError, TransportError):
            pass

    def _wait(self, operation_uuid: str, deadline_s: float) -> dict:
        deadline = time.monotonic() + deadline_s
        while time.monotonic() < deadline:
            data = self.get_operation(operation_uuid)
            if data.get("status") in TERMINAL:
                return data
            retry_after = self.requests_log[-1].get("retry_after")
            try:
                delay = max(self.poll_interval, float(retry_after)) if retry_after else self.poll_interval
            except ValueError:
                delay = self.poll_interval
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
        self.cancel(operation_uuid)
        for _ in range(15):
            data = self.get_operation(operation_uuid)
            if data.get("status") in TERMINAL:
                return data
            time.sleep(1)
        raise SandboxError(f"operation {operation_uuid} did not reach a terminal state after cancellation")

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
        self.ledger.add_op(op)
        try:
            accepted, _ = self._request("POST", "/instances", payload, timeout=60)
        except TransportError as error:
            op.status = "UNCERTAIN"
            raise SandboxError(f"spawn outcome uncertain ({error}); inspect account operations, do not replay") from None
        op.operation_uuid = (accepted or {}).get("uuid")
        if not op.operation_uuid:
            op.status = "REJECTED"
            raise SandboxError("spawn response had no operation uuid")
        result = self._wait(op.operation_uuid, deadline_s=timeout + 90)
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
