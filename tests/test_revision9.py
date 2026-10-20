"""Revision 9 (20 Oct 2026): a run stops at the first operation whose outcome is uncertain, and nothing is sent after it.

Each class reproduces one failure of revision 8 and shows the repaired behaviour, offline (tests/_isolation.py blocks every connection
outside the loopback interface and removes credentials):
- ErrorBodies: an HTTP error whose body is cut or stalls is an HttpError with its status, `request_sent` and phase (revision 8 let a
  raw IncompleteRead or timeout escape the transport wrapper); a success whose body is cut keeps its status.
- AnswerClasses: the one classification of a failed POST (`not_sent`, `rejected`, `uncertain`) and of a retryable read.
- SandboxSpawnAnswers, SandboxPolls: a spawn answered 5xx is UNCERTAIN and halts the run (revision 8 recorded no state and raised a
  plain error); 4xx is REJECTED; polls are retried, and an accepted operation whose outcome is not read is ACCEPTED_UNREAD.
- SandboxJournal, RestartRecovery: the PENDING record is durable before the spawn, the accepted id before the first poll; any journal
  failure (disk full, I/O error, a half-written line, a read-back mismatch) dispatches or polls nothing and halts with what is known;
  after a restart the journal names every spawn and operation left unresolved, and the console holds new runs.
- ConcurrentBranches: parallel branches send nothing after one of them halts the run.
- GatewayAnswers, TokenFactoryAnswers, GroundingStops: the providers' 5xx answers are uncertain and halt; Tavily too.
- PipelineStopsEverywhere: an uncertain Sandbox failure at every stage (checkpoint, witness, red check, implementer tools,
  verification, repository, held-out, mutants, adversarial tests, arbitration re-runs) ends the run there: no model call or sandbox
  request afterwards, verdict ERROR with the operation listed for reconciliation, no advice to run the stage again (revision 8 went on
  to the drift audit after the breaker, and ended VERIFIED after an uncertain witness or mutant).
- CheckerReconciliation, ConsoleHolds, HarnessStops, CliReconcile: the checker, the console worker, the evaluation harness and the CLI.
"""

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import shutil
import socket
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import attest.ledger as ledger_module
from attest.core.check import check_bundle
from attest.core.pipeline import Pipeline
from attest.core.task import TaskSpec
from attest.http import HttpError, TransportError, post_outcome, read_retryable, request_json
from attest.ledger import JOURNAL_FILE, Ledger, LedgerError, ModelCall, RunHalted, SandboxOp, read_journal, utcnow
from attest.models.base import ModelError, ModelResult
from attest.sandbox.tf_sandboxes import SandboxError, TokenFactorySandboxes
from tests.test_verification import HELDOUT_SRC, TASK, FakeExecutor, FakeProvider

ROOT = Path(__file__).resolve().parent.parent
STEPS = [{"name": "s", "cmd": ["true"]}]
SCHEMA = {"type": "object", "properties": {"result": {"type": "integer"}}, "required": ["result"]}


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args, **kwargs)


def temp_dir(test: unittest.TestCase, prefix: str = "attest-r9-") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix))
    test.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
    return path


def journaled(test: unittest.TestCase) -> tuple[Ledger, Path]:
    directory = temp_dir(test)
    ledger = Ledger()
    ledger.attach_sink(directory / JOURNAL_FILE)
    return ledger, directory / JOURNAL_FILE


def events(journal: Path) -> list[dict]:
    return [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]


def done(uuid="op-1", status="SUCCESS"):
    report = {"runner": "attest-guest/3", "steps": [{"name": "s", "cmd": ["true"], "exit_code": 0, "timed_out": False, "stdout": "", "stderr": "", "duration_s": 0.1}]}
    stdout = "ATTEST-RESULT-BEGIN\n" + json.dumps(report) + "\nATTEST-RESULT-END\n"
    return {"uuid": uuid, "status": status, "duration": 0.5, "metadata": {"result": {"state": {"exit_code": 0, "timed_out": False, "signal": -1},
            "stdout": {"value": stdout}, "stderr": {"value": ""}, "resources": {"cost": 0.0001}}}}


class Sandbox:
    """The real Sandboxes client with HTTP replaced by `script(method, path, n)` (a value is answered 200, an exception raised)."""

    def __init__(self, test, script, ledger=None, poll_interval=0.0):
        self.ledger, self.journal = (ledger, None) if ledger is not None else journaled(test)
        self.ex = TokenFactorySandboxes("synthetic-key", "synthetic-project", self.ledger, poll_interval=poll_interval)
        self.ex._sleep = lambda s: None
        self.seen: list[str] = []
        self.script = script
        self.lock = threading.Lock()

    def fake(self, method, url, headers, payload=None, timeout=60, max_bytes=0):
        with self.lock:
            self.seen.append(f"{method} {url.split('/v1')[-1].split('?')[0]}")
            n = len(self.seen)
        outcome = self.script(method, url.split("/v1")[-1], n)
        if isinstance(outcome, BaseException):
            raise outcome
        return 200, outcome, {}

    def run(self, stage="verify", timeout=120):
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", self.fake):
            return self.ex.run_branch("image-1", {}, STEPS, stage=stage, timeout=timeout)

    def posts(self):
        return sum(1 for s in self.seen if s.startswith("POST"))

    def gets(self):
        return sum(1 for s in self.seen if s.startswith("GET"))


def lost():
    return TransportError("RemoteDisconnected: Remote end closed connection without response", request_sent=True, phase="response")


def not_sent():
    return TransportError("SSLEOFError: EOF occurred in violation of protocol (while the connection was being set up)", request_sent=False, phase="connect")


# ----------------------------------------------------------------------------------------------------------------------- transport
class _OneShot:
    def __init__(self, respond):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(2)
        self.port = self.sock.getsockname()[1]
        self.respond = respond
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            conn, _ = self.sock.accept()
        except OSError:
            return
        with conn:
            conn.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                data += chunk
            head, _, body = data.partition(b"\r\n\r\n")
            length = next((int(line.split(b":")[1]) for line in head.split(b"\r\n") if line.lower().startswith(b"content-length:")), 0)
            while len(body) < length:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                body += chunk
            try:
                self.respond(conn)
            except OSError:
                pass

    def close(self):
        self.sock.close()
        self.thread.join(5)


class ErrorBodies(unittest.TestCase):
    def post(self, respond, timeout=2.0):
        server = _OneShot(respond)
        try:
            return request_json("POST", f"http://127.0.0.1:{server.port}/v1/instances", {}, {"x": 1}, timeout=timeout)
        finally:
            server.close()

    def test_a_chunked_error_body_cut_mid_chunk_is_an_http_error_with_its_status(self):
        with self.assertRaises(HttpError) as caught:
            self.post(lambda c: c.sendall(b"HTTP/1.1 502 Bad Gateway\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\n\r\n"
                                          b"40\r\n{\"error\": {\"message\": \"upstream res"))
        error = caught.exception
        self.assertEqual((error.status, error.request_sent, error.phase, error.body_complete), (502, True, "response", False))
        self.assertIn("IncompleteRead", error.body_error)
        self.assertEqual(post_outcome(error), "uncertain")

    def test_an_error_body_that_stalls_is_an_http_error_with_its_status(self):
        with self.assertRaises(HttpError) as caught:
            self.post(lambda c: (c.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 200\r\n\r\n{\"err"), time.sleep(3)), timeout=1.0)
        self.assertEqual((caught.exception.status, caught.exception.body_complete), (503, False))
        self.assertIn("incomplete", str(caught.exception))

    def test_a_short_content_length_error_body_is_marked_incomplete(self):
        with self.assertRaises(HttpError) as caught:
            self.post(lambda c: c.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 300\r\n\r\n{\"detail\": \"invalid"))
        self.assertEqual((caught.exception.status, caught.exception.body_complete), (400, False))
        self.assertEqual(post_outcome(caught.exception), "rejected", "a 4xx is a refusal whatever happened to its body")

    def test_a_complete_error_body_is_parsed(self):
        with self.assertRaises(HttpError) as caught:
            self.post(lambda c: c.sendall(b"HTTP/1.1 422 Unprocessable\r\nContent-Type: application/json\r\nContent-Length: 27\r\n\r\n"
                                          b"{\"detail\": \"name required\"}"))
        self.assertTrue(caught.exception.body_complete)
        self.assertEqual(caught.exception.body, {"detail": "name required"})

    def test_a_success_whose_body_is_cut_keeps_its_status_and_stays_uncertain(self):
        with self.assertRaises(TransportError) as caught:
            self.post(lambda c: c.sendall(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n40\r\n{\"uuid\": \"op-"))
        self.assertEqual((caught.exception.status, caught.exception.request_sent, caught.exception.phase), (200, True, "response"))
        self.assertEqual(post_outcome(caught.exception), "uncertain")


class AnswerClasses(unittest.TestCase):
    def test_post_outcomes(self):
        self.assertEqual(post_outcome(not_sent()), "not_sent")
        self.assertEqual(post_outcome(lost()), "uncertain")
        for status in (400, 401, 403, 404, 408, 409, 413, 422, 429):
            self.assertEqual(post_outcome(HttpError(status, {}, "u")), "rejected", status)
        for status in (500, 502, 503, 504, 520, 301, 303):
            self.assertEqual(post_outcome(HttpError(status, {}, "u")), "uncertain", status)
        self.assertEqual(post_outcome(RuntimeError("anything else")), "uncertain")

    def test_retryable_reads(self):
        self.assertTrue(read_retryable(lost()) and read_retryable(not_sent()))
        for status in (408, 429, 500, 502, 503, 504):
            self.assertTrue(read_retryable(HttpError(status, {}, "u")), status)
        for status in (400, 401, 403, 404, 422):
            self.assertFalse(read_retryable(HttpError(status, {}, "u")), status)


# ----------------------------------------------------------------------------------------------------------------------- sandboxes
class SandboxSpawnAnswers(unittest.TestCase):
    def test_a_spawn_answered_5xx_is_uncertain_halts_the_run_and_is_never_resent(self):
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                box = Sandbox(self, lambda m, p, n, _s=status: HttpError(_s, {"raw": "<html>bad gateway</html>"}, "https://sandbox.invalid/v1/instances"))
                with self.assertRaises(SandboxError) as caught:
                    box.run()
                self.assertTrue(caught.exception.uncertain and caught.exception.stops_run)
                self.assertEqual(caught.exception.http_status, status)
                op = box.ledger.sandbox_ops[0]
                self.assertEqual((op.status, op.http_status), ("UNCERTAIN", status))
                self.assertEqual(box.posts(), 1)
                self.assertEqual(box.ledger.halted["kind"], "uncertain_operation")
                items = box.ledger.reconciliation_items()
                self.assertEqual([i["kind"] for i in items], ["sandbox_spawn"])
                self.assertIn("GET /operations?kind=instance", items[0]["how"])
                self.assertEqual([e.get("status") for e in events(box.journal) if e["event"].startswith("sandbox_op")], ["PENDING", "UNCERTAIN"])
                self.assertEqual(read_journal(box.journal)["spawns_unresolved"][0]["op_id"], op.op_id)
                with self.assertRaises(SandboxError) as again:  # the run has stopped: the next operation sends nothing
                    box.run(stage="existing")
                self.assertTrue(again.exception.halted)
                self.assertEqual(box.posts(), 1)

    def test_a_spawn_answered_4xx_is_rejected_and_needs_no_reconciliation(self):
        for status in (400, 401, 403, 404, 413, 422, 429):
            with self.subTest(status=status):
                box = Sandbox(self, lambda m, p, n, _s=status: HttpError(_s, {"detail": "no"}, "https://sandbox.invalid/v1/instances"))
                with self.assertRaises(SandboxError) as caught:
                    box.run()
                self.assertTrue(caught.exception.rejected)
                self.assertFalse(caught.exception.stops_run)
                self.assertEqual(box.ledger.sandbox_ops[0].status, "REJECTED")
                self.assertIsNone(box.ledger.halted)
                self.assertEqual(box.ledger.reconciliation_items(), [])
                self.assertEqual(box.ledger.totals()["sandbox_rejected"], 1)

    def test_a_success_without_an_operation_id_is_uncertain(self):
        box = Sandbox(self, lambda m, p, n: {"status": "accepted"})
        with self.assertRaises(SandboxError) as caught:
            box.run()
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(box.ledger.sandbox_ops[0].status, "UNCERTAIN")
        self.assertTrue(box.ledger.halted)

    def test_a_lost_answer_and_a_never_sent_spawn(self):
        box = Sandbox(self, lambda m, p, n: lost())
        with self.assertRaises(SandboxError) as caught:
            box.run()
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual((box.posts(), box.ledger.sandbox_ops[0].status), (1, "UNCERTAIN"))
        box = Sandbox(self, lambda m, p, n: not_sent())
        with self.assertRaises(SandboxError) as caught:
            box.run()
        self.assertTrue(caught.exception.unreachable)
        self.assertFalse(caught.exception.stops_run)
        self.assertEqual((box.posts(), box.ledger.sandbox_ops[0].status), (3, "NOT_SENT"))
        self.assertIsNone(box.ledger.halted)


class SandboxPolls(unittest.TestCase):
    def test_transient_poll_answers_are_retried(self):
        for status in (404, 408, 429, 500, 502, 503, 504):
            with self.subTest(status=status):
                box = Sandbox(self, lambda m, p, n, _s=status: {"uuid": "op-1"} if m == "POST" else (HttpError(_s, {}, p) if n == 2 else done()))
                self.assertTrue(box.run().ok)
                self.assertEqual((box.posts(), box.gets()), (1, 2))
                self.assertIsNone(box.ledger.halted)

    def test_polls_that_keep_failing_leave_the_operation_accepted_unread_with_its_id(self):
        for failure in (HttpError(503, {}, "p"), lost(), HttpError(404, {}, "p")):
            with self.subTest(failure=type(failure).__name__ + str(getattr(failure, "status", ""))):
                box = Sandbox(self, lambda m, p, n, _f=failure: {"uuid": "op-1"} if m == "POST" else _f)
                with self.assertRaises(SandboxError) as caught:
                    box.run()
                self.assertTrue(caught.exception.accepted_unread)
                self.assertEqual(caught.exception.operation_uuid, "op-1")
                self.assertEqual(box.gets(), 5, "one poll plus four bounded retries")
                self.assertEqual(box.posts(), 1, "an accepted operation is never spawned again")
                self.assertEqual(box.ledger.sandbox_ops[0].status, "ACCEPTED_UNREAD")
                self.assertEqual([i["kind"] for i in box.ledger.reconciliation_items()], ["sandbox_operation"])
                self.assertIn("GET /operations/op-1", box.ledger.reconciliation_items()[0]["how"])
                self.assertEqual(read_journal(box.journal)["operations_unread"], ["op-1"])
                self.assertTrue(box.ledger.halted)

    def test_a_definite_poll_refusal_is_not_retried_and_still_kept_for_reconciliation(self):
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"} if m == "POST" else HttpError(403, {}, p))
        with self.assertRaises(SandboxError) as caught:
            box.run()
        self.assertTrue(caught.exception.accepted_unread)
        self.assertEqual(box.gets(), 1)
        self.assertEqual(box.ledger.sandbox_ops[0].status, "ACCEPTED_UNREAD")

    def test_an_operation_that_never_ends_is_accepted_unread(self):
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"} if m == "POST" else ({} if m == "DELETE" else {"uuid": "op-1", "status": "RUNNING"}))
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", box.fake):
            with self.assertRaises(SandboxError) as caught:
                box.ex._execute("image-1", box.ex._job({}, STEPS), "verify", disposable=True, timeout=-90)
        self.assertTrue(caught.exception.accepted_unread)
        self.assertIn("DELETE /operations/op-1", box.seen)
        self.assertEqual(box.ledger.sandbox_ops[0].status, "ACCEPTED_UNREAD")
        self.assertEqual(len(box.ledger.reconciliation_items()), 1)

    def test_polling_stops_when_the_run_halts_elsewhere(self):
        ledger, _ = journaled(self)
        state = {"polls": 0}

        def script(m, p, n):
            if m == "POST":
                return {"uuid": "op-1"}
            state["polls"] += 1
            if state["polls"] == 2:
                ledger.halt("uncertain_operation", "a parallel branch's spawn is uncertain", stage="mutant-x")
            return {"uuid": "op-1", "status": "RUNNING"}
        box = Sandbox(self, script, ledger=ledger)
        with self.assertRaises(SandboxError) as caught:
            box.run()
        self.assertTrue(caught.exception.accepted_unread and caught.exception.halted)
        self.assertEqual(box.gets(), 2, "no poll after the halt")
        self.assertNotIn("DELETE /operations/op-1", box.seen)
        op = box.ledger.sandbox_ops[0]
        self.assertEqual((op.status, op.outcome_note), ("ACCEPTED_UNREAD", "polling stopped: the run halted for reconciliation"))
        self.assertEqual(ledger.halted["stage"], "mutant-x", "the run's halt stays the first one")


class ConcurrentBranches(unittest.TestCase):
    def test_no_request_is_admitted_after_the_halt(self):
        ledger, journal = journaled(self)
        state = {"posts": 0, "admitted_at_halt": None}
        ledger.on_halt = lambda led, rec: state.__setitem__("admitted_at_halt", led.admitted)
        lock = threading.Lock()

        def script(m, p, n):
            if m == "POST":
                with lock:
                    state["posts"] += 1
                    number = state["posts"]
                if number == 3:
                    raise lost()
                return {"uuid": f"op-{number}"}
            time.sleep(0.01)
            return {"uuid": p.rsplit("/", 1)[-1], "status": "RUNNING"}
        box = Sandbox(self, script, ledger=ledger, poll_interval=0.005)
        box.ex._sleep = lambda s: time.sleep(min(s, 0.005))

        def branch(i):
            try:
                with mock.patch("attest.sandbox.tf_sandboxes.request_json", box.fake):
                    box.ex.run_branch("image-1", {}, STEPS, stage=f"mutant-{i}", timeout=-89)
            except SandboxError as error:
                return error
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", box.fake):
            with ThreadPoolExecutor(max_workers=6) as pool:
                errors = list(pool.map(branch, range(6)))
        self.assertIsNotNone(state["admitted_at_halt"])
        self.assertLessEqual(len(box.seen), state["admitted_at_halt"], "every request sent was admitted before the halt")
        self.assertTrue(all(isinstance(e, SandboxError) and e.stops_run for e in errors))
        statuses = sorted(o.status for o in ledger.sandbox_ops)
        self.assertNotIn("PENDING", statuses)
        self.assertNotIn("ACCEPTED", statuses)
        accepted = [o for o in ledger.sandbox_ops if o.operation_uuid]
        listed = {i.get("operation_uuid") for i in ledger.reconciliation_items()}
        self.assertTrue({o.operation_uuid for o in accepted} <= listed, "every accepted operation is listed for reconciliation")
        self.assertEqual(sum(1 for o in ledger.sandbox_ops if o.status == "UNCERTAIN"), 1)


class SandboxJournal(unittest.TestCase):
    def failing(self, event, status=None, partial=False, code=errno.ENOSPC, at="write"):
        real = ledger_module._write_durably

        def write(path, lines):
            try:
                record = json.loads(lines[-1])
            except (json.JSONDecodeError, IndexError):
                record = {}
            if record.get("event") == event and (status is None or record.get("status") == status):
                if partial:
                    with open(path, "a", encoding="utf-8") as handle:
                        handle.write("".join(lines)[: len("".join(lines)) // 2])
                raise OSError(code, os.strerror(code))
            return real(path, lines)
        return write

    def test_the_pending_record_is_durable_before_the_spawn_is_sent(self):
        seen_journal = []

        def script(m, p, n):
            if m == "POST":
                seen_journal.extend(events(box.journal))  # what was on disk when the spawn left
                return {"uuid": "op-1"}
            seen_journal.append({"poll_saw": [e.get("status") for e in events(box.journal) if e["event"].startswith("sandbox_op")]})
            return done()
        box = Sandbox(self, script)
        self.assertTrue(box.run().ok)
        self.assertEqual([e.get("status") for e in seen_journal if e.get("event") == "sandbox_op"], ["PENDING"])
        self.assertEqual(seen_journal[-1]["poll_saw"], ["PENDING", "ACCEPTED"], "the accepted id was durable before the first poll")
        self.assertEqual([e.get("status") for e in events(box.journal) if e["event"].startswith("sandbox_op")], ["PENDING", "ACCEPTED", "SUCCESS"])

    def test_no_dispatch_when_the_pending_record_cannot_be_made_durable(self):
        cases = {"disk full": self.failing("sandbox_op"), "I/O error on fsync": self.failing("sandbox_op", code=errno.EIO),
                 "a half-written line": self.failing("sandbox_op", partial=True)}
        for label, writer in cases.items():
            with self.subTest(case=label):
                box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"} if m == "POST" else done())
                with mock.patch.object(ledger_module, "_write_durably", writer), self.assertLogs("attest.ledger", "ERROR") as logs:
                    with self.assertRaises(SandboxError) as caught:
                        box.run()
                self.assertTrue(caught.exception.journal_failed and caught.exception.stops_run)
                self.assertEqual(box.seen, [], "nothing was sent")
                self.assertEqual(box.ledger.sandbox_ops, [], "an operation that was never dispatched is not recorded as one")
                self.assertEqual(box.ledger.halted["kind"], "journal_failure")
                self.assertTrue(any("ATTEST-HALT" in line for line in logs.output))
                self.assertEqual([i["kind"] for i in box.ledger.reconciliation_items()], ["journal"])
                restored = read_journal(box.journal)
                self.assertEqual(restored["spawns_unresolved"], [])

    def test_a_read_back_mismatch_of_the_pending_record_dispatches_nothing(self):
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"})
        real = ledger_module._write_durably

        def corrupting(path, lines):
            if '"event": "sandbox_op"' in lines[-1]:
                return real(path, [lines[-1].replace("PENDING", "PENDXNG")])
            return real(path, lines)
        with mock.patch.object(ledger_module, "_write_durably", corrupting), self.assertLogs("attest.ledger", "ERROR"):
            with self.assertRaises(SandboxError) as caught:
                box.run()
        self.assertTrue(caught.exception.journal_failed)
        self.assertEqual(box.seen, [])

    def test_no_poll_when_the_accepted_id_cannot_be_journaled_and_the_id_is_kept(self):
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-7"} if m == "POST" else done("op-7"))
        with mock.patch.object(ledger_module, "_write_durably", self.failing("sandbox_op_update", status="ACCEPTED")), \
                self.assertLogs("attest.ledger", "ERROR") as logs:
            with self.assertRaises(SandboxError) as caught:
                box.run()
        self.assertEqual((box.posts(), box.gets()), (1, 0))
        self.assertTrue(caught.exception.journal_failed and caught.exception.accepted_unread)
        self.assertEqual(caught.exception.operation_uuid, "op-7")
        self.assertEqual(box.ledger.halted["operation"]["operation_uuid"], "op-7")
        self.assertTrue(any("op-7" in line and "ATTEST-HALT" in line for line in logs.output), "the id reaches the operator's log")
        self.assertIn("op-7", {i.get("operation_uuid") for i in box.ledger.reconciliation_items()})
        restored = read_journal(box.journal)
        self.assertEqual(len(restored["spawns_unresolved"]), 1, "on disk the spawn is PENDING: after a restart it is found by listing")

    def test_a_final_state_that_cannot_be_journaled_stops_the_run(self):
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"} if m == "POST" else done())
        with mock.patch.object(ledger_module, "_write_durably", self.failing("sandbox_op_update", status="SUCCESS")), self.assertLogs("attest.ledger", "ERROR"):
            with self.assertRaises(SandboxError) as caught:
                box.run()
        self.assertTrue(caught.exception.journal_failed)
        self.assertEqual(box.ledger.halted["kind"], "journal_failure")
        self.assertEqual(read_journal(box.journal)["operations_unread"], ["op-1"])

    def test_a_ledger_without_a_journal_dispatches_nothing(self):
        ledger = Ledger()
        box = Sandbox(self, lambda m, p, n: {"uuid": "op-1"}, ledger=ledger)
        with self.assertLogs("attest.ledger", "ERROR"):
            with self.assertRaises(SandboxError) as caught:
                box.run()
        self.assertTrue(caught.exception.journal_failed)
        self.assertEqual(box.seen, [])


class RestartRecovery(unittest.TestCase):
    class Died(BaseException):
        pass

    def store(self, root):
        from attest.app.db import Store
        return Store(root / "attest.db")

    def interrupted(self, script):
        root = temp_dir(self)
        run_dir = root / "runs" / "r1"
        run_dir.mkdir(parents=True)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        box = Sandbox(self, script, ledger=ledger)
        with mock.patch("attest.sandbox.tf_sandboxes.request_json", box.fake):
            with self.assertRaises(self.Died):
                box.ex.run_branch("image-1", {}, STEPS, stage="verify")
        return root, run_dir

    def test_a_process_that_died_between_dispatch_and_answer_leaves_an_unresolved_spawn(self):
        root, run_dir = self.interrupted(lambda m, p, n: self.Died())
        journal = read_journal(run_dir / JOURNAL_FILE)
        self.assertEqual([(s["stage"], s["status"]) for s in journal["spawns_unresolved"]], [("verify", "PENDING")])
        self.assertTrue(journal["reconciliation_required"])
        store = self.store(root)
        store.create_run(run_id="r1", task_id="t", task_title="t", provider="nebius", profile_label="judge-demo", status="running",
                         created_at=utcnow(), out_dir=str(run_dir), requester="x")
        with self.assertLogs("attest.app", "ERROR"):
            outcome = store.finalize_interrupted("r1", per_run_cap=0.5)
        row = store.get_run("r1")
        self.assertEqual(row["error_code"], "reconciliation_required")
        self.assertEqual(len(outcome["spawns_unresolved"]), 1)
        self.assertEqual([h["run_id"] for h in store.active_holds()], ["r1"])

    def test_a_process_that_died_while_polling_leaves_the_accepted_id(self):
        root, run_dir = self.interrupted(lambda m, p, n: {"uuid": "op-9"} if m == "POST" else self.Died())
        journal = read_journal(run_dir / JOURNAL_FILE)
        self.assertEqual(journal["operations_unread"], ["op-9"])
        self.assertEqual(journal["spawns_unresolved"], [])
        self.assertEqual([i["kind"] for i in journal["reconciliation_items"]], ["sandbox_operation"])

    def test_a_model_call_in_flight_is_named_after_a_restart(self):
        run_dir = temp_dir(self)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        ledger.reserve("codex_gateway", "implement", "implement-3", "gpt-6-sol", 0.0)  # the process died with the call in flight
        journal = read_journal(run_dir / JOURNAL_FILE)
        self.assertEqual([(i["kind"], i["stage"]) for i in journal["reconciliation_items"]], [("model_call_in_flight", "implement-3")])

    def test_a_cut_tail_is_repaired_and_the_open_operation_still_found(self):
        root, run_dir = self.interrupted(lambda m, p, n: self.Died())
        with (run_dir / JOURNAL_FILE).open("a", encoding="utf-8") as handle:
            handle.write('{"event": "sandbox_op_update", "op_id": "s1", "status": "ACCE')  # a write cut by the death
        journal = read_journal(run_dir / JOURNAL_FILE)
        self.assertFalse(journal["tail_framed"])
        self.assertEqual(journal["unparsable_lines"], 1)
        self.assertEqual(len(journal["spawns_unresolved"]), 1, "the cut line never counts as an outcome")
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)  # a later writer repairs the tail before appending
        self.assertTrue(read_journal(run_dir / JOURNAL_FILE)["tail_framed"])

    def test_a_clean_interruption_needs_no_hold(self):
        root = temp_dir(self)
        run_dir = root / "runs" / "r2"
        run_dir.mkdir(parents=True)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        store = self.store(root)
        store.create_run(run_id="r2", task_id="t", task_title="t", provider="nebius", profile_label="judge-demo", status="running",
                         created_at=utcnow(), out_dir=str(run_dir), requester="x")
        with self.assertLogs("attest.app", "ERROR"):
            store.finalize_interrupted("r2", per_run_cap=0.5)
        self.assertEqual(store.get_run("r2")["error_code"], "interrupted")
        self.assertEqual(store.active_holds(), [])


# ----------------------------------------------------------------------------------------------------------------------- providers
class _Clock:
    def __init__(self):
        self.now = 1_700_000_000.0

    def time(self):
        return self.now

    def sleep(self, s):
        self.now += s


class GatewayAnswers(unittest.TestCase):
    def client(self, ledger=None):
        from attest.models.codex_gateway import CodexGateway
        from attest.models.pacing import RateGovernor
        clock = _Clock()
        ledger = ledger or journaled(self)[0]
        client = CodexGateway("synthetic-key", ledger, base_url="https://gateway.invalid/v1",
                              governor=RateGovernor(f"r9-{id(ledger)}", time_fn=clock.time, sleep_fn=clock.sleep))
        client._catalog = {"gpt-6-sol": ["medium"], "gpt-6-astra": ["low", "medium"], "gpt-6-luna": ["low"]}
        return client, ledger

    def test_a_5xx_answer_is_uncertain_halts_the_run_and_nothing_is_sent_afterwards(self):
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                client, ledger = self.client()
                posts = []

                def fake(method, url, headers, payload=None, timeout=60, max_bytes=0, _s=status):
                    if url.endswith("/status"):
                        return 200, {}, {}
                    posts.append(url)
                    raise HttpError(_s, {"error": {"message": "upstream"}}, url)
                with mock.patch("attest.models.codex_gateway.request_json", fake):
                    with self.assertRaises(ModelError) as caught:
                        client.structured("implement", "p", SCHEMA, "implement-1")
                    with self.assertRaises(ModelError) as again:
                        client.structured("implement", "p", SCHEMA, "implement-2")
                self.assertTrue(caught.exception.uncertain)
                self.assertEqual(caught.exception.http_status, status)
                self.assertTrue(again.exception.halted)
                self.assertEqual(len(posts), 1)
                call = ledger.model_calls[0]
                self.assertEqual((call.outcome, call.http_status, call.transport_phase, call.request_sent), ("uncertain", status, "response", True))
                self.assertEqual([i["kind"] for i in ledger.reconciliation_items()], ["model_call"])
                self.assertNotIn("gateway.invalid", json.dumps(ledger.to_dict()))

    def test_a_4xx_answer_is_a_definite_rejection(self):
        for status in (400, 401, 403, 404, 408, 413, 422):
            with self.subTest(status=status):
                client, ledger = self.client()

                def fake(method, url, headers, payload=None, timeout=60, max_bytes=0, _s=status):
                    if url.endswith("/status"):
                        return 200, {}, {}
                    raise HttpError(_s, {"error": {"message": "no"}}, url)
                with mock.patch("attest.models.codex_gateway.request_json", fake):
                    with self.assertRaises(ModelError) as caught:
                        client.structured("implement", "p", SCHEMA, "implement-1")
                self.assertFalse(caught.exception.stops_run)
                self.assertEqual(ledger.model_calls[0].outcome, "rejected")
                self.assertIsNone(ledger.halted)
                self.assertEqual(ledger.open_reservations, [])

    def test_reads_are_retried_on_answers_that_ask_for_it(self):
        client, ledger = self.client()
        client._catalog = None
        reads = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            reads.append(url)
            if len(reads) <= 2:
                raise HttpError(503 if len(reads) == 1 else 429, {}, url, {"Retry-After": "2"})
            return 200, {"data": [{"id": "gpt-6-sol", "supported_reasoning_efforts": ["medium"]}]}, {}
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            self.assertIn("gpt-6-sol", client.catalog())
        self.assertEqual(len(reads), 3)
        client._catalog = None
        with mock.patch("attest.models.codex_gateway.request_json", lambda *a, **k: (_ for _ in ()).throw(HttpError(401, {}, "u"))):
            with self.assertRaises(ModelError):
                client.catalog()

    def test_every_call_takes_a_pending_record_and_a_failed_one_sends_nothing(self):
        client, ledger = self.client(ledger=Ledger())
        posts = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            if method == "GET":
                return 200, {}, {}  # reads (the policy) need no pending record
            posts.append(url)
            return 200, {"json": {"result": 1}}, {}
        with mock.patch("attest.models.codex_gateway.request_json", fake), self.assertLogs("attest.ledger", "ERROR"):
            with self.assertRaises(ModelError) as caught:
                client.structured("implement", "p", SCHEMA, "implement-1")
        self.assertEqual(posts, [], "a call without a durable pending record is never sent")
        self.assertTrue(caught.exception.halted)
        self.assertEqual(ledger.halted["kind"], "journal_failure")

    def test_the_policy_window_uses_the_governors_clock(self):
        client, ledger = self.client()
        statuses = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            statuses.append(url)
            return 200, {"limits": {"hourly_requests_enforced": False}}, {}
        with mock.patch("attest.models.codex_gateway.request_json", fake):
            client.adopt_gateway_policy()
            client.describe()
            client.adopt_gateway_policy()
        self.assertEqual(len(statuses), 1, "within the refresh window nothing is read again (revision 8 compared two clocks)")


class TokenFactoryAnswers(unittest.TestCase):
    def provider(self):
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        ledger, journal = journaled(self)
        provider = NebiusTokenFactory("synthetic-key", ledger, base_url="https://tokenfactory.invalid/v1", usd_cap=0.5, max_calls=22)
        provider._sleep = lambda s: None
        return provider, ledger, journal

    def test_a_5xx_answer_is_uncertain_keeps_its_reservation_and_halts(self):
        provider, ledger, journal = self.provider()
        posts = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            posts.append(url)
            raise HttpError(502, {"error": {"message": "bad gateway"}}, url)
        with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
            with self.assertRaises(ModelError) as caught:
                provider.structured("implement", "p", SCHEMA, "implement-1")
            with self.assertRaises(ModelError) as again:
                provider.structured("implement", "p", SCHEMA, "implement-2")
        self.assertTrue(caught.exception.uncertain)
        self.assertTrue(again.exception.halted)
        self.assertEqual(len(posts), 1)
        call = ledger.model_calls[0]
        self.assertEqual((call.settlement, call.outcome, call.http_status), ("unsettled", "uncertain", 502))
        self.assertGreater(ledger.totals()["cost_usd_committed"], 0)
        self.assertEqual(len(ledger.model_calls), 1, "the refused request took no reservation and left no call record")
        self.assertIn("halt", [e["event"] for e in events(journal)])

    def test_a_4xx_answer_settles_at_zero(self):
        provider, ledger, _ = self.provider()
        with mock.patch("attest.models.nebius_tokenfactory.request_json", lambda *a, **k: (_ for _ in ()).throw(HttpError(400, {}, "u"))):
            with self.assertRaises(ModelError) as caught:
                provider.structured("implement", "p", SCHEMA, "implement-1")
        self.assertFalse(caught.exception.stops_run)
        self.assertEqual((ledger.model_calls[0].cost_usd, ledger.model_calls[0].outcome), (0.0, "rejected"))
        self.assertIsNone(ledger.halted)

    def test_a_metering_failure_halts_the_run_after_the_answer(self):
        provider, ledger, _ = self.provider()
        answer = {"model": "m", "choices": [{"message": {"content": "{\"result\": 1}"}, "finish_reason": "stop"}], "usage": {}}
        with mock.patch("attest.models.nebius_tokenfactory.request_json", return_value=(200, answer, {})):
            self.assertEqual(provider.structured("implement", "p", SCHEMA, "implement-1").json, {"result": 1})
        self.assertEqual(ledger.halted["kind"], "metering_unknown")
        self.assertEqual([i["kind"] for i in ledger.reconciliation_items()], ["model_call_billing"])


class GroundingStops(unittest.TestCase):
    def test_an_uncertain_search_ends_grounding_and_the_run(self):
        from attest.core.grounding import Tavily, ground
        tavily = Tavily("synthetic-key")
        tavily._sleep = lambda s: None
        sent = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            sent.append((method, url.rsplit("/", 1)[-1]))
            if method == "GET":
                return 200, {"usage": 1}, {}
            raise HttpError(502, {}, url)
        with mock.patch("attest.core.grounding.request_json", fake):
            record = ground(["q1", "q2", "q3"], tavily)
        self.assertEqual(sent, [("GET", "usage"), ("POST", "search")], "no second search and no usage read after it")
        self.assertEqual(record["uncertain"]["query_index"], 0)
        self.assertIsNone(record["usage_after"])
        self.assertEqual(record["calls"], 1)


# ----------------------------------------------------------------------------------------------------------------------- pipeline
class _Requests:
    def __init__(self):
        self.items, self.stop = [], None

    def add(self, kind, stage):
        self.items.append((kind, stage))
        return len(self.items) - 1


class _RecordingProvider:
    def __init__(self, inner, requests, inject):
        self.inner, self.requests, self.inject, self.name, self.ledger = inner, requests, inject, inner.name, inner.ledger

    def describe(self):
        return self.inner.describe()

    def structured(self, role, prompt, schema, stage):
        self.requests.add("model", stage)
        result = self.inner.structured(role, prompt, schema, stage)
        if self.inject and role == "implement" and stage in ("implement-2", "implement-3"):
            action = {"action": "run_tests" if stage == "implement-2" else "run_python", "path": None, "content": None, "find": None, "replace": None,
                      "start_line": None, "end_line": None, "code": None if stage == "implement-2" else "print(1)", "reason": "check", "summary": None}
            return ModelResult(json=action, text=None, call=result.call)
        return result


class _FailingExecutor(FakeExecutor):
    def __init__(self, ledger, scenario, requests, predicate, accepted_unread=False):
        super().__init__(ledger, scenario)
        self.requests, self.predicate, self.accepted_unread, self.raised = requests, predicate, accepted_unread, False

    def _gate(self, stage):
        index = self.requests.add("sandbox", stage)
        if not self.raised and self.predicate(stage):
            self.raised, self.requests.stop = True, index
            if self.accepted_unread:
                raise SandboxError("operation op-u was accepted but its outcome could not be read", accepted_unread=True, operation_uuid="op-u")
            raise SandboxError("spawn outcome uncertain (RemoteDisconnected); inspect account operations, do not replay", uncertain=True)

    def create_checkpoint(self, image, files, steps, stage, timeout=120, networking=False):
        self._gate(stage)
        return super().create_checkpoint(image, files, steps, stage, timeout, networking)

    def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
        self._gate(stage)
        return super().run_branch(image, files, steps, stage, deletes, timeout, networking)


STAGES = [
    ("checkpoint", "honest", lambda s: s == "checkpoint", {}),
    ("contract-audit witness", "contract_claim_unproven", lambda s: s.startswith("witness-"), {}),
    ("red check", "honest", lambda s: s == "red-1", {}),
    ("implementer run_tests", "honest", lambda s: s.startswith("impl-tests-"), {"inject": True}),
    ("implementer run_python", "honest", lambda s: s.startswith("impl-python-"), {"inject": True}),
    ("verification", "honest", lambda s: s == "verify", {}),
    ("repository suite", "honest", lambda s: s == "existing", {}),
    ("held-out suite", "honest", lambda s: s == "heldout", {"heldout": True}),
    ("mutant", "honest", lambda s: s.startswith("mutant-"), {}),
    ("adversarial tests", "honest", lambda s: s == "breaker-tests", {}),
    ("adversarial tests, accepted but unread", "honest", lambda s: s == "breaker-tests", {"accepted_unread": True}),
    ("arbitration candidate re-run", "arb_clear", lambda s: s == "arbitrate-adversarial-candidate", {}),
    ("arbitration base re-run", "arb_clear", lambda s: s == "arbitrate-adversarial-base", {}),
    ("arbitration mutant re-run", "arb_refactor", lambda s: s.startswith("arbitrate-adversarial-") and not s.endswith(("-candidate", "-base")), {}),
    ("sealed arbitration re-run", "sealed_one_timeout", lambda s: s == "arbitrate-sealed-candidate", {}),
]


def run_stopping(test, scenario, predicate, options, mutant_workers=1):
    tmp = temp_dir(test)
    ledger, requests = Ledger(), _Requests()
    task = TaskSpec.load(TASK)
    if options.get("heldout"):
        task.heldout_tests = {"tests/test_heldout.py": HELDOUT_SRC}
    provider = _RecordingProvider(FakeProvider(ledger, scenario), requests, options.get("inject"))
    executor = _FailingExecutor(ledger, scenario, requests, predicate, options.get("accepted_unread"))
    pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=tmp, max_turns=6, max_mutants=6,
                        mutant_workers=mutant_workers, tavily=None, profile_label="test")
    with test.assertLogs("attest.ledger", "ERROR"):
        bundle = quiet(pipeline.run)
    return bundle, requests, pipeline


class PipelineStopsEverywhere(unittest.TestCase):
    def test_an_uncertain_sandbox_operation_ends_the_run_at_every_stage(self):
        for label, scenario, predicate, options in STAGES:
            with self.subTest(stage=label):
                bundle, requests, pipeline = run_stopping(self, scenario, predicate, options)
                self.assertIsNotNone(requests.stop, "the failure was reached")
                self.assertEqual(requests.items[requests.stop + 1:], [], "no model call or sandbox request after it")
                self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
                reasons = bundle["verdict"]["reasons"]
                self.assertTrue(reasons[0].startswith("stopped for reconciliation at "), reasons[0])
                self.assertFalse(any("rerun" in r.lower() or "re-run the" in r.lower() or "run again" in r.lower() for r in reasons), reasons)
                record = bundle["reconciliation"]
                self.assertTrue(record["required"])
                self.assertGreaterEqual(len(record["items"]), 1)
                self.assertEqual(record["halt"]["kind"], "uncertain_operation")
                from attest.core.exhibits import decision
                verdict_decision = decision(bundle)
                self.assertEqual(verdict_decision["statement"], "This run stopped for reconciliation.")
                self.assertIn(f"At stage {record['halt']['stage']} ", verdict_decision["explanation"], "the stage of the operation, not a label")
                self.assertNotIn("Start a new run", " ".join(verdict_decision["decide"]))
                proof = (pipeline.out_dir / "PROOF.md").read_text(encoding="utf-8")
                self.assertIn("12b. Reconciliation", proof)
                report = check_bundle(pipeline.out_dir)
                self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
                self.assertEqual(report["protocol"], 5)

    def test_parallel_mutants_stop_dispatching_after_one_is_uncertain(self):
        bundle, requests, _ = run_stopping(self, "honest", lambda s: s.startswith("mutant-"), {}, mutant_workers=1)
        self.assertEqual([k for k, s in requests.items if s.startswith("mutant-")], ["sandbox"], "only the failing mutant was dispatched")
        self.assertNotIn(("model", "drift-audit"), requests.items)

    def test_an_honest_run_is_verified_and_needs_no_reconciliation(self):
        tmp = temp_dir(self)
        ledger = Ledger()
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=FakeProvider(ledger, "honest"), executor=FakeExecutor(ledger, "honest"), ledger=ledger,
                            out_dir=tmp, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="test")
        bundle = quiet(pipeline.run)
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")
        self.assertEqual((bundle["reconciliation"]["required"], bundle["reconciliation"]["items"]), (False, []))
        self.assertTrue(check_bundle(pipeline.out_dir)["fully_verified"])

    def test_an_uncertain_tavily_search_ends_the_run_at_grounding(self):
        from attest.core.grounding import Tavily
        tmp = temp_dir(self)
        ledger, requests = Ledger(), _Requests()

        class Grounded(FakeProvider):
            def structured(self, role, prompt, schema, stage):
                result = super().structured(role, prompt, schema, stage)
                if role == "spec":
                    result.json["external_references_needed"] = ["the duration unit grammar"]
                return result
        provider = _RecordingProvider(Grounded(ledger, "honest"), requests, False)
        tavily = Tavily("synthetic-key")
        sent = []

        def fake(method, url, headers, payload=None, timeout=60, max_bytes=0):
            sent.append(method)
            if method == "GET":
                return 200, {}, {}
            raise lost()
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=provider, executor=_FailingExecutor(ledger, "honest", requests, lambda s: False),
                            ledger=ledger, out_dir=tmp, max_turns=4, tavily=tavily, profile_label="test")
        with mock.patch("attest.core.grounding.request_json", fake), self.assertLogs("attest.ledger", "ERROR"):
            bundle = quiet(pipeline.run)
        self.assertEqual(sent, ["GET", "POST"])
        # grounding follows the specification and its contract audit; nothing is sent after the search (no sealing, no sandbox)
        self.assertEqual([s for _, s in requests.items], ["checkpoint", "spec", "contract-audit"])
        self.assertEqual(bundle["reconciliation"]["halt"]["stage"], "ground")
        self.assertEqual([i["kind"] for i in bundle["reconciliation"]["items"]], ["search"])

    def test_an_uncertain_model_call_still_stops_every_stage(self):
        # revision 8's guarantee for model calls holds through the new path (ask converts the error and halts the ledger)
        tmp = temp_dir(self)
        ledger = Ledger()

        class Uncertain(FakeProvider):
            def structured(self, role, prompt, schema, stage):
                if stage == "drift-audit":
                    raise ModelError("inference outcome uncertain (timed out); not retried", uncertain=True)
                return super().structured(role, prompt, schema, stage)
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=Uncertain(ledger, "honest"), executor=FakeExecutor(ledger, "honest"), ledger=ledger,
                            out_dir=tmp, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="test")
        with self.assertLogs("attest.ledger", "ERROR"):
            bundle = quiet(pipeline.run)
        self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
        self.assertIn("outcome uncertain; not retried", bundle["verdict"]["reasons"][0])
        self.assertEqual(bundle["arbitration"], None)
        self.assertEqual([i["kind"] for i in bundle["reconciliation"]["items"]], ["unrecorded_operation"])


# ----------------------------------------------------------------------------------------------------------------------- checker
class CheckerReconciliation(unittest.TestCase):
    def halted_run(self):
        bundle, requests, pipeline = run_stopping(self, "honest", lambda s: s == "breaker-tests", {})
        return pipeline.out_dir

    def rewrite(self, run_dir, change):
        from tests.test_audit_core import rewrite_bundle
        rewrite_bundle(run_dir, change)

    def failed(self, run_dir):
        return {c["name"] for c in check_bundle(run_dir)["checks"] if c["ok"] is False}

    def test_the_genuine_halted_bundle_passes(self):
        report = check_bundle(self.halted_run())
        self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
        self.assertTrue(report["evidence_complete"])

    def test_forged_reconciliation_records_are_refused(self):
        forgeries = {
            "record removed": lambda b: b.pop("reconciliation"),
            "required cleared": lambda b: b["reconciliation"].update(required=False, items=[]),
            "verdict raised": lambda b: b["verdict"].update(verdict="VERIFIED", reasons=[]),
            "items dropped": lambda b: b["reconciliation"].update(items=[]),
            "protocol downgraded": lambda b: b["evidence_protocol"].update(version=4),
        }
        for label, change in forgeries.items():
            with self.subTest(forgery=label):
                run_dir = self.halted_run()
                self.rewrite(run_dir, change)
                self.assertTrue(self.failed(run_dir) & {"reconciliation_record", "evidence_protocol", "verified_has_no_reasons", "verdict_derivation"},
                                self.failed(run_dir))

    def test_a_historical_bundle_that_went_on_after_an_uncertain_mutant_is_warned_about(self):
        run_dir = ROOT / "reports" / "attest-reliability-2026-10-17" / "evaluation-paced-codex" / "runs" / "balanced-brackets-attest-a1-20261017T121900586528Z"
        if not run_dir.is_dir():
            self.skipTest("the recorded evidence is not in this checkout")
        report = check_bundle(run_dir)
        self.assertTrue(report["ok"])
        self.assertEqual(report["verdict"], "VERIFIED")
        warning = next(c for c in report["checks"] if c["name"] == "reconciliation_record")
        self.assertIsNone(warning["ok"])
        self.assertIn("recorded before revision 9", warning["detail"])


# ----------------------------------------------------------------------------------------------------------------------- console
class ConsoleHolds(unittest.TestCase):
    def setUp(self):
        from attest.app.db import Store
        from attest.app.worker import Worker
        self.tmp = temp_dir(self)
        self.store = Store(self.tmp / "attest.db")
        with mock.patch.object(Worker, "_loop", lambda self: None):
            self.worker = Worker(self.store, self.tmp, TASK.parent.parent, max_turns=6)
        self.per_run: dict[str, _Requests] = {}

    def runtime(self, stops: dict):
        def build(run_id, provider_name, ledger):
            requests = self.per_run.setdefault(run_id, _Requests())
            predicate = stops.get(run_id, lambda s: False)
            return (_RecordingProvider(FakeProvider(ledger, "honest"), requests, False), _FailingExecutor(ledger, "honest", requests, predicate), None)
        return build

    def queued(self, *run_ids):
        for run_id in run_ids:
            self.store.create_run(run_id=run_id, task_id="durationkit-units-001", task_title="T", provider="codex", profile_label="development",
                                  status="queued", stage="queued", created_at=utcnow(), requester="team")

    def test_a_held_run_pauses_the_worker_until_an_operator_clears_it(self):
        from attest.app.worker import ReconciliationHold
        self.queued("r1", "r2")
        with mock.patch.object(self.worker, "build_runtime", self.runtime({"r1": lambda s: s == "verify"})), self.assertLogs(level="ERROR"):
            quiet(self.worker._execute, "r1", TASK, "codex", "development")
            quiet(self.worker._execute, "r2", TASK, "codex", "development")
        first, second = self.store.get_run("r1"), self.store.get_run("r2")
        self.assertEqual((first["status"], first["error_code"], first["verdict"]), ("error", "reconciliation_required", "ERROR"))
        self.assertEqual((second["status"], second["error_code"]), ("error", "paused_for_reconciliation"))
        self.assertNotIn("r2", self.per_run, "no provider or executor was built for the paused run")
        holds = self.store.active_holds()
        self.assertEqual([h["run_id"] for h in holds], ["r1"])
        self.assertGreaterEqual(len(holds[0]["items"]), 1)
        with mock.patch.object(self.worker, "ensure_alive", return_value=True):
            with self.assertRaises(ReconciliationHold):
                self.worker.enqueue("durationkit-units-001", "codex", "team", "development")
        from attest.app.db import Store
        self.assertEqual(len(Store(self.tmp / "attest.db").active_holds()), 1, "the hold survives a restart")
        with self.assertRaises(ValueError):
            self.store.clear_hold(holds[0]["hold_id"], "")
        self.assertTrue(self.store.clear_hold(holds[0]["hold_id"], "op found FAILED in the account's operations; nothing to settle"))
        self.queued("r3")
        with mock.patch.object(self.worker, "build_runtime", self.runtime({})):
            quiet(self.worker._execute, "r3", TASK, "codex", "development")
        self.assertEqual(self.store.get_run("r3")["status"], "finished")

    def test_retention_keeps_a_held_run(self):
        self.queued("r1")
        with mock.patch.object(self.worker, "build_runtime", self.runtime({"r1": lambda s: s == "verify"})), self.assertLogs(level="ERROR"):
            quiet(self.worker._execute, "r1", TASK, "codex", "development")
        out_dir = Path(self.store.get_run("r1")["out_dir"])
        self.assertEqual(self.store.prune_runs(self.tmp / "runs", keep=0, keep_errors=0), [])
        self.assertTrue(out_dir.is_dir())

    def test_the_api_refuses_admission_and_reports_the_hold(self):
        from fastapi.testclient import TestClient
        import importlib
        env = {"ATTEST_DATA_DIR": str(self.tmp / "data"), "ATTEST_EXAMPLES_DIR": str(TASK.parent.parent), "ATTEST_ADMIN_TOKEN": "synthetic-team-token",
               "ATTEST_IMPORT_DIRS": str(self.tmp / "none")}
        with mock.patch.dict(os.environ, env):
            import attest.app.server as server
            server = importlib.reload(server)
            server.store.add_hold("held-run", "stopped for reconciliation (offline test)", [{"kind": "sandbox_spawn"}])
            client = TestClient(server.app)
            health = client.get("/api/health").json()
            self.assertEqual(health["reconciliation"]["holds_open"], 1)
            self.assertFalse(health["reconciliation"]["accepting_runs"])
            self.assertNotIn("held_runs", health["reconciliation"], "held run ids only for the team")
            team = client.get("/api/health", headers={"X-Attest-Token": "synthetic-team-token"}).json()
            self.assertEqual(team["reconciliation"]["held_runs"], ["held-run"])
            answer = client.post("/api/runs", json={"task_id": "durationkit-units-001", "provider": "nebius"}, headers={"X-Attest-Confirm": "start-run"})
            self.assertEqual(answer.status_code, 503)
            self.assertIn("reconciled", answer.json()["detail"])
            self.assertEqual(server.store.list_runs(include_team=True), [], "nothing was queued")
            server.worker.stop()


# ----------------------------------------------------------------------------------------------------------------------- harness and CLI
class HarnessStops(unittest.TestCase):
    def harness(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_evaluation_r9", ROOT / "scripts" / "run_evaluation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_a_halted_cell_is_not_judged_and_stops_the_batch(self):
        harness = self.harness()
        tmp = temp_dir(self)
        requests = _Requests()
        (tmp / "heldout.py").write_text(HELDOUT_SRC, encoding="utf-8")
        cell = {"task": "durationkit-units-001", "system": "attest", "attempt": 1, "task_path": str(TASK), "heldout": str(tmp / "heldout.py"),
                "ground_truth": "satisfiable", "scheduled_index": 0}
        budget = harness.Budget(None, 0.5)
        with mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: _RecordingProvider(FakeProvider(ledger, "honest"), requests, False)), \
             mock.patch.object(harness, "executor_for", lambda ledger: _FailingExecutor(ledger, "honest", requests, lambda s: s == "breaker-tests")), \
             self.assertLogs("attest.ledger", "ERROR"):
            row = quiet(harness.run_cell, cell, budget, "codex", 0.5, None, tmp / "runs", 6, Path("/"))
        self.assertEqual(requests.items[requests.stop + 1:], [], "no judge, no drift audit")
        self.assertTrue(row["uncertain"])
        self.assertTrue(row["halted"])
        self.assertIn("not judged", row["held_out_summary"])
        self.assertGreaterEqual(len(row["reconciliation"]), 1)
        self.assertIn("stopped for reconciliation", budget.snapshot()["stopped"])
        self.assertEqual(budget.try_reserve(), budget.snapshot()["stopped"], "no further cell starts")

    def test_a_halt_in_one_cell_halts_every_cell_in_flight(self):
        harness = self.harness()
        budget = harness.Budget(None, 0.5)
        first, second = Ledger(), Ledger()
        budget.register(first)
        budget.register(second)
        with self.assertLogs("attest.ledger", "ERROR"):
            first.halt("uncertain_operation", "a spawn's answer was lost", stage="mutant-1")
        self.assertEqual(second.halted["kind"], "batch_stop")
        with self.assertRaises(RunHalted):
            second.admit("sandboxes", "verify")

    def test_the_judge_journals_its_operation_next_to_the_run_directory(self):
        harness = self.harness()
        tmp = temp_dir(self)
        (tmp / "heldout.py").write_text(HELDOUT_SRC, encoding="utf-8")
        cell = {"task": "durationkit-units-001", "system": "attest", "attempt": 1, "task_path": str(TASK), "heldout": str(tmp / "heldout.py"),
                "ground_truth": "satisfiable", "scheduled_index": 0}
        with mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: FakeProvider(ledger, "honest")), \
             mock.patch.object(harness, "executor_for", lambda ledger: FakeExecutor(ledger, "honest")):
            row = quiet(harness.one_system, cell, "codex", 0.5, None, tmp / "runs", 4, Path("/"))
        self.assertEqual(row["verdict"], "VERIFIED")
        self.assertTrue((tmp / "runs" / f"{row['run_id']}.judge.jsonl").is_file())
        self.assertTrue(check_bundle(row["out_dir"])["ok"], "the sealed run directory is untouched by the judge")


class CliReconcile(unittest.TestCase):
    def test_reconcile_lists_a_halted_run_and_holds_can_be_listed_and_cleared(self):
        from attest import cli
        bundle, requests, pipeline = run_stopping(self, "honest", lambda s: s == "verify", {})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["reconcile", str(pipeline.out_dir)]), 4)
        listed = json.loads(out.getvalue())
        self.assertTrue(listed["required"])
        self.assertEqual(listed["source"], "proof_bundle.json")
        from attest.app.db import Store
        db = temp_dir(self) / "attest.db"
        with self.assertLogs("attest.app", "ERROR"):
            hold = Store(db).add_hold("r1", "offline test", [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["holds", "--db", str(db)]), 0)
        self.assertEqual([h["hold_id"] for h in json.loads(out.getvalue())["holds"]], [hold])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["holds", "--db", str(db), "--clear", hold]), 2, "a hold is cleared only with a note")
            self.assertEqual(cli.main(["holds", "--db", str(db), "--clear", hold, "--note", "reconciled offline"]), 0)
        self.assertEqual(Store(db).active_holds(), [])


class SelfContained(unittest.TestCase):
    def test_the_gateway_client_needs_an_explicit_url_in_the_offline_suite(self):
        from attest.models.codex_gateway import CodexGateway
        with self.assertRaises(ModelError):
            CodexGateway("synthetic-key", Ledger())  # no private configuration is visible here (tests/_isolation.py)


if __name__ == "__main__":
    unittest.main()
