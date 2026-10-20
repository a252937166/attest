#!/usr/bin/env python3
"""Reproduction of the six defects named in the revision-10 instruction (20 Oct 2026), offline, against any package tree.

    python reproduce_r10.py --tree <checkout> --out <result.json>

The tree's own `attest` package and `tests` helpers are imported (tests/__init__ installs the offline guard: credentials removed,
every connection outside the loopback interface refused). Every scenario uses only interfaces both 0.9.0 and the repaired version
have (the store, the worker, the console's start-up path, the harness, the adapters), so the same script shows each failure on
0.9.0 and the repaired behaviour afterwards. Faults are injected from outside the code under test: SQLite triggers on the `holds`
table (a refused insert, or a process that dies inside the statement), and a local HTTP server that answers malformed bodies to
the real HTTP client and adapters.

A  restart with a proof bundle present: the bundle's reconciliation record (and the journal) must be inspected and the hold kept
B  the failed-run record and its hold: atomic, fail-closed, repaired at start-up, idempotent, a cleared hold never reopened
C  batch resume: completed and halted rows, bundles and journals inspected; a note tied to item ids, kept across restarts
D  malformed upstream answers through the real HTTP client: UNCERTAIN / ACCEPTED_UNREAD, halt, nothing sent afterwards
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

RESULTS: list[dict] = []


def check(scenario: str, label: str, ok: bool, observed: str = "") -> bool:
    RESULTS.append({"scenario": scenario, "check": label, "ok": bool(ok), "observed": observed[:600]})
    print(f"[{scenario}] {'PASS' if ok else 'FAIL'}  {label}" + (f"  (observed: {observed[:300]})" if observed else ""), flush=True)
    return bool(ok)


def guarded(scenario: str, label: str):
    """Decorator: an exception inside a scenario is a FAIL of that scenario (with the exception), never an abort of the script."""
    def wrap(fn):
        def run(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except BaseException as error:  # noqa: BLE001
                if isinstance(error, KeyboardInterrupt):
                    raise
                check(scenario, label + " (scenario raised)", False, f"{type(error).__name__}: {error}; {traceback.format_exc()[-400:]}")
                return None
        return run
    return wrap


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args, **kwargs)


def tmpdir(prefix="r10-") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


# ---------------------------------------------------------------------------------------------------------------- shared fakes
def fakes(tree: Path):
    from tests.test_verification import FakeExecutor, FakeProvider, TASK  # the tree's own offline fakes
    from attest.sandbox.tf_sandboxes import SandboxError

    class Recorder:
        def __init__(self):
            self.items, self.stop = [], None

        def add(self, kind, stage):
            self.items.append((kind, stage))
            return len(self.items) - 1

    class RecordingProvider:
        def __init__(self, inner, requests):
            self.inner, self.requests, self.name, self.ledger = inner, requests, inner.name, inner.ledger

        def describe(self):
            return self.inner.describe()

        def structured(self, role, prompt, schema, stage):
            self.requests.add("model", stage)
            return self.inner.structured(role, prompt, schema, stage)

    class StoppingExecutor(FakeExecutor):
        """The tree's FakeExecutor; the first operation whose stage matches `predicate` raises an uncertain SandboxError, or is
        delegated to `delegate` (a real adapter talking to the local HTTP server)."""

        def __init__(self, ledger, requests, predicate, delegate=None):
            super().__init__(ledger, "honest")
            self.requests, self.predicate, self.delegate, self.raised = requests, predicate, delegate, False

        def _gate(self, stage):
            index = self.requests.add("sandbox", stage)
            if not self.raised and self.predicate(stage):
                self.raised, self.requests.stop = True, index
                return True
            return False

        def create_checkpoint(self, image, files, steps, stage, timeout=120, networking=False):
            if self._gate(stage):
                raise SandboxError("spawn outcome uncertain (RemoteDisconnected); inspect account operations, do not replay", uncertain=True)
            return super().create_checkpoint(image, files, steps, stage, timeout, networking)

        def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
            if self._gate(stage):
                if self.delegate is not None:
                    return self.delegate.run_branch(image, files, steps, stage=stage, deletes=deletes, timeout=timeout)
                raise SandboxError("spawn outcome uncertain (RemoteDisconnected); inspect account operations, do not replay", uncertain=True)
            return super().run_branch(image, files, steps, stage, deletes, timeout, networking)

    return FakeProvider, FakeExecutor, TASK, Recorder, RecordingProvider, StoppingExecutor


def halted_run(tree: Path, runs_dir: Path, run_id: str, stage_prefix: str = "verify"):
    """An offline pipeline run that stops at an uncertain sandbox operation: its run directory holds a halted proof bundle."""
    from attest.core.pipeline import Pipeline
    from attest.core.task import TaskSpec
    from attest.ledger import Ledger
    FakeProvider, _, TASK, Recorder, RecordingProvider, StoppingExecutor = fakes(tree)
    ledger, requests = Ledger(), Recorder()
    provider = RecordingProvider(FakeProvider(ledger, "honest"), requests)
    executor = StoppingExecutor(ledger, requests, lambda s: s.startswith(stage_prefix))
    pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=executor, ledger=ledger, out_dir=runs_dir, max_turns=6,
                        max_mutants=6, mutant_workers=1, tavily=None, profile_label="development", run_id=run_id)
    bundle = quiet(pipeline.run)
    return bundle, pipeline


def console_row(store, run_id: str, status: str = "running", out_dir: str | None = None):
    from attest.ledger import utcnow
    store.create_run(run_id=run_id, task_id="durationkit-units-001", task_title="T", provider="codex", profile_label="development",
                     status=status, stage="queued" if status == "queued" else "verify", created_at=utcnow(), requester="team",
                     out_dir=out_dir)


def restart(data_dir: Path, examples: Path):
    """The console's real start-up path: a fresh import of attest.app.server against the data directory (import, dedupe and the
    restart recovery run at module level), with the worker stopped right after."""
    env = {"ATTEST_DATA_DIR": str(data_dir), "ATTEST_EXAMPLES_DIR": str(examples), "ATTEST_ADMIN_TOKEN": "synthetic-team-token",
           "ATTEST_IMPORT_DIRS": str(data_dir / "runs")}
    with mock.patch.dict(os.environ, env):
        import attest.app.server as server
        server = quiet(importlib.reload, server)
        server.worker.stop()
    return server


def holds_of(db: Path, run_id: str | None = None) -> list[tuple]:
    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute("SELECT hold_id, run_id, cleared_at FROM holds" + (" WHERE run_id = ?" if run_id else ""), (run_id,) if run_id else ()).fetchall()
    finally:
        conn.close()
    return rows


def row_of(db: Path, run_id: str) -> dict:
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT status, error_code, verdict, stage FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else {}


# ---------------------------------------------------------------------------------------------------------------- A
@guarded("A", "restart with a halted proof bundle")
def scenario_a(tree: Path):
    from attest.app.db import Store
    examples = tree / "examples"
    data = tmpdir("r10-a-")
    bundle, pipeline = halted_run(tree, data / "runs", "a1-halted-run")
    check("A", "the offline run left a halted bundle requiring reconciliation", bool((bundle.get("reconciliation") or {}).get("required")),
          f"verdict {bundle['verdict']['verdict']}, items {len((bundle.get('reconciliation') or {}).get('items') or [])}")
    store = Store(data / "attest.db")
    console_row(store, "a1-halted-run", "running", str(pipeline.out_dir))  # the process died after the bundle, before the row update
    server = restart(data, examples)
    row = row_of(data / "attest.db", "a1-halted-run")
    holds = [h for h in holds_of(data / "attest.db", "a1-halted-run") if h[2] is None]
    check("A", "after the restart the run is recorded as reconciliation_required (not finished)", row.get("error_code") == "reconciliation_required",
          f"row {row}")
    check("A", "after the restart the run's hold is open", len(holds) == 1, f"{len(holds)} open hold(s) for the run")
    from fastapi.testclient import TestClient
    accepting = TestClient(server.app).get("/api/health").json().get("reconciliation", {}).get("accepting_runs")
    check("A", "the console refuses new runs (health: accepting_runs false)", accepting is False, f"accepting_runs {accepting}")
    # control: a run that died before any bundle, with the halt only in its journal (both versions already hold it)
    data2 = tmpdir("r10-a2-")
    bundle2, pipeline2 = halted_run(tree, data2 / "runs", "a2-journal-only")
    (pipeline2.out_dir / "proof_bundle.json").unlink()
    store2 = Store(data2 / "attest.db")
    console_row(store2, "a2-journal-only", "running", str(pipeline2.out_dir))
    restart(data2, examples)
    holds2 = [h for h in holds_of(data2 / "attest.db", "a2-journal-only") if h[2] is None]
    check("A", "control: with no bundle the journal alone keeps the hold", len(holds2) == 1, f"{len(holds2)} open hold(s)")


# ---------------------------------------------------------------------------------------------------------------- B
def worker_for(tree: Path, data: Path, store, stops: dict):
    """A worker whose loop does not run (items are fed to `_run_one`), with fake runtimes; `built` lists the runs that got one."""
    from attest.app.worker import Worker
    FakeProvider, _, TASK, Recorder, RecordingProvider, StoppingExecutor = fakes(tree)
    with mock.patch.object(Worker, "_loop", lambda self: None):
        worker = Worker(store, data, tree / "examples", max_turns=6)
    built: list[str] = []

    def build(run_id, provider_name, ledger):
        built.append(run_id)
        requests = Recorder()
        predicate = stops.get(run_id, lambda s: False)
        return RecordingProvider(FakeProvider(ledger, "honest"), requests), StoppingExecutor(ledger, requests, predicate), None
    worker.build_runtime = build
    return worker, built, TASK


def feed(worker, run_id: str, task: Path):
    item = (run_id, task, "codex", "development")
    worker.queue.put(item)
    worker.queue.get()
    quiet(worker._run_one, item)


@guarded("B", "a refused hold insert")
def scenario_b_failed_insert(tree: Path):
    from attest.app.db import Store
    data = tmpdir("r10-b1-")
    store = Store(data / "attest.db")
    console_row(store, "b1-first", "queued")
    console_row(store, "b1-second", "queued")
    conn = sqlite3.connect(str(data / "attest.db"))
    conn.execute("CREATE TRIGGER fail_hold BEFORE INSERT ON holds BEGIN SELECT RAISE(FAIL, 'injected: database or disk is full'); END")
    conn.commit()
    conn.close()
    worker, built, task = worker_for(tree, data, store, {"b1-first": lambda s: s == "verify"})
    feed(worker, "b1-first", task)
    feed(worker, "b1-second", task)
    first = row_of(data / "attest.db", "b1-first")
    check("B", "a refused hold insert: no further run is started by the worker", "b1-second" not in built, f"runtimes built for {built}")
    check("B", "a refused hold insert: the run is not left recorded as reconciliation_required without its hold",
          not (first.get("error_code") == "reconciliation_required" and not holds_of(data / "attest.db", "b1-first")), f"row {first}, holds {holds_of(data / 'attest.db', 'b1-first')}")
    refused = False
    try:
        with mock.patch.object(worker, "ensure_alive", return_value=True):
            worker.enqueue("durationkit-units-001", "codex", "team", "development")
    except Exception as error:  # noqa: BLE001
        refused = True
        reason = f"{type(error).__name__}: {error}"
    else:
        reason = "admitted"
    check("B", "a refused hold insert: admission is refused while the hold is not recorded (fail closed)", refused, reason)
    conn = sqlite3.connect(str(data / "attest.db"))
    conn.execute("DROP TRIGGER fail_hold")
    conn.commit()
    conn.close()
    worker.stop()
    restart(data, tree / "examples")
    holds = holds_of(data / "attest.db", "b1-first")
    check("B", "after the fault is gone and the service restarts, the run's hold exists exactly once", len(holds) == 1 and holds[0][2] is None,
          f"holds {holds}; row {row_of(data / 'attest.db', 'b1-first')}")


DIE_CHILD = r'''
import os, sqlite3, sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, sys.argv[1])
import tests  # the offline guard
sys.path.insert(0, sys.argv[3])
import reproduce_r10 as r
from attest.app.db import Store
data = Path(sys.argv[2])
store = Store(data / "attest.db")
store._conn.create_function("die", 0, lambda: os._exit(9))
worker, built, task = r.worker_for(Path(sys.argv[1]), data, store, {"b2-first": lambda s: s == "verify"})
r.feed(worker, "b2-first", task)
print("NOT KILLED")
'''


@guarded("B", "a process killed inside the record")
def scenario_b_killed(tree: Path):
    from attest.app.db import Store
    data = tmpdir("r10-b2-")
    store = Store(data / "attest.db")
    console_row(store, "b2-first", "queued")
    conn = sqlite3.connect(str(data / "attest.db"))
    conn.execute("CREATE TRIGGER die_on_hold BEFORE INSERT ON holds BEGIN SELECT die(); END")
    conn.commit()
    conn.close()
    del store
    child = subprocess.run([sys.executable, "-c", DIE_CHILD, str(tree), str(data), str(Path(__file__).resolve().parent)],
                           capture_output=True, text=True, timeout=300, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    check("B", "the injected kill happened inside the hold insert", child.returncode == 9, f"exit {child.returncode}; {child.stderr[-300:]}")
    after_kill = row_of(data / "attest.db", "b2-first")
    conn = sqlite3.connect(str(data / "attest.db"))
    conn.execute("DROP TRIGGER die_on_hold")
    conn.commit()
    conn.close()
    restart(data, tree / "examples")
    holds = holds_of(data / "attest.db", "b2-first")
    check("B", "after a kill between the row update and the hold, the restart restores the hold", len([h for h in holds if h[2] is None]) == 1,
          f"row right after the kill {after_kill}; holds after restart {holds}")
    restart(data, tree / "examples")
    holds = holds_of(data / "attest.db", "b2-first")
    check("B", "a second restart (repeated recovery) leaves exactly one hold", len(holds) == 1, f"holds {holds}")
    # an operator clears it; restarts never reopen it
    store = Store(data / "attest.db")
    open_holds = [h for h in store.holds(active_only=True) if h.get("run_id") == "b2-first"]
    if open_holds:
        store.clear_hold(open_holds[0]["hold_id"], "reconciled: the account lists no operation for the spawn (offline reproduction)")
    restart(data, tree / "examples")
    restart(data, tree / "examples")
    holds = holds_of(data / "attest.db", "b2-first")
    check("B", "a hold the operator cleared is not reopened by later restarts", bool(open_holds) and len(holds) == 1 and holds[0][2] is not None,
          f"holds {holds}")


@guarded("B", "start-up repair of a recorded run without its hold")
def scenario_b_repair(tree: Path):
    from attest.app.db import Store
    data = tmpdir("r10-b3-")
    bundle, pipeline = halted_run(tree, data / "runs", "b3-held")
    store = Store(data / "attest.db")
    console_row(store, "b3-held", "running", str(pipeline.out_dir))
    # the state 0.9.0 leaves when its process stops between record_failure and add_hold
    store.update_run("b3-held", status="error", error_code="reconciliation_required", error="stopped for reconciliation", stage="reconciliation")
    restart(data, tree / "examples")
    holds = holds_of(data / "attest.db", "b3-held")
    check("B", "start-up repairs the missing hold of a run recorded as reconciliation_required", len(holds) == 1 and holds[0][2] is None, f"holds {holds}")


# ---------------------------------------------------------------------------------------------------------------- C
def harness(tree: Path):
    spec = importlib.util.spec_from_file_location(f"run_evaluation_{abs(hash(str(tree)))}", tree / "scripts" / "run_evaluation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def batch(tree: Path, out: Path, h) -> None:
    args = h.parse_args(["--register-only", "--out", str(out), "--tasks", "durationkit-units-001", "--systems", "baseline,attest", "--attempts", "2",
                         "--snapshot-root", str(tree), "--source-root", str(tree)])
    with mock.patch.object(h, "codex_governor", lambda: None):
        code = quiet(h.run_batch, args)
    if code != 0:
        raise RuntimeError(f"register-only exited {code}")


def resume(tree: Path, out: Path, h, extra: list[str], stops=None) -> tuple[int | None, list, str]:
    FakeProvider, FakeExecutor, TASK, Recorder, RecordingProvider, StoppingExecutor = fakes(tree)
    built: list = []

    def build(name, ledger, usd_cap, max_calls, notify=None):
        built.append(name)
        return FakeProvider(ledger, "honest")

    def executor(ledger):
        return StoppingExecutor(ledger, Recorder(), stops or (lambda s: False))
    out_text = io.StringIO()
    code = None
    try:
        args = h.parse_args(["--resume", str(out), "--snapshot-root", str(tree), "--source-root", str(tree)] + extra)
        with mock.patch.object(h, "codex_governor", lambda: None), mock.patch.object(h, "build_provider", build), \
             mock.patch.object(h, "executor_for", executor), contextlib.redirect_stdout(out_text), contextlib.redirect_stderr(out_text):
            code = h.run_batch(args)
    except SystemExit as error:
        code = f"SystemExit({error.code})"
    return code, built, out_text.getvalue()


def completed_row(cell: dict, bundle: dict, out_dir: Path) -> dict:
    record = bundle.get("reconciliation") or {}
    return {**cell, "status": "completed", "verdict": bundle["verdict"]["verdict"], "accepted": False, "held_out_correct": None, "judge_passed": None,
            "reconciliation": record.get("items") or [], "halted": record.get("halt"), "uncertain": True, "infra_error": True, "cost_usd": None,
            "cost_committed_usd": 0.0, "wall_s": 1.0, "out_dir": str(out_dir), "run_id": bundle["run_id"], "confusion": "infra_error",
            "revision_digest": None, "provider_profile": None}


@guarded("C", "batch resume")
def scenario_c(tree: Path):
    h = harness(tree)
    out = tmpdir("r10-c-") / "batch"
    batch(tree, out, h)
    schedule = json.loads((out / "schedule.json").read_text(encoding="utf-8"))
    cells = schedule["cells"]
    attest_cell = next(c for c in cells if c["system"] == "attest")
    bundle, pipeline = halted_run(tree, out / "runs", f"durationkit-units-001-attest-a{attest_cell['attempt']}-halted", stage_prefix="mutant-")
    row = completed_row(attest_cell, bundle, pipeline.out_dir)
    (out / "evaluation.json").write_text(json.dumps({"schedule": schedule, "rows": [row], "interrupted": []}, indent=2), encoding="utf-8")
    # C1: a completed row whose run halted for reconciliation; --resume alone must start nothing
    code, built, text = resume(tree, out, h, [])
    check("C", "--resume alone over a completed, halted row starts no cell", built == [], f"exit {code}; providers built {len(built)}")
    # C2: an interrupted run directory (no row) whose journal leaves a spawn unresolved; a bare note must not approve it
    out2 = tmpdir("r10-c2-") / "batch"
    batch(tree, out2, h)
    from attest.ledger import JOURNAL_FILE, Ledger, SandboxOp, utcnow
    run_dir = out2 / "runs" / "durationkit-units-001-attest-a1-interrupted"
    run_dir.mkdir(parents=True)
    ledger = Ledger()
    ledger.attach_sink(run_dir / JOURNAL_FILE)
    ledger.add_op(SandboxOp(stage="mutant-m01", operation_uuid=None, image_uuid="img-1", result_image_uuid=None, disposable=True,
                            networking_enabled=False, status=None, exit_code=None, timed_out=None, signal=None, duration_s=None,
                            raw_cost_diag=None, stdout_truncated=None, started_at_utc=utcnow()))
    code, built, text = resume(tree, out2, h, ["--reconciled", "checked"])
    check("C", "a bare --reconciled NOTE (not tied to item ids) does not approve the unresolved spawn", built == [], f"exit {code}; providers built {len(built)}")
    # C3: an acknowledgement that names the items is kept across restarts; a new unresolved item blocks again
    code, built, text = resume(tree, out, h, [])
    pending = out / "reconciliation-pending.json"
    ids = [i["id"] for i in json.loads(pending.read_text(encoding="utf-8"))["items"]] if pending.is_file() else []
    check("C", "the refusal lists the unresolved items with ids", bool(ids), f"{len(ids)} id(s) listed; exit {code}")
    (out / "STOP").write_text("hold", encoding="utf-8")
    code, built, text = resume(tree, out, h, ["--reconciled", "the account lists no operation for the uncertain spawn (offline reproduction)",
                                              "--items", ",".join(ids)])
    ack = out / "reconciliations.jsonl"
    check("C", "a note tied to the listed ids is recorded durably", ack.is_file() and all(i in ack.read_text(encoding="utf-8") for i in ids) and bool(ids),
          f"exit {code}; record {'present' if ack.is_file() else 'absent'}")
    (out / "STOP").unlink()
    code, built, text = resume(tree, out, h, [], stops=lambda s: s == "verify")
    check("C", "a later restart honours the recorded acknowledgement without a new note", len(built) >= 1, f"exit {code}; providers built {len(built)}")
    code, built, text = resume(tree, out, h, [])
    check("C", "an item that appeared after the acknowledgement blocks the next resume", built == [], f"exit {code}; providers built {len(built)}")


# ---------------------------------------------------------------------------------------------------------------- D
class Server:
    """A local HTTP server with a scripted answer per request: script(method, path, n) -> (status, body bytes, mode) where mode is
    'whole' or 'cut' (a Content-Length larger than the body, then the connection closes)."""

    def __init__(self, script):
        self.script, self.seen, self.lock = script, [], threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
                with outer.lock:
                    outer.seen.append(f"{self.command} {self.path.split('?')[0]}")
                    n = len(outer.seen)
                status, body, mode = outer.script(self.command, self.path, n)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body) + (50 if mode == "cut" else 0)))
                if mode == "cut":
                    self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
                if mode == "cut":
                    self.close_connection = True

            do_GET = do_POST = do_DELETE = _answer

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base(self):
        return f"http://127.0.0.1:{self.port}/v1"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def done_record(uuid):
    report = {"runner": "attest-guest/3", "steps": [{"name": "s", "cmd": ["true"], "exit_code": 0, "timed_out": False, "stdout": "", "stderr": "", "duration_s": 0.1}]}
    stdout = "ATTEST-RESULT-BEGIN\n" + json.dumps(report) + "\nATTEST-RESULT-END\n"
    return {"uuid": uuid, "status": "SUCCESS", "duration": 0.5, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False, "signal": -1},
            "stdout": {"value": stdout}, "stderr": {"value": ""}, "resources": {"cost": 0.0001}}}}


GOOD_UUID = "01a1548b-896b-724f-85f2-6e0b92187971"
MALFORMED = [  # (label, body bytes, mode)
    ("a JSON array", b"[]", "whole"),
    ("a JSON array holding the object", json.dumps([{"uuid": GOOD_UUID}]).encode(), "whole"),
    ("a JSON string", b'"accepted"', "whole"),
    ("a JSON number", b"42", "whole"),
    ("invalid UTF-8", b'{"uuid": "\xff\xfe", "status": "PENDING"}', "whole"),
    ("not JSON", b"<html>accepted</html>", "whole"),
    ("a truncated body", b'{"uuid": "01a1548b-896b', "cut"),
]
SPAWN_ONLY = [
    ("an operation id that is a path", json.dumps({"uuid": "../../instances"}).encode(), "whole"),
    ("an operation id that is a number", json.dumps({"uuid": 12345}).encode(), "whole"),
    ("an object without an operation id", b"{}", "whole"),
]
POLL_ONLY = [
    ("a record without a status", json.dumps({"uuid": GOOD_UUID}).encode(), "whole"),
    ("a status that is not a string", json.dumps({"uuid": GOOD_UUID, "status": 7}).encode(), "whole"),
    ("an undocumented status", json.dumps({"uuid": GOOD_UUID, "status": "WEIRD"}).encode(), "whole"),
    ("a record of another operation", json.dumps({**done_record("01a1548b-0000-724f-85f2-6e0b92187971")}).encode(), "whole"),
    ("SUCCESS with a result that is a list", json.dumps({"uuid": GOOD_UUID, "status": "SUCCESS", "metadata": {"result": []}}).encode(), "whole"),
    ("SUCCESS with stdout that is not base64", json.dumps({"uuid": GOOD_UUID, "status": "SUCCESS", "metadata": {"result": {"state": {"exit_code": 0},
                                               "stdout": {"value": "%%%not base64%%%", "encoding": "base64"}, "stderr": {"value": ""}}}}).encode(), "whole"),
]


class FakeTime:
    """The adapter module's clock: every reading is three seconds later, so a polling deadline passes after a few dozen polls."""

    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        self.now += 3.0
        return self.now

    def time(self):
        return time.time()

    def sleep(self, seconds):
        pass


def sandbox_case(scenario, label, spawn_answer=None, poll_answer=None):
    from attest.ledger import JOURNAL_FILE, Ledger
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes

    def script(method, path, n):
        if method == "POST":
            return spawn_answer if spawn_answer is not None else (200, json.dumps({"uuid": GOOD_UUID}).encode(), "whole")
        if method == "GET" and "/operations/" in path:
            return poll_answer if poll_answer is not None else (200, json.dumps(done_record(GOOD_UUID)).encode(), "whole")
        return 200, b"{}", "whole"
    server = Server(script)
    directory = tmpdir("r10-d-")
    ledger = Ledger()
    ledger.attach_sink(directory / JOURNAL_FILE)
    adapter = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, base_url=server.base, poll_interval=0.0)
    adapter._sleep = lambda s: None
    import attest.sandbox.tf_sandboxes as module
    raised = None
    try:
        with mock.patch.object(module, "time", FakeTime()):
            quiet(adapter.run_branch, "img-1", {}, [{"name": "s", "cmd": ["true"]}], stage="mutant-m01", timeout=5)
    except BaseException as error:  # noqa: BLE001
        raised = error
    seen = list(server.seen)
    server.close()
    op = ledger.sandbox_ops[0] if ledger.sandbox_ops else None
    status = getattr(op, "status", None)
    stops = bool(getattr(raised, "stops_run", False))
    halted = ledger.halted is not None
    expected = "UNCERTAIN" if poll_answer is None else "ACCEPTED_UNREAD"
    after = seen[1:] if poll_answer is None else seen[seen.index(f"GET /v1/operations/{GOOD_UUID}") + 1:] if f"GET /v1/operations/{GOOD_UUID}" in seen else seen
    # for a truncated poll the bounded read retries are the repaired behaviour (a cut body is a transport failure); the check is
    # that the operation ends ACCEPTED_UNREAD, halted, with nothing but those retries sent
    retries_only = all(s == f"GET /v1/operations/{GOOD_UUID}" for s in after) and poll_answer is not None and poll_answer[2] == "cut"
    ok = (type(raised).__name__ == "SandboxError" and stops and status == expected and halted and (not after or retries_only)
          and (poll_answer is None or getattr(op, "operation_uuid", None) == GOOD_UUID))
    check(scenario, f"{'spawn' if poll_answer is None else 'poll'} answered HTTP 200 with {label}: {expected}, halted, nothing sent afterwards", ok,
          f"raised {type(raised).__name__ if raised else None} (stops_run {stops}); op {status}; halted {halted}; requests {seen}")
    try:
        ledger.admit("sandboxes", "next")
        admitted = True
    except Exception:  # noqa: BLE001
        admitted = False
    if not admitted and ok:
        pass
    elif ok:
        check(scenario, f"after {label}: no new request is admitted", False, "admit() still accepts requests")


@guarded("D", "Sandboxes answers")
def scenario_d_sandboxes(tree: Path):
    for label, body, mode in MALFORMED + SPAWN_ONLY:
        sandbox_case("D", label, spawn_answer=(200, body, mode))
    for label, body, mode in MALFORMED + POLL_ONLY:
        sandbox_case("D", label, poll_answer=(200, body, mode))


def gateway_case(label, body, mode):
    from attest.ledger import JOURNAL_FILE, Ledger
    from attest.models.codex_gateway import CodexGateway
    from attest.models.pacing import RateGovernor
    catalog = {"data": [{"id": m, "supported_reasoning_efforts": ["low", "medium", "high"]} for m in ("gpt-6-sol", "gpt-6-astra", "gpt-6-luna")]}

    def script(method, path, n):
        if path.startswith("/v1/models"):
            return 200, json.dumps(catalog).encode(), "whole"
        if path.startswith("/v1/status"):
            return 200, b'{"limits": {"hourly_requests_enforced": false}}', "whole"
        return 200, body, mode
    server = Server(script)
    directory = tmpdir("r10-g-")
    ledger = Ledger()
    ledger.attach_sink(directory / JOURNAL_FILE)
    gateway = CodexGateway("offline-fake-key", ledger, base_url=server.base, governor=RateGovernor("offline-fake-key", state_path=None))
    gateway._sleep = lambda s: None
    schema = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}
    raised = second = None
    try:
        quiet(gateway.structured, "implement", "prompt", schema, "implement-1")
    except BaseException as error:  # noqa: BLE001
        raised = error
    runs_before = sum(1 for s in server.seen if s.startswith("POST"))
    try:
        quiet(gateway.structured, "implement", "prompt", schema, "implement-2")
    except BaseException as error:  # noqa: BLE001
        second = error
    runs_after = sum(1 for s in server.seen if s.startswith("POST"))
    server.close()
    stops = bool(getattr(raised, "stops_run", False))
    ok = type(raised).__name__ == "ModelError" and stops and ledger.halted is not None and runs_before == 1 and runs_after == 1
    check("D", f"gateway /run answered HTTP 200 with {label}: the run halts and no further model request is sent", ok,
          f"raised {type(raised).__name__ if raised else None}: {str(raised)[:120] if raised else ''} (stops_run {stops}); halted {ledger.halted is not None}; "
          f"POSTs {runs_before} then {runs_after}; calls recorded {len(ledger.model_calls)}")


def tokenfactory_case(label, body, mode):
    from attest.ledger import JOURNAL_FILE, Ledger
    from attest.models.nebius_tokenfactory import NebiusTokenFactory

    def script(method, path, n):
        return 200, body, mode
    server = Server(script)
    directory = tmpdir("r10-t-")
    ledger = Ledger()
    ledger.attach_sink(directory / JOURNAL_FILE)
    provider = NebiusTokenFactory("synthetic-key", ledger, base_url=server.base, usd_cap=0.5, max_calls=22)
    provider._sleep = lambda s: None
    schema = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}
    raised = None
    try:
        quiet(provider.structured, "implement", "prompt", schema, "implement-1")
    except BaseException as error:  # noqa: BLE001
        raised = error
    first = len(server.seen)
    try:
        quiet(provider.structured, "implement", "prompt", schema, "implement-2")
    except BaseException:  # noqa: BLE001
        pass
    total = len(server.seen)
    server.close()
    stops = bool(getattr(raised, "stops_run", False))
    totals = ledger.totals()
    ok = (type(raised).__name__ == "ModelError" and stops and ledger.halted is not None and first == 1 and total == 1
          and (totals.get("cost_usd_committed") or 0) > 0)
    check("D", f"Token Factory answered HTTP 200 with {label}: the run halts, the reservation stays committed, nothing further is sent", ok,
          f"raised {type(raised).__name__ if raised else None} (stops_run {stops}); halted {ledger.halted is not None}; requests {first} then {total}; "
          f"committed {totals.get('cost_usd_committed')}")


MODEL_ONLY = [
    ("an object without output", b'{"model": "gpt-6-sol"}', "whole"),
    ("output that is not a string", b'{"output": 5}', "whole"),
]
TF_ONLY = [
    ("an object without choices", b'{"model": "m", "usage": {"prompt_tokens": 10, "completion_tokens": 5}}', "whole"),
    ("choices that are not a list", b'{"choices": {"0": {}}, "usage": {"prompt_tokens": 10, "completion_tokens": 5}}', "whole"),
    ("a message that is not an object", b'{"choices": [{"message": "hi"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}', "whole"),
]


@guarded("D", "model answers")
def scenario_d_models(tree: Path):
    for label, body, mode in MALFORMED + MODEL_ONLY:
        gateway_case(label, body, mode)
    for label, body, mode in MALFORMED + TF_ONLY:
        tokenfactory_case(label, body, mode)


@guarded("D", "a malformed spawn answer inside a run")
def scenario_d_pipeline(tree: Path):
    from attest.core.pipeline import Pipeline
    from attest.core.task import TaskSpec
    from attest.ledger import Ledger
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
    FakeProvider, _, TASK, Recorder, RecordingProvider, StoppingExecutor = fakes(tree)
    server = Server(lambda m, p, n: (200, b'"accepted"', "whole"))
    ledger, requests = Ledger(), Recorder()
    real = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, base_url=server.base, poll_interval=0.0)
    real._sleep = lambda s: None
    provider = RecordingProvider(FakeProvider(ledger, "honest"), requests)
    executor = StoppingExecutor(ledger, requests, lambda s: s.startswith("mutant-"), delegate=real)
    out = tmpdir("r10-dp-")
    pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=executor, ledger=ledger, out_dir=out, max_turns=6, max_mutants=6,
                        mutant_workers=1, tavily=None, profile_label="test")
    raised = None
    try:
        bundle = quiet(pipeline.run)
    except BaseException as error:  # noqa: BLE001
        raised, bundle = error, pipeline.bundle
    server.close()
    after = requests.items[requests.stop + 1:] if requests.stop is not None else ["(the mutant stage was not reached)"]
    record = bundle.get("reconciliation") or {}
    check("D", "a mutant spawn answered with a JSON string inside a run: nothing is sent after it and the run ends ERROR for reconciliation",
          requests.stop is not None and after == [] and bundle["verdict"]["verdict"] == "ERROR" and bool(record.get("required")) and raised is None,
          f"requests after it: {after[:6]}{'...' if len(after) > 6 else ''} ({len(after)}); verdict {bundle['verdict']['verdict']}; "
          f"reconciliation required {record.get('required')}; raised {type(raised).__name__ if raised else None}")


# ---------------------------------------------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="comma-separated scenario letters")
    args = ap.parse_args(argv)
    tree = Path(args.tree).resolve()
    sys.path.insert(0, str(tree))
    os.chdir(tree)
    import tests  # noqa: F401  (the tree's offline guard)
    import attest
    version = attest.__version__
    from attest.core.provenance import attest_revision
    digest = attest_revision(tree / "attest")["digest"]
    print(f"tree {tree} (attest {version}, package {digest[:12]})", flush=True)
    import logging
    logging.disable(logging.CRITICAL)
    only = set(filter(None, args.only.split(",")))
    for letter, fn in (("A", scenario_a), ("B", scenario_b_failed_insert), ("B", scenario_b_killed), ("B", scenario_b_repair), ("C", scenario_c),
                       ("D", scenario_d_sandboxes), ("D", scenario_d_models), ("D", scenario_d_pipeline)):
        if not only or letter in only:
            fn(tree)
    passed = sum(1 for r in RESULTS if r["ok"])
    summary = {"tree": str(tree), "attest_version": version, "package_digest": digest, "checks": len(RESULTS), "passed": passed,
               "failed": len(RESULTS) - passed, "by_scenario": {s: {"passed": sum(1 for r in RESULTS if r["scenario"] == s and r["ok"]),
                                                                  "failed": sum(1 for r in RESULTS if r["scenario"] == s and not r["ok"])}
                                                              for s in sorted({r["scenario"] for r in RESULTS})}, "results": RESULTS}
    Path(args.out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\n{passed} of {len(RESULTS)} checks pass; {len(RESULTS) - passed} fail -> {args.out}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
