"""Revision 10 (20 Oct 2026): holds survive restarts, the held state and its hold are written atomically, a resumed batch cannot bypass
unresolved operations, and a malformed upstream answer stops the run at once.

Each class reproduces a failure of 0.9.0 (reports/attest-revision10-repairs-2026-10-20/repro/ shows them against the frozen tree) and
the repaired behaviour, offline (tests/_isolation.py blocks every connection outside the loopback interface and removes credentials):
- RestartKeepsHolds: a run whose proof bundle (or journal) requires reconciliation keeps its hold after a restart, whichever of bundle
  creation, row update and hold creation the process died after; imported evidence is never held for its history.
- AtomicHoldRecord: the reconciliation state and its hold are one transaction: a refused insert or a process killed inside it changes
  nothing, recovery is idempotent (one hold per run, ever), a cleared hold is never reopened, and a failure fails the service closed.
- ResumeGate: a resumed batch reads every row, bundle and run or judge journal; nothing starts until a note names the item ids, the note is
  kept across restarts, `--resume` alone approves nothing, and a refused resume sends nothing (not even a status read).
- MalformedAnswers: arrays, scalars, invalid UTF-8, unpaired surrogates, non-standard constants, missing fields, malformed identifiers
  and truncated bodies, through the real HTTP client and the real adapters against a local server: a spawn becomes UNCERTAIN, an accepted
  operation ACCEPTED_UNREAD with its id, a model call uncertain, the run halts and no further request leaves.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from attest.app.db import Store, StoreError, read_run_reconciliation
from attest.core.pipeline import Pipeline
from attest.core.task import TaskSpec
from attest.http import HttpError, MalformedResponse, decode_json, request_json, safe_text
from attest.ledger import JOURNAL_FILE, Ledger, RunHalted, SandboxOp, read_journal, utcnow
from attest.models.base import ModelError
from attest.sandbox.tf_sandboxes import SandboxError, TokenFactorySandboxes
from tests.test_revision9 import STEPS, _FailingExecutor, _RecordingProvider, _Requests, quiet
from tests.test_verification import TASK, FakeExecutor, FakeProvider

ROOT = Path(__file__).resolve().parent.parent
OP = "0199a000-0000-7000-8000-00000000a001"
SCHEMA = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}


def tmp(test: unittest.TestCase, prefix: str = "attest-r10-") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix))
    test.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
    return path


def pipeline_run(runs_dir: Path, run_id: str, stop=None, scenario: str = "honest") -> tuple[dict, Pipeline, _Requests]:
    """An offline run into runs_dir/run_id; `stop(stage)` names the sandbox operation that ends uncertain (None: an honest run)."""
    ledger, requests = Ledger(), _Requests()
    provider = _RecordingProvider(FakeProvider(ledger, scenario), requests, False)
    executor = _FailingExecutor(ledger, scenario, requests, stop or (lambda s: False))
    pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=executor, ledger=ledger, out_dir=runs_dir, max_turns=6,
                        max_mutants=6, mutant_workers=1, tavily=None, profile_label="development", run_id=run_id)
    with contextlib.ExitStack() as stack:
        if stop is not None:
            stack.enter_context(unittest.TestCase().assertLogs("attest.ledger", "ERROR"))
        bundle = quiet(pipeline.run)
    return bundle, pipeline, requests


def row(store: Store, run_id: str, status: str = "running", out_dir=None, requester: str = "team"):
    store.create_run(run_id=run_id, task_id="durationkit-units-001", task_title="T", provider="codex", profile_label="development", status=status,
                     stage="verify", created_at=utcnow(), requester=requester, out_dir=str(out_dir) if out_dir else None)


def holds(db: Path, run_id: str) -> list[tuple]:
    conn = sqlite3.connect(str(db))
    try:
        return conn.execute("SELECT hold_id, cleared_at FROM holds WHERE run_id = ?", (run_id,)).fetchall()
    finally:
        conn.close()


def sql(db: Path, statement: str) -> None:
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(statement)
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------------------------------------------------------- item 1
class RestartKeepsHolds(unittest.TestCase):
    def setUp(self):
        self.data = tmp(self)
        self.db = self.data / "attest.db"
        self.store = Store(self.db)

    def recover(self) -> dict:
        with self.assertLogs("attest.app", "ERROR") if True else contextlib.nullcontext():
            return Store(self.db).startup_recovery(per_run_cap=0.5)

    def test_a_bundle_written_before_the_crash_keeps_its_hold(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "held-1", stop=lambda s: s == "verify")
        self.assertTrue(bundle["reconciliation"]["required"])
        row(self.store, "held-1", "running", pipeline.out_dir)  # the process died after write_bundle, before the worker's row update
        report = self.recover()
        self.assertEqual([r["action"] for r in report["settled"]], ["held"])
        settled = self.store.get_run("held-1")
        self.assertEqual((settled["status"], settled["error_code"], settled["verdict"], settled["stage"]), ("error", "reconciliation_required", "ERROR", "reconciliation"))
        open_holds = [h for h in self.store.active_holds() if h["run_id"] == "held-1"]
        self.assertEqual(len(open_holds), 1)
        self.assertEqual(len(open_holds[0]["items"]), len(bundle["reconciliation"]["items"]))
        self.assertEqual([e["stage"] for e in self.store.events("held-1")], ["reconciliation"])

    def test_the_journal_is_read_even_when_the_bundle_needs_nothing(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "honest-1")
        self.assertFalse(bundle["reconciliation"]["required"])
        # a spawn journaled after the bundle's ledger was taken (a record the bundle cannot know): the journal decides
        op = SandboxOp(stage="late", operation_uuid=None, image_uuid="img", result_image_uuid=None, disposable=True, networking_enabled=False, status="PENDING",
                       exit_code=None, timed_out=None, signal=None, duration_s=None, raw_cost_diag=None, stdout_truncated=None, started_at_utc=utcnow(), op_id="s99")
        with (pipeline.out_dir / JOURNAL_FILE).open("a", encoding="utf-8") as handle:
            from dataclasses import asdict
            handle.write(json.dumps({"event": "sandbox_op", **asdict(op)}) + "\n")
        row(self.store, "honest-1", "running", pipeline.out_dir)
        self.recover()
        self.assertEqual(self.store.get_run("honest-1")["error_code"], "reconciliation_required")
        self.assertEqual([h["run_id"] for h in self.store.active_holds()], ["honest-1"])

    def test_an_unreadable_bundle_falls_back_to_the_journal(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "cut-1", stop=lambda s: s == "verify")
        (pipeline.out_dir / "proof_bundle.json").write_text('{"run_id": "cut-1", "verdict": ', encoding="utf-8")  # cut while being written
        row(self.store, "cut-1", "running", pipeline.out_dir)
        self.recover()
        self.assertEqual(self.store.get_run("cut-1")["error_code"], "reconciliation_required")
        self.assertIn("could not be read", self.store.get_run("cut-1")["error"])
        self.assertEqual(len(self.store.active_holds()), 1)

    def test_an_honest_bundle_is_finalized_without_a_hold(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "honest-2")
        row(self.store, "honest-2", "running", pipeline.out_dir)
        report = Store(self.db).startup_recovery(per_run_cap=0.5)
        self.assertEqual([r["action"] for r in report["settled"]], ["finalized"])
        self.assertEqual((self.store.get_run("honest-2")["status"], self.store.get_run("honest-2")["verdict"]), ("finished", "VERIFIED"))
        self.assertEqual(self.store.active_holds(), [])

    def test_every_crash_point_between_bundle_row_and_hold(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "crash", stop=lambda s: s == "verify")
        cases = {
            "after the bundle, before any row update": dict(status="running"),
            "after the row update, before the hold (0.9.0's two writes)": dict(status="error", error_code="reconciliation_required", error="stopped", stage="reconciliation"),
            "after the hold": None,
        }
        for label, state in cases.items():
            with self.subTest(crash=label):
                data = tmp(self)
                shutil.copytree(pipeline.out_dir, data / "runs" / "crash")
                store = Store(data / "attest.db")
                row(store, "crash", "running", data / "runs" / "crash")
                if state is None:
                    with self.assertLogs("attest.app", "ERROR"):
                        store.record_reconciliation("crash", "stopped for reconciliation", bundle["reconciliation"]["items"])
                else:
                    store.update_run("crash", **state)
                with self.assertLogs("attest.app", "ERROR") if state is not None else contextlib.nullcontext():
                    Store(data / "attest.db").startup_recovery(per_run_cap=0.5)
                self.assertEqual(len(holds(data / "attest.db", "crash")), 1)
                self.assertIsNone(holds(data / "attest.db", "crash")[0][1], "the hold is open")
                self.assertEqual(store.get_run("crash")["error_code"], "reconciliation_required")

    def test_a_run_of_the_own_directory_without_a_row_is_held_and_imported_evidence_is_not(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "orphan", stop=lambda s: s == "verify")
        with self.assertLogs("attest.app", "ERROR"):
            self.assertTrue(self.store.import_run_dir(pipeline.out_dir, providers=None, hold_if_required=True))
        self.assertEqual(self.store.get_run("orphan")["error_code"], "reconciliation_required")
        self.assertEqual(len(holds(self.db, "orphan")), 1)
        evidence = tmp(self)
        shutil.copytree(pipeline.out_dir, evidence / "imported")
        other = Store(evidence / "other.db")
        self.assertTrue(other.import_run_dir(evidence / "imported", providers=None))  # evidence from elsewhere: a row, never a hold
        self.assertEqual(other.active_holds(), [])
        self.assertEqual(other.repair_holds(), [], "start-up repair never holds imported evidence")

    def test_rows_that_0_9_0_finalized_as_finished_are_repaired(self):
        bundle, pipeline, _ = pipeline_run(self.data / "runs", "finished-held", stop=lambda s: s == "verify")
        row(self.store, "finished-held", "finished", pipeline.out_dir)
        self.store.update_run("finished-held", verdict="ERROR", stage="finished")
        with self.assertLogs("attest.app", "ERROR"):
            repaired = self.store.repair_holds()
        self.assertEqual([r["action"] for r in repaired], ["held_from_bundle"])
        self.assertEqual(self.store.get_run("finished-held")["error_code"], "reconciliation_required")
        self.assertEqual(self.store.repair_holds(), [], "idempotent")


# ----------------------------------------------------------------------------------------------------------------------- item 2
DIE_CHILD = r'''
import os, sys
sys.path.insert(0, sys.argv[1])
import tests  # the offline guard
from attest.app.db import Store
store = Store(sys.argv[2])
store._conn.create_function("die", 0, lambda: os._exit(9))
store.record_reconciliation("r1", "stopped for reconciliation at verify (uncertain_operation): 1 operation(s) to settle", [{"kind": "sandbox_spawn"}])
print("NOT KILLED")
'''


class AtomicHoldRecord(unittest.TestCase):
    def setUp(self):
        self.data = tmp(self)
        self.db = self.data / "attest.db"
        self.store = Store(self.db)
        self.bundle, self.pipeline, _ = pipeline_run(self.data / "runs", "r1", stop=lambda s: s == "verify")
        row(self.store, "r1", "running", self.pipeline.out_dir)

    def test_a_refused_insert_changes_nothing(self):
        sql(self.db, "CREATE TRIGGER refuse BEFORE INSERT ON holds BEGIN SELECT RAISE(FAIL, 'injected: database or disk is full'); END")
        before = self.store.get_run("r1")
        with self.assertRaises(StoreError):
            self.store.record_reconciliation("r1", "stopped", [{"kind": "sandbox_spawn"}])
        self.assertEqual(self.store.get_run("r1"), before, "the row update was rolled back with the refused insert")
        self.assertEqual(self.store.events("r1"), [])
        self.assertEqual(holds(self.db, "r1"), [])

    def test_a_kill_inside_the_transaction_leaves_nothing_half_written(self):
        sql(self.db, "CREATE TRIGGER die_on_hold BEFORE INSERT ON holds BEGIN SELECT die(); END")
        child = subprocess.run([sys.executable, "-c", DIE_CHILD, str(ROOT), str(self.db)], capture_output=True, text=True, timeout=120)
        self.assertEqual(child.returncode, 9, child.stderr[-500:])
        sql(self.db, "DROP TRIGGER die_on_hold")
        survivor = Store(self.db)
        self.assertEqual(survivor.get_run("r1")["status"], "running", "the uncommitted row update is gone with the process")
        self.assertEqual(holds(self.db, "r1"), [])
        with self.assertLogs("attest.app", "ERROR"):
            survivor.startup_recovery(per_run_cap=0.5)
        self.assertEqual(len(holds(self.db, "r1")), 1)
        self.assertEqual(survivor.get_run("r1")["error_code"], "reconciliation_required")

    def test_recording_is_idempotent_with_one_hold_per_run(self):
        with self.assertLogs("attest.app", "ERROR"):
            first = self.store.record_reconciliation("r1", "stopped", [{"kind": "sandbox_spawn"}])
        ref = self.store.get_run("r1")["error_ref"]
        second = self.store.record_reconciliation("r1", "stopped again", [{"kind": "sandbox_spawn"}])
        self.assertEqual(first, second)
        self.assertEqual(len(holds(self.db, "r1")), 1)
        self.assertEqual(len(self.store.events("r1")), 1)
        self.assertEqual(self.store.get_run("r1")["error_ref"], ref, "a recorded row is not rewritten")
        conn = sqlite3.connect(str(self.db))
        with self.assertRaises(sqlite3.IntegrityError):  # the database itself refuses a second hold for the run
            conn.execute("INSERT INTO holds (hold_id, run_id, created_at, reason) VALUES ('x', 'r1', 'now', 'dup')")
        conn.close()

    def test_repeated_recovery_and_a_cleared_hold(self):
        with self.assertLogs("attest.app", "ERROR"):
            Store(self.db).startup_recovery(per_run_cap=0.5)
        for _ in range(3):
            Store(self.db).startup_recovery(per_run_cap=0.5)
        self.assertEqual(len(holds(self.db, "r1")), 1)
        hold = self.store.active_holds()[0]["hold_id"]
        with self.assertLogs("attest.app", "WARNING"):
            self.assertTrue(self.store.clear_hold(hold, "the account lists no operation for the spawn (offline test)"))
        for _ in range(2):
            self.assertEqual(Store(self.db).startup_recovery(per_run_cap=0.5), {"settled": [], "repaired": []})
        self.assertEqual(self.store.record_reconciliation("r1", "stopped", []), hold, "re-recording returns the cleared hold, it opens nothing")
        self.assertEqual(self.store.active_holds(), [])
        self.assertEqual(len(holds(self.db, "r1")), 1)

    def worker(self, stops):
        from attest.app.worker import Worker
        with mock.patch.object(Worker, "_loop", lambda self: None):
            worker = Worker(self.store, self.data, TASK.parent.parent, max_turns=6, min_free_frac=0.0, min_free_mb=0)  # the host's free space is not under test
        built = []

        def build(run_id, provider_name, ledger):
            built.append(run_id)
            requests = _Requests()
            return (_RecordingProvider(FakeProvider(ledger, "honest"), requests, False),
                    _FailingExecutor(ledger, "honest", requests, stops.get(run_id, lambda s: False)), None)
        worker.build_runtime = build
        return worker, built

    def feed(self, worker, run_id):
        item = (run_id, TASK, "codex", "development")
        worker.queue.put(item)
        worker.queue.get()
        quiet(worker._run_one, item)

    def test_the_worker_fails_closed_until_the_record_is_written(self):
        from attest.app.worker import ReconciliationHold
        for run_id in ("w1", "w2", "w3"):
            row(self.store, run_id, "queued")
        sql(self.db, "CREATE TRIGGER refuse BEFORE INSERT ON holds BEGIN SELECT RAISE(FAIL, 'injected: database or disk is full'); END")
        worker, built = self.worker({"w1": lambda s: s == "verify"})
        with self.assertLogs(level="ERROR"):
            self.feed(worker, "w1")
            self.feed(worker, "w2")
        self.assertEqual(built, ["w1"], "nothing started after the record failed")
        self.assertIsNotNone(worker.closed)
        self.assertEqual(self.store.get_run("w1")["status"], "running", "left for the restart recovery, not recorded as an ordinary failure")
        self.assertEqual(self.store.get_run("w2")["error_code"], "paused_for_reconciliation")
        with mock.patch.object(worker, "ensure_alive", return_value=True), self.assertRaises(ReconciliationHold):
            worker.enqueue("durationkit-units-001", "codex", "team", "development")
        sql(self.db, "DROP TRIGGER refuse")
        with self.assertLogs(level="WARNING"):
            worker.housekeeping()
        self.assertIsNone(worker.closed, "the pending record was written; the hold now pauses the service")
        self.assertEqual(self.store.get_run("w1")["error_code"], "reconciliation_required")
        self.assertEqual([h["run_id"] for h in self.store.active_holds()], ["w1"])
        with mock.patch.object(worker, "ensure_alive", return_value=True), self.assertRaises(ReconciliationHold):
            worker.enqueue("durationkit-units-001", "codex", "team", "development")
        with self.assertLogs("attest.app", "WARNING"):
            self.store.clear_hold(self.store.active_holds()[0]["hold_id"], "reconciled offline")
        self.feed(worker, "w3")
        self.assertEqual(self.store.get_run("w3")["status"], "finished")

    def test_a_failed_start_up_recovery_fails_the_service_closed(self):
        from fastapi.testclient import TestClient
        sql(self.db, "CREATE TRIGGER refuse BEFORE INSERT ON holds BEGIN SELECT RAISE(FAIL, 'injected: database or disk is full'); END")
        env = {"ATTEST_DATA_DIR": str(self.data), "ATTEST_EXAMPLES_DIR": str(TASK.parent.parent), "ATTEST_ADMIN_TOKEN": "synthetic-team-token",
               "ATTEST_IMPORT_DIRS": str(self.data / "none")}
        with mock.patch.dict(os.environ, env), self.assertLogs(level="ERROR"):
            import attest.app.server as server
            server = importlib.reload(server)
            server.worker.stop()
            client = TestClient(server.app)
            health = client.get("/api/health", headers={"X-Attest-Token": "synthetic-team-token"}).json()
            self.assertTrue(health["reconciliation"]["fail_closed"])
            self.assertFalse(health["reconciliation"]["accepting_runs"])
            self.assertTrue(health["startup"]["recovery_failed"])
            self.assertIn("start-up recovery", health["reconciliation"]["fail_closed_reason"])
            answer = client.post("/api/runs", json={"task_id": "durationkit-units-001", "provider": "nebius"}, headers={"X-Attest-Confirm": "start-run"})
            self.assertEqual(answer.status_code, 503)
            self.assertEqual(server.store.get_run("r1")["status"], "running", "the run stays for the next restart's recovery")


# ----------------------------------------------------------------------------------------------------------------------- item 3
def _harness():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_evaluation_r10", ROOT / "scripts" / "run_evaluation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResumeGate(unittest.TestCase):
    """The harness's real run_batch; only one_system (a scripted cell), the provider construction and the provenance probe are stubs."""

    def setUp(self):
        self.h = _harness()
        self.out = tmp(self) / "batch"
        from tests.test_audit_accounting import DescriptionOnly, _provenance_stub
        self.provenance = _provenance_stub()
        self.DescriptionOnly = DescriptionOnly
        self.executed: list[int] = []
        self.next_rows: dict[int, dict] = {}
        self.assertEqual(self.batch(fresh=True), 0)

    def cell(self, cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root, registered_profile=None, budget=None):
        self.executed.append(cell["scheduled_index"])
        run_id = f"{cell['task']}-{cell['system']}-a{cell['attempt']}-{len(self.executed):03d}"
        (Path(out_dir) / run_id).mkdir(parents=True)
        extra = self.next_rows.pop(cell["scheduled_index"], {})
        return {**cell, "status": "completed", "verdict": "BASELINE" if cell["system"] == "baseline" else "VERIFIED", "accepted": True, "finished": True,
                "changed_paths": 1, "held_out_correct": True, "cost_usd": None, "cost_committed_usd": 0.0, "wall_s": 0.1, "infra_error": False,
                "uncertain": False, "revision_digest": self.provenance["attest_revision"]["digest"], "out_dir": str(Path(out_dir) / run_id), "run_id": run_id,
                "reconciliation": [], "halted": None, **extra}

    def batch(self, fresh=False, **flags):
        """One harness process: a fresh registration and run, or a resume with the given flags (`reconciled=`, `items=`)."""
        common = ["--snapshot-root", str(ROOT), "--source-root", str(ROOT)] + [x for k, v in flags.items() for x in (f"--{k}", v)]
        argv = (["--provider", "codex", "--tasks", "durationkit-units-001", "--systems", "baseline,attest", "--attempts", "2", "--workers", "1",
                 "--out", str(self.out)] if fresh else ["--resume", str(self.out)]) + common
        args = self.h.parse_args(argv)
        with mock.patch.object(self.h, "runtime_provenance", return_value=self.provenance), \
             mock.patch.object(self.h, "build_provider", return_value=self.DescriptionOnly()), \
             mock.patch.object(self.h, "codex_governor", return_value=None), mock.patch.object(self.h, "one_system", side_effect=self.cell), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.h.run_batch(args)
        self.err = err.getvalue()
        return code

    def rows(self):
        return json.loads((self.out / "evaluation.json").read_text(encoding="utf-8"))["rows"]

    def keep_first(self, n: int, **change):
        report = json.loads((self.out / "evaluation.json").read_text(encoding="utf-8"))
        report["rows"] = sorted(report["rows"], key=lambda r: r["scheduled_index"])[:n]
        report["rows"][-1].update(change)
        (self.out / "evaluation.json").write_text(json.dumps(report), encoding="utf-8")

    def pending(self):
        return json.loads((self.out / self.h.PENDING_FILE).read_text(encoding="utf-8"))["items"]

    def test_completed_and_halted_rows_block_until_acknowledged_by_id(self):
        item = {"kind": "sandbox_operation", "stage": "mutant-m01", "op_id": "s7", "operation_uuid": OP, "status": "ACCEPTED_UNREAD",
                "how": f"GET /operations/{OP} for its final status (read-only); it is never spawned again"}
        self.keep_first(2, verdict="ERROR", reconciliation=[item], halted={"kind": "uncertain_operation", "stage": "mutant-m01", "reason": "lost", "at_utc": "t"})
        executed = list(self.executed)
        schedule = (self.out / "schedule.json").read_text(encoding="utf-8")
        self.assertEqual(self.batch(), 4)
        self.assertEqual(self.executed, executed, "--resume alone starts nothing")
        self.assertEqual((self.out / "schedule.json").read_text(encoding="utf-8"), schedule, "not even a resumption is recorded")
        ids = [i["id"] for i in self.pending()]
        self.assertEqual(len(ids), 1)
        self.assertIn(ids[0], self.err)
        self.assertEqual(self.batch(reconciled="looked: no note"), 2, "a note without item ids is no approval")
        self.assertEqual(self.batch(items=ids[0]), 2, "ids without a note are no approval")
        self.assertEqual(self.batch(reconciled="checked", items="u-000000000000"), 2, "an unknown id refuses everything")
        self.assertFalse((self.out / self.h.ACK_FILE).exists())
        self.assertEqual(self.executed, executed)
        note = f"GET /operations/{OP}: SUCCESS, exit 1 (the mutant was killed); nothing to settle (offline test)"
        self.assertEqual(self.batch(reconciled=note, items=ids[0]), 0)
        self.assertGreater(len(self.executed), len(executed))
        record = json.loads((self.out / self.h.ACK_FILE).read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual((record["note"], [i["id"] for i in record["items"]]), (note, ids))
        report = json.loads((self.out / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(report["starting_total"]["reconciled"][0]["items"], ids)
        self.assertEqual(report["schedule"]["resumptions"][-1]["reconciliation_acknowledgements"], ids)
        # the acknowledgement is kept across restarts; a new item needs its own
        self.keep_first(3)
        executed = list(self.executed)
        self.assertEqual(self.batch(), 0)
        self.assertGreater(len(self.executed), len(executed), "the recorded acknowledgement is honoured without a new note")
        self.keep_first(3, reconciliation=[{**item, "op_id": "s8", "operation_uuid": None, "status": "UNCERTAIN", "kind": "sandbox_spawn"}])
        self.assertEqual(self.batch(), 4)
        self.assertEqual([i["stage"] for i in self.pending()], ["mutant-m01"])

    def test_halt_records_without_items(self):
        for kind, blocks in (("uncertain_operation", True), ("journal_failure", True), ("batch_stop", False)):
            with self.subTest(kind=kind):
                self.keep_first(2, verdict="ERROR", reconciliation=[], halted={"kind": kind, "stage": "verify", "reason": "r", "at_utc": f"t-{kind}"})
                code = self.batch()
                self.assertEqual(code == 4, blocks, self.err[-400:])
                if blocks:
                    self.assertEqual([i["kind"] for i in self.pending()], ["halt"])

    def test_the_run_directory_is_read_even_when_the_row_lists_nothing(self):
        first = sorted(self.rows(), key=lambda r: r["scheduled_index"])[0]
        run_dir = Path(first["out_dir"])
        cases = {}
        bundle_dir = run_dir.parent / "with-bundle"
        bundle_dir.mkdir()
        (bundle_dir / "proof_bundle.json").write_text(json.dumps({"run_id": "with-bundle", "reconciliation": {"required": True, "halt": None, "items": [
            {"kind": "sandbox_spawn", "stage": "verify", "op_id": "s1", "how": "list the account's operations"}]}}), encoding="utf-8")
        cases["the bundle's reconciliation record"] = bundle_dir
        journal_dir = run_dir.parent / "with-journal"
        ledger = Ledger()
        ledger.attach_sink(journal_dir / JOURNAL_FILE)
        ledger.add_op(SandboxOp(stage="checkpoint", operation_uuid=None, image_uuid="img", result_image_uuid=None, disposable=False, networking_enabled=False,
                                status=None, exit_code=None, timed_out=None, signal=None, duration_s=None, raw_cost_diag=None, stdout_truncated=None,
                                started_at_utc=utcnow()))
        cases["the run journal"] = journal_dir
        judge_dir = run_dir.parent / "with-judge"
        judge_dir.mkdir()
        judge = Ledger()
        judge.attach_sink(run_dir.parent / "with-judge.judge.jsonl")
        judge.add_op(SandboxOp(stage="judge", operation_uuid=OP, image_uuid="img", result_image_uuid=None, disposable=True, networking_enabled=False,
                               status="ACCEPTED", exit_code=None, timed_out=None, signal=None, duration_s=None, raw_cost_diag=None, stdout_truncated=None,
                               started_at_utc=utcnow()))
        cases["the judge journal"] = judge_dir
        for label, directory in cases.items():
            with self.subTest(record=label):
                self.keep_first(2, out_dir=str(directory), run_id=directory.name, reconciliation=[], halted=None)
                self.assertEqual(self.batch(), 4, self.err[-300:])
                self.assertIn(directory.name, {i["run_id"] for i in self.pending()}, "the row's own run directory was read")

    def test_a_cut_acknowledgement_line_approves_nothing(self):
        self.keep_first(2, reconciliation=[{"kind": "sandbox_spawn", "stage": "verify", "op_id": "s1", "how": "list"}])
        self.assertEqual(self.batch(), 4)
        iid = self.pending()[0]["id"]
        (self.out / self.h.ACK_FILE).write_text('{"event": "reconciled", "note": "half', encoding="utf-8")  # a write cut short
        self.assertEqual(self.batch(), 4)
        self.assertEqual(self.batch(reconciled="checked: no operation exists", items=iid), 0)
        lines = (self.out / self.h.ACK_FILE).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2, "the new record starts on its own line after the cut one")
        self.assertEqual(json.loads(lines[1])["items"][0]["id"], iid)

    def test_a_refused_resume_sends_nothing(self):
        self.keep_first(2, reconciliation=[{"kind": "model_call", "stage": "spec", "started_at_utc": "t", "how": "ingress log"}])
        refused = AssertionError("nothing may be built or read from a provider before the gate")
        args = self.h.parse_args(["--resume", str(self.out), "--snapshot-root", str(ROOT), "--source-root", str(ROOT)])
        with mock.patch.object(self.h, "codex_governor", side_effect=refused), mock.patch.object(self.h, "build_provider", side_effect=refused), \
             mock.patch.object(self.h, "runtime_provenance", side_effect=refused), mock.patch.object(self.h, "one_system", side_effect=refused), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(quiet(self.h.run_batch, args), 4)


# ----------------------------------------------------------------------------------------------------------------------- item 4
class Upstream:
    """A local HTTP server answering scripted bodies: script(method, path, n) -> (status, body bytes, mode, headers); mode 'whole' or
    'cut' (a Content-Length larger than the body, then the connection closes)."""

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
                status, body, mode, headers = outer.script(self.command, self.path, n)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body) + (40 if mode == "cut" else 0)))
                if mode == "cut":
                    self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
                if mode == "cut":
                    self.close_connection = True

            do_GET = do_POST = do_DELETE = _answer

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def finished(uuid=OP):
    report = {"runner": "attest-guest/3", "steps": [{"name": "s", "cmd": ["true"], "exit_code": 0, "timed_out": False, "stdout": "", "stderr": "", "duration_s": 0.1}]}
    stdout = "ATTEST-RESULT-BEGIN\n" + json.dumps(report) + "\nATTEST-RESULT-END\n"
    return {"uuid": uuid, "status": "SUCCESS", "duration": 0.5, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False, "signal": -1},
            "stdout": {"value": stdout}, "stderr": {"value": ""}, "resources": {"cost": 0.0001}}}}


UNREADABLE = {  # bodies no adapter may read (a 2xx answer)
    "an array": b"[]",
    "an array holding the expected object": json.dumps([{"uuid": OP}]).encode(),
    "a string": b'"accepted"',
    "a number": b"42",
    "null": b"null",
    "an empty body": b"",
    "invalid UTF-8": b'{"uuid": "\xff\xfe", "status": "PENDING"}',
    "an unpaired surrogate escape": b'{"uuid": "\\ud800", "status": "PENDING"}',
    "a NaN": b'{"uuid": NaN}',
    "not JSON": b"<html>ok</html>",
    "nesting beyond the parser": b"[" * 100_000,
}


class MalformedAnswers(unittest.TestCase):
    def sandbox(self, script):
        server = Upstream(script)
        self.addCleanup(server.close)
        directory = tmp(self)
        ledger = Ledger()
        ledger.attach_sink(directory / JOURNAL_FILE)
        adapter = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, base_url=server.base, poll_interval=0.0)
        adapter._sleep = lambda s: None
        return server, ledger, adapter, directory / JOURNAL_FILE

    def assert_stopped(self, ledger: Ledger, server: Upstream, sent: int):
        self.assertIsNotNone(ledger.halted)
        self.assertEqual(len(server.seen), sent, server.seen)
        with self.assertRaises(RunHalted):
            ledger.admit("sandboxes", "next")  # no new request is admitted after the stop

    def test_an_unreadable_spawn_answer_is_uncertain(self):
        cases = {label: (200, body, "whole", {}) for label, body in UNREADABLE.items()}
        cases.update({
            "a truncated body": (201, b'{"uuid": "0199a000-0000', "cut", {}),
            "an operation id that is a path": (201, json.dumps({"uuid": "../../instances"}).encode(), "whole", {}),
            "an operation id that is a number": (201, json.dumps({"uuid": 12345}).encode(), "whole", {}),
            "an operation id with a trailing newline": (201, json.dumps({"uuid": OP + "\n"}).encode(), "whole", {}),
            "an object without an operation id": (201, b'{"command": "/usr/local/bin/python"}', "whole", {}),
        })
        for label, answer in cases.items():
            with self.subTest(answer=label):
                server, ledger, adapter, journal = self.sandbox(lambda m, p, n, _a=answer: _a)
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(SandboxError) as caught:
                    adapter.run_branch("img-1", {}, STEPS, stage="mutant-m01", timeout=5)
                self.assertTrue(caught.exception.stops_run and caught.exception.uncertain)
                self.assertEqual(ledger.sandbox_ops[0].status, "UNCERTAIN")
                self.assertIsNone(ledger.sandbox_ops[0].operation_uuid, "a malformed id is never used")
                self.assert_stopped(ledger, server, 1)
                state = read_journal(journal)
                self.assertEqual([u["stage"] for u in state["spawns_unresolved"]], ["mutant-m01"], "the UNCERTAIN state is journaled")
                self.assertEqual([i["kind"] for i in ledger.reconciliation_items()], ["sandbox_spawn"])
                note = ledger.sandbox_ops[0].outcome_note
                self.assertEqual(note, safe_text(note, 2000), "the note is ASCII-safe")
                if "path" in label:
                    self.assertIn("../../instances", note, "the reported id is kept, escaped, for the operator")

    def test_the_location_header_of_an_unreadable_spawn_answer_is_kept(self):
        server, ledger, adapter, journal = self.sandbox(lambda m, p, n: (201, b'"queued"', "whole", {"Location": f"/v1/operations/{OP}"}))
        with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(SandboxError):
            adapter.run_branch("img-1", {}, STEPS, stage="verify", timeout=5)
        self.assertEqual(ledger.sandbox_ops[0].status, "UNCERTAIN")
        self.assertEqual(ledger.halted["operation"]["reported_uuid"], OP)
        self.assertIn(f"GET /operations/{OP}", ledger.reconciliation_items()[0]["note"])
        self.assert_stopped(ledger, server, 1)

    def test_an_unreadable_poll_answer_leaves_the_operation_accepted_unread(self):
        cases = {label: body for label, body in UNREADABLE.items() if label != "an array holding the expected object"}
        cases.update({
            "a record without a status": json.dumps({"uuid": OP}).encode(),
            "a status that is not a string": json.dumps({"uuid": OP, "status": 7}).encode(),
            "an undocumented status": json.dumps({"uuid": OP, "status": "RUNNING"}).encode(),
            "a record of another operation": json.dumps(finished("0199a000-0000-7000-8000-0000000000ff")).encode(),
            "SUCCESS without a result": json.dumps({"uuid": OP, "status": "SUCCESS"}).encode(),
            "SUCCESS with a result that is a list": json.dumps({"uuid": OP, "status": "SUCCESS", "metadata": {"result": []}}).encode(),
            "SUCCESS with an exit code that is a string": json.dumps({**finished(), "metadata": {"result": {"state": {"exit_code": "0"}}}}).encode(),
            "SUCCESS with stdout that is not base64": json.dumps({**finished(), "metadata": {"result": {"state": {"exit_code": 0}, "stdout": {"value": "%%", "encoding": "base64"}}}}).encode(),
            "SUCCESS with a result image that is not a UUID": json.dumps({**finished(), "result_image_uuid": "img; rm -rf /"}).encode(),
        })
        for label, body in cases.items():
            with self.subTest(answer=label):
                server, ledger, adapter, journal = self.sandbox(lambda m, p, n, _b=body: (201, json.dumps({"uuid": OP}).encode(), "whole", {}) if m == "POST" else (200, _b, "whole", {}))
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(SandboxError) as caught:
                    adapter.run_branch("img-1", {}, STEPS, stage="verify", timeout=5)
                self.assertTrue(caught.exception.accepted_unread and caught.exception.stops_run)
                self.assertEqual((ledger.sandbox_ops[0].status, ledger.sandbox_ops[0].operation_uuid), ("ACCEPTED_UNREAD", OP))
                self.assert_stopped(ledger, server, 2)  # the spawn and the one poll: no retry of a malformed answer, no cancel
                self.assertNotIn(f"DELETE /v1/operations/{OP}", server.seen)
                self.assertEqual(read_journal(journal)["operations_unread"], [OP])
                self.assertIn(f"GET /operations/{OP}", ledger.reconciliation_items()[0]["how"])

    def test_a_truncated_poll_body_keeps_its_bounded_retries(self):
        server, ledger, adapter, journal = self.sandbox(lambda m, p, n: (201, json.dumps({"uuid": OP}).encode(), "whole", {}) if m == "POST" else
                                                        ((200, b'{"uuid": "', "cut", {}) if n < 4 else (200, json.dumps(finished()).encode(), "whole", {})))
        run = adapter.run_branch("img-1", {}, STEPS, stage="verify", timeout=5)
        self.assertEqual((run.status, ledger.sandbox_ops[0].status), ("SUCCESS", "SUCCESS"))
        self.assertIsNone(ledger.halted)
        self.assertEqual(server.seen.count(f"GET /v1/operations/{OP}"), 3)

    def test_an_unreadable_image_list_halts_the_run(self):
        for label, body in {"an array": b"[]", "images that are not a list": b'{"images": {}}', "an image without a UUID": b'{"images": [{"tag": "t", "uuid": 5}]}'}.items():
            with self.subTest(answer=label):
                server, ledger, adapter, _ = self.sandbox(lambda m, p, n, _b=body: (200, _b, "whole", {}))
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(SandboxError) as caught:
                    adapter.resolve_image("t")
                self.assertTrue(caught.exception.malformed and caught.exception.stops_run)
                self.assertEqual(ledger.halted["kind"], "malformed_response")
                self.assert_stopped(ledger, server, 1)

    def gateway(self, run_answer, models=None, status=None):
        from attest.models.codex_gateway import CodexGateway
        from attest.models.pacing import RateGovernor
        catalog = {"data": [{"id": m, "supported_reasoning_efforts": ["low", "medium", "high"]} for m in ("gpt-6-sol", "gpt-6-astra", "gpt-6-luna")]}

        def script(method, path, n):
            if path.startswith("/v1/models"):
                return models or (200, json.dumps(catalog).encode(), "whole", {})
            if path.startswith("/v1/status"):
                return status or (200, b'{"limits": {"hourly_requests_enforced": false}}', "whole", {})
            return run_answer
        server = Upstream(script)
        self.addCleanup(server.close)
        ledger = Ledger()
        ledger.attach_sink(tmp(self) / JOURNAL_FILE)
        gateway = CodexGateway("offline-fake-key", ledger, base_url=server.base, governor=RateGovernor("offline-fake-key", state_path=None))
        gateway._sleep = lambda s: None
        return server, ledger, gateway

    def test_an_unreadable_gateway_answer_stops_the_run(self):
        cases = {label: (200, body, "whole", {}) for label, body in UNREADABLE.items()}
        cases.update({"a truncated body": (200, b'{"output": "{\\"res', "cut", {}),
                      "an object without output or json": (200, b'{"id": "run-42", "model": "gpt-6-sol"}', "whole", {}),
                      "output that is a number": (200, b'{"id": "run-43", "output": 5}', "whole", {}),
                      "usage that is a string": (200, b'{"id": "run-44", "output": "{}", "usage": "lots"}', "whole", {})})
        for label, answer in cases.items():
            with self.subTest(answer=label):
                server, ledger, gateway = self.gateway(answer)
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(ModelError) as caught:
                    gateway.structured("implement", "prompt", SCHEMA, "implement-1")
                self.assertTrue(caught.exception.stops_run)
                self.assertEqual([c.outcome for c in ledger.model_calls], ["uncertain"])
                self.assertEqual([i["kind"] for i in ledger.reconciliation_items()], ["model_call"])
                posts = sum(1 for s in server.seen if s.startswith("POST"))
                with self.assertRaises(ModelError) as again:
                    gateway.structured("implement", "prompt", SCHEMA, "implement-2")
                self.assertTrue(again.exception.halted)
                self.assertEqual((posts, sum(1 for s in server.seen if s.startswith("POST"))), (1, 1), "no further model request")
                if label.startswith("an object without"):
                    self.assertEqual(ledger.halted["operation"]["answer_id"], "run-42", "the answer's id is kept")

    def test_unreadable_gateway_reads_stop_the_run(self):
        for label, kwargs in {"a catalog that is an array": {"models": (200, b"[]", "whole", {})},
                              "a catalog entry without an id": {"models": (200, b'{"data": [{"name": "x"}]}', "whole", {})},
                              "a status that is not UTF-8": {"status": (200, b'{"limits": "\xff"}', "whole", {})}}.items():
            with self.subTest(answer=label):
                server, ledger, gateway = self.gateway((200, b'{"output": "{\\"result\\": 1}"}', "whole", {}), **kwargs)
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(ModelError) as caught:
                    gateway.structured("implement", "prompt", SCHEMA, "implement-1")
                self.assertTrue(caught.exception.stops_run)
                self.assertEqual(ledger.halted["kind"], "malformed_response")
                self.assertEqual(sum(1 for s in server.seen if s.startswith("POST")), 0, "the run request was never sent")

    def test_an_unreadable_token_factory_answer_keeps_its_reservation_and_stops(self):
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        cases = {label: (200, body, "whole", {}) for label, body in UNREADABLE.items()}
        cases.update({"a truncated body": (200, b'{"choices": [', "cut", {}),
                      "no choices": (200, json.dumps({"id": "cmpl-1", "usage": usage}).encode(), "whole", {}),
                      "empty choices": (200, json.dumps({"choices": [], "usage": usage}).encode(), "whole", {}),
                      "a message that is a string": (200, json.dumps({"choices": [{"message": "hi"}], "usage": usage}).encode(), "whole", {}),
                      "content that is a list": (200, json.dumps({"choices": [{"message": {"content": ["x"]}}], "usage": usage}).encode(), "whole", {})})
        for label, answer in cases.items():
            with self.subTest(answer=label):
                server = Upstream(lambda m, p, n, _a=answer: _a)
                self.addCleanup(server.close)
                ledger = Ledger()
                ledger.attach_sink(tmp(self) / JOURNAL_FILE)
                provider = NebiusTokenFactory("synthetic-key", ledger, base_url=server.base, usd_cap=0.5, max_calls=22)
                provider._sleep = lambda s: None
                with self.assertLogs("attest.ledger", "ERROR"), self.assertRaises(ModelError) as caught:
                    provider.structured("implement", "prompt", SCHEMA, "implement-1")
                self.assertTrue(caught.exception.stops_run)
                call = ledger.model_calls[0]
                self.assertEqual((call.outcome, call.settlement, call.cost_usd), ("uncertain", "unsettled", None))
                self.assertGreater(ledger.totals()["cost_usd_committed"], 0, "the reservation stays committed")
                with self.assertRaises(ModelError):
                    provider.structured("implement", "prompt", SCHEMA, "implement-2")
                self.assertEqual(len(server.seen), 1, "no repair, no low-effort retry, nothing further")

    def test_an_unreadable_search_answer_ends_grounding(self):
        import attest.core.grounding as grounding
        for label, (usage, search) in {"a search answer that is an array": (b'{"plan": 1}', b"[]"),
                                       "results that are strings": (b'{"plan": 1}', b'{"results": ["x"]}'),
                                       "a usage answer that is not UTF-8": (b'{"plan": "\xff"}', b'{"results": []}')}.items():
            with self.subTest(answer=label):
                server = Upstream(lambda m, p, n, _u=usage, _s=search: (200, _u if "usage" in p else _s, "whole", {}))
                self.addCleanup(server.close)
                with mock.patch.object(grounding, "BASE", server.base.rsplit("/v1", 1)[0]):
                    record = grounding.ground(["q1", "q2"], grounding.Tavily("synthetic-key"))
                self.assertTrue(record["uncertain"] or record["malformed"], record)
                self.assertLessEqual(sum(1 for s in server.seen if s.startswith("POST")), 1, "no further search")

    def test_a_malformed_spawn_answer_inside_a_run_stops_it(self):
        server = Upstream(lambda m, p, n: (201, b'"accepted"', "whole", {}))
        self.addCleanup(server.close)
        ledger, requests = Ledger(), _Requests()
        real = TokenFactorySandboxes("synthetic-key", "synthetic-project", ledger, base_url=server.base, poll_interval=0.0)
        real._sleep = lambda s: None

        class Hybrid(_FailingExecutor):
            def run_branch(inner, image, files, steps, stage, deletes=None, timeout=120, networking=False):
                if stage.startswith("mutant-") and inner.requests.stop is None:
                    inner.requests.stop = inner.requests.add("sandbox", stage)
                    return real.run_branch(image, files, steps, stage=stage, deletes=deletes, timeout=timeout)
                return super().run_branch(image, files, steps, stage, deletes, timeout, networking)
        provider = _RecordingProvider(FakeProvider(ledger, "honest"), requests, False)
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=Hybrid(ledger, "honest", requests, lambda s: False), ledger=ledger,
                            out_dir=tmp(self), max_turns=6, max_mutants=6, mutant_workers=1, tavily=None, profile_label="test")
        with self.assertLogs("attest.ledger", "ERROR"):
            bundle = quiet(pipeline.run)
        self.assertIsNotNone(requests.stop)
        self.assertEqual(requests.items[requests.stop + 1:], [], "no model call or sandbox request after the malformed answer")
        self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
        self.assertTrue(bundle["reconciliation"]["required"])
        self.assertEqual(len(server.seen), 1)

    def test_a_malformed_gateway_answer_inside_a_run_stops_it_without_a_repair_request(self):
        server, ledger, gateway = self.gateway((200, b'["not", "an", "object"]', "whole", {}))
        requests = _Requests()

        class Hybrid:
            name, describe = "codex_gateway", (lambda inner: {"provider": "codex_gateway"})

            def __init__(inner):
                inner.fake, inner.ledger = FakeProvider(ledger, "honest"), ledger

            def structured(inner, role, prompt, schema, stage):
                requests.add("model", stage)
                if role == "implement" and requests.stop is None:
                    requests.stop = len(requests.items) - 1
                    return gateway.structured(role, prompt, schema, stage)
                return inner.fake.structured(role, prompt, schema, stage)
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=Hybrid(), executor=_FailingExecutor(ledger, "honest", requests, lambda s: False), ledger=ledger,
                            out_dir=tmp(self), max_turns=6, max_mutants=6, mutant_workers=1, tavily=None, profile_label="test")
        with self.assertLogs("attest.ledger", "ERROR"):
            bundle = quiet(pipeline.run)
        self.assertEqual(requests.items[requests.stop + 1:], [], "no repair request and nothing else after the unreadable answer")
        self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
        self.assertEqual(sum(1 for s in server.seen if s.startswith("POST")), 1)


class GatewayStatusAtBatchStart(unittest.TestCase):
    def test_an_unreadable_status_answer_starts_no_cell(self):
        harness = _harness()
        server = Upstream(lambda m, p, n: (200, b'["no", "limits"]', "whole", {}))
        self.addCleanup(server.close)
        out = tmp(self) / "batch"
        args = harness.parse_args(["--provider", "codex", "--tasks", "durationkit-units-001", "--systems", "attest", "--out", str(out),
                                   "--snapshot-root", str(ROOT), "--source-root", str(ROOT)])
        started = AssertionError("no cell may start after an unreadable status answer")
        env = {"ATTEST_CODEX_BASE_URL": server.base, "CODEX_API_KEY": "synthetic-key", "ATTEST_CODEX_PACING_STATE": "off"}
        with mock.patch.dict(os.environ, env), mock.patch.object(harness, "one_system", side_effect=started), \
             mock.patch.object(harness, "build_provider", return_value=type("D", (), {"describe": lambda self: {"provider": "offline"}})()), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err, self.assertLogs("attest.ledger", "ERROR"):
            self.assertEqual(harness.run_batch(args), 2)
        self.assertIn("could not be read", err.getvalue())
        self.assertEqual(server.seen, ["GET /v1/status"], "the status read was the only request")


class StrictDecoding(unittest.TestCase):
    def test_the_decoder_and_its_texts(self):
        for label, raw in UNREADABLE.items():
            with self.subTest(body=label):
                with self.assertRaises(MalformedResponse) as caught:
                    decode_json(raw, 200)
                self.assertEqual(str(caught.exception), str(caught.exception).encode("ascii", "replace").decode("ascii"), "ASCII-safe")
                self.assertFalse(caught.exception.request_sent is False)
        self.assertEqual(decode_json(b'{"a": "\\ud83d\\ude00"}', 200), {"a": "\U0001F600"}, "a paired surrogate escape is text")
        self.assertIsNone(decode_json(b"", 200, allow_empty=True))
        self.assertEqual(decode_json(b"[1]", 200, expect=list), [1])

    def test_error_bodies_and_diagnostics_never_carry_undecodable_text(self):
        error = HttpError(500, {"error": {"message": "bad \ud800 thing"}}, "https://example.invalid/v1/run")
        self.assertIn("\\ud800", str(error))
        str(error).encode("utf-8")  # no unpaired surrogate survives into the message
        from attest.core.diagnostics import Diagnostics
        sidecar = tmp(self)
        diagnostics = Diagnostics("r", sidecar)
        diagnostics.record("stage", RuntimeError("text with \ud800 inside"))
        self.assertIn("\\ud800", (sidecar / "r.jsonl").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
