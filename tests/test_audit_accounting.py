"""Acceptance tests for the accounting repairs of the 19 Oct 2026 audit.

AC-01: every process start rebuilds the batch's starting committed total from disk (each completed row once, each run directory no
row owns once); AC-02: a finished bundle whose row was never persisted is recovered from its ledger totals; AC-03: a USD reservation
is journaled durably before dispatch, or the request is not sent; AC-04: a successful answer without usable metering keeps its
reservation unsettled and stops further paid calls; AC-07: a resumed batch runs exactly its registered configuration or refuses
before anything is constructed. Offline only: fake providers and transports, temporary directories, a socket tripwire; no
credentials are read.
"""

import argparse
import contextlib
import io
import json
import os
import shutil
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import attest.ledger as ledger_module
from attest.ledger import JOURNAL_FILE, Ledger, LedgerError, ModelCall, read_journal, utcnow
from attest.models.base import ModelError, extract_usage, token_count, usage_problem
from attest.models.nebius_tokenfactory import NebiusTokenFactory
from tests.test_budget import PaidFakeProvider, quiet
from tests.test_verification import FakeExecutor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_evaluation as harness  # noqa: E402
import render_evaluation  # noqa: E402

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"], "additionalProperties": False}
SUPER = "nvidia/nemotron-3-super-120b-a12b"
REQUEST = "attest.models.nebius_tokenfactory.request_json"


def _forbid_network(*args, **kwargs):
    raise AssertionError("network access is forbidden in the offline accounting tests")


_TRIPWIRE = [mock.patch.object(socket.socket, "connect", _forbid_network), mock.patch.object(socket, "create_connection", _forbid_network)]


def setUpModule():
    for patcher in _TRIPWIRE:
        patcher.start()


def tearDownModule():
    for patcher in _TRIPWIRE:
        patcher.stop()


def answer(usage="absent", content='{"x":1}', finish="stop") -> dict:
    """A fake HTTP 200 chat completion; `usage="absent"` leaves the usage object out entirely."""
    body = {"model": SUPER, "choices": [{"message": {"content": content}, "finish_reason": finish}]}
    if usage != "absent":
        body["usage"] = usage
    return body


def _call(**over) -> ModelCall:
    base = dict(provider="nebius_tokenfactory", role="seal", stage="seal-1", requested_model="m", requested_effort=None, returned_model="m",
                returned_effort=None, started_at_utc=utcnow(), elapsed_ms=1, gateway_duration_ms=None, prompt_chars=10, tokens_in=10,
                tokens_out=5, tokens_cached=0, usage_raw={}, cost_usd=0.01, cost_note="t", ok=True, reserved_usd=0.05)
    base.update(over)
    return ModelCall(**base)


class FailingHandle:
    """Wraps a real journal handle and raises OSError at one step (write, flush or close); the real handle is always closed."""

    def __init__(self, real, fail_at: str):
        self._real, self._fail_at = real, fail_at

    def write(self, text):
        if self._fail_at == "write":
            raise OSError(28, "No space left on device (fake)")
        return self._real.write(text)

    def flush(self):
        if self._fail_at == "flush":
            raise OSError(5, "Input/output error on flush (fake)")
        return self._real.flush()

    def fileno(self):
        return self._real.fileno()

    def close(self):
        try:
            if self._fail_at == "close":
                raise OSError(5, "Input/output error on close (fake)")
        finally:
            self._real.close()


@contextlib.contextmanager
def journal_failure(step: str):
    """Make the next journal append fail at `step`: open, write, flush, fsync or close."""
    real_open = ledger_module._open_journal
    if step == "open":
        with mock.patch("attest.ledger._open_journal", side_effect=OSError(28, "No space left on device (fake)")):
            yield
    elif step == "fsync":
        with mock.patch("attest.ledger.os.fsync", side_effect=OSError(5, "fsync failed (fake)")):
            yield
    else:
        with mock.patch("attest.ledger._open_journal", side_effect=lambda path: FailingHandle(real_open(path), step)):
            yield


class Interrupted(BaseException):
    """Simulates the process dying: not an Exception, so run_cell's attempt-retaining handler does not catch it, the future
    re-raises it in the main thread and the row is never persisted."""


# ----------------------------------------------------------------------------- AC-03: durable reservation before dispatch
class ReservationDurability(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ac03-"))
        self.sink = self.tmp / JOURNAL_FILE

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _provider(self, attach=True, usd_cap=0.5):
        ledger = Ledger()
        if attach:
            ledger.attach_sink(self.sink)
        return NebiusTokenFactory("offline-fake-key", ledger, usd_cap=usd_cap), ledger

    def test_reserve_without_a_sink_is_refused_and_records_nothing(self):
        ledger = Ledger()
        with self.assertRaises(LedgerError) as cm:
            ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
        self.assertIn("no journal sink", str(cm.exception))
        self.assertEqual(ledger.open_reservations, [])
        self.assertEqual(ledger.totals()["cost_usd_committed"], 0)
        provider, ledger = self._provider(attach=False)
        with mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 1, "completion_tokens": 1}), {})) as request:
            for _ in range(2):  # the second request is refused by the halt, still without any HTTP call
                with self.assertRaises(ModelError) as cm:
                    provider.structured("seal", "prompt", SCHEMA, "seal")
                self.assertFalse(cm.exception.uncertain)  # definite: nothing left the process
        self.assertIn("could not be journaled", str(cm.exception))
        self.assertEqual(request.call_count, 0)
        self.assertEqual(ledger.model_calls, [])
        self.assertTrue(provider.halted)

    def test_reservation_failure_at_every_step_sends_nothing(self):
        for step in ("open", "write", "flush", "fsync", "close"):
            with self.subTest(step=step):
                shutil.rmtree(self.tmp, ignore_errors=True)
                provider, ledger = self._provider()  # the sink attaches fine; the failure strikes the reservation's append
                with journal_failure(step), mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 1, "completion_tokens": 1}), {})) as request:
                    with self.assertRaises(ModelError) as cm:
                        provider.structured("seal", "prompt", SCHEMA, "seal-1")
                self.assertFalse(cm.exception.uncertain, step)
                self.assertIn("could not be journaled", str(cm.exception))
                self.assertIn("was not sent", str(cm.exception))
                self.assertEqual(request.call_count, 0, step)
                self.assertEqual(ledger.open_reservations, [])
                self.assertEqual(ledger.model_calls, [])
                self.assertTrue(provider.halted)
                # with the disk healthy again the instance still refuses: nothing is dispatched blind for the rest of the run
                with mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 1, "completion_tokens": 1}), {})) as request:
                    with self.assertRaises(ModelError) as cm:
                        provider.structured("seal", "prompt", SCHEMA, "seal-2")
                self.assertIn("no further paid requests", str(cm.exception))
                self.assertEqual(request.call_count, 0)
                journal = read_journal(self.sink)
                if step in ("open", "write"):
                    self.assertEqual(journal["open_reservations"], 0)  # the line never reached the file
                else:
                    # the line reached the file before the failing step: the journal then holds a reservation for a request that was
                    # never sent, which a restart counts at its bound (conservative, never an understatement)
                    self.assertLessEqual(journal["open_reservations"], 1)

    def test_the_auditors_injection_point_is_refused(self):
        # reports/attest-audit-2026-10-19/accounting-repro.py (AC-03) patches Path.open after a successful attach_sink
        ledger = Ledger()
        ledger.attach_sink(self.sink)
        with mock.patch.object(Path, "open", side_effect=OSError("offline fake disk full")):
            with self.assertRaises(LedgerError):
                ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
        self.assertEqual(ledger.totals()["cost_usd_committed"], 0)  # nothing recorded in memory: nothing was sent
        self.assertEqual(read_journal(self.sink)["cost_usd_committed"], 0)  # and nothing in the journal: the two agree

    def test_reservation_is_in_the_journal_and_fsynced_before_the_request_leaves(self):
        provider, ledger = self._provider()
        synced, seen = [], {}
        real_fsync = os.fsync

        def spy_fsync(fd):
            synced.append(fd)
            return real_fsync(fd)

        def transport(method, url, headers, payload=None, timeout=60, max_bytes=0):
            seen["journal_at_dispatch"] = read_journal(self.sink)
            seen["fsyncs_at_dispatch"] = len(synced)
            return 200, answer({"prompt_tokens": 1000, "completion_tokens": 200}), {}
        with mock.patch("attest.ledger.os.fsync", side_effect=spy_fsync), mock.patch(REQUEST, transport):
            result = provider.structured("seal", "prompt", SCHEMA, "seal-1")
        self.assertEqual(result.json, {"x": 1})
        self.assertEqual(seen["journal_at_dispatch"]["open_reservations"], 1)  # written before the request left
        self.assertGreaterEqual(seen["fsyncs_at_dispatch"], 1)  # and fsynced before it left
        self.assertEqual(read_journal(self.sink)["open_reservations"], 0)  # the call record closed it afterwards
        self.assertEqual(ledger.model_calls[-1].settlement, "known")

    def test_failed_settlement_write_keeps_the_durable_reservation(self):
        ledger = Ledger()
        ledger.attach_sink(self.sink)
        rid = ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)
        with journal_failure("write"):
            ledger.add_call(_call(cost_usd=0.01, reserved_usd=0.05), rid)  # does not raise: the in-memory record is kept
        self.assertEqual(len(ledger.model_calls), 1)
        self.assertEqual(ledger.open_reservations, [])
        self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], 0.01)  # the process knows the real cost
        self.assertEqual(ledger.totals()["journal_failures"], 1)
        journal = read_journal(self.sink)  # a restart reads the journal: the reservation is still open and counts at its bound
        self.assertEqual((journal["model_calls"], journal["open_reservations"]), (0, 1))
        self.assertAlmostEqual(journal["cost_usd_committed"], 0.05)
        # the same through the provider: the answer is returned, the journal keeps the bound
        provider, ledger = self._provider()
        with journal_failure("open"):
            pass  # the reservation itself must succeed; only the settlement append fails below
        with mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 1000, "completion_tokens": 200}), {})):
            real_open = ledger_module._open_journal
            appends = []

            def fail_second_append(path):
                appends.append(path)
                if len(appends) == 2:  # 1: the reservation, 2: the call record
                    raise OSError(28, "No space left on device (fake)")
                return real_open(path)
            with mock.patch("attest.ledger._open_journal", side_effect=fail_second_append):
                result = provider.structured("seal", "prompt", SCHEMA, "seal-1")
        self.assertEqual(result.json, {"x": 1})
        self.assertEqual(ledger.model_calls[-1].settlement, "known")
        self.assertEqual(ledger.totals()["journal_failures"], 1)
        journal = read_journal(self.sink)
        self.assertEqual(journal["open_reservations"], 1)
        self.assertAlmostEqual(journal["cost_usd_committed"], ledger.model_calls[-1].reserved_usd)


# ----------------------------------------------------------------------------- AC-04: no settlement without metering
class MeteringFailures(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ac04-"))
        self.count = 0

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _provider(self, usd_cap=0.5):
        self.count += 1
        ledger = Ledger()
        ledger.attach_sink(self.tmp / str(self.count) / JOURNAL_FILE)
        return NebiusTokenFactory("offline-fake-key", ledger, usd_cap=usd_cap), ledger

    def test_three_answers_without_usage_are_not_all_accepted(self):
        # the audit's reproduction: a $0.02 per-run cap and three fake HTTP 200 answers that carry no usage object
        provider, ledger = self._provider(usd_cap=0.02)
        outcomes = []
        with mock.patch(REQUEST, return_value=(200, answer(), {})) as request:
            for _ in range(3):
                try:
                    outcomes.append(provider.structured("seal", "prompt", SCHEMA, "seal").json)
                except ModelError as error:
                    outcomes.append(str(error))
        self.assertEqual(request.call_count, 1)  # the second and third requests were refused before dispatch
        self.assertEqual(outcomes[0], {"x": 1})  # the generated answer is still returned
        self.assertIn("metering failed", outcomes[1])
        self.assertIn("pending reconciliation", outcomes[1])
        self.assertEqual([c.settlement for c in ledger.model_calls], ["unsettled"])
        call = ledger.model_calls[0]
        self.assertIsNone(call.cost_usd)
        self.assertTrue(call.ok)
        self.assertIn("metering failed", call.cost_note)
        self.assertAlmostEqual(call.reserved_usd, 0.014701)
        self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], call.reserved_usd)  # committed USD equals the first reservation
        self.assertAlmostEqual(provider.spent_usd(), call.reserved_usd)  # the per-run cap counts the unsettled reservation
        self.assertEqual(ledger.totals()["uncertain_unpriced_calls"], 1)
        self.assertIn("metering failed", provider.describe()["halted"])

    def test_each_metering_defect_keeps_the_reservation_unsettled(self):
        cases = {"absent": "absent", "empty": {}, "one counter only": {"prompt_tokens": 100},
                 "malformed counters": {"prompt_tokens": "100", "completion_tokens": None},
                 "negative counter": {"prompt_tokens": -1, "completion_tokens": 5},
                 "boolean counters": {"prompt_tokens": True, "completion_tokens": False},
                 "not an object": [1000, 200], "non-integral float": {"prompt_tokens": 12.5, "completion_tokens": 3}}
        for label, usage in cases.items():
            with self.subTest(usage=label):
                provider, ledger = self._provider()
                with mock.patch(REQUEST, return_value=(200, answer(usage), {})) as request:
                    result = provider.structured("seal", "prompt", SCHEMA, "seal-1")
                    with self.assertRaises(ModelError) as cm:
                        provider.structured("implement", "prompt", SCHEMA, "implement-1")
                self.assertEqual(result.json, {"x": 1})
                self.assertEqual(request.call_count, 1, label)
                self.assertIn("metering failed", str(cm.exception))
                self.assertIn("paid calls of this run stop pending reconciliation", str(cm.exception))
                call = ledger.model_calls[0]
                self.assertEqual((call.settlement, call.cost_usd, call.ok), ("unsettled", None, True), label)
                self.assertIn("metering failed", call.cost_note)
                self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], call.reserved_usd, places=6)
                self.assertAlmostEqual(provider.spent_usd(), call.reserved_usd, places=6)
                self.assertTrue(provider.halted, label)

    def test_explicit_zero_counters_settle_as_known_zero_and_do_not_halt(self):
        provider, ledger = self._provider()
        with mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 0, "completion_tokens": 0}), {})) as request:
            first = provider.structured("seal", "prompt", SCHEMA, "seal-1")
            second = provider.structured("seal", "prompt", SCHEMA, "seal-2")
        self.assertEqual((first.json, second.json), ({"x": 1}, {"x": 1}))
        self.assertEqual(request.call_count, 2)
        self.assertEqual([(c.settlement, c.cost_usd) for c in ledger.model_calls], [("known", 0.0), ("known", 0.0)])
        self.assertEqual(ledger.totals()["cost_usd_committed"], 0.0)
        self.assertIsNone(provider.halted)

    def test_valid_usage_prices_the_call_from_the_table(self):
        provider, ledger = self._provider()
        with mock.patch(REQUEST, return_value=(200, answer({"prompt_tokens": 1000, "completion_tokens": 200}), {})):
            provider.structured("seal", "prompt", SCHEMA, "seal-1")
        call = ledger.model_calls[0]
        self.assertEqual((call.tokens_in, call.tokens_out, call.settlement), (1000, 200, "known"))
        self.assertAlmostEqual(call.cost_usd, 1000 / 1e6 * 0.30 + 200 / 1e6 * 0.90, places=9)
        self.assertIsNone(provider.halted)

    def test_metering_failure_on_a_reasoning_runaway_blocks_the_low_effort_retry(self):
        provider, ledger = self._provider()
        with mock.patch(REQUEST, return_value=(200, answer(content="", finish="length"), {})) as request:
            with self.assertRaises(ModelError) as cm:
                provider.structured("seal", "prompt", SCHEMA, "seal-1")
        self.assertIn("schema", str(cm.exception))
        self.assertEqual(request.call_count, 1)  # no low-effort retry: that would be a paid call after a metering failure
        self.assertEqual([c.settlement for c in ledger.model_calls], ["unsettled"])
        self.assertTrue(provider.halted)

    def test_token_counters_reject_malformed_values(self):
        self.assertEqual([token_count(v) for v in (5, 5.0, 0)], [5, 5, 0])
        self.assertEqual([token_count(v) for v in (True, -1, float("nan"), float("inf"), "5", 2.5, None, [])], [None] * 8)
        self.assertEqual(extract_usage({"input_tokens": "x", "prompt_tokens": 7, "completion_tokens": 3}), (7, 3, None))
        self.assertEqual(extract_usage({"prompt_tokens": 7, "completion_tokens": 3, "prompt_tokens_details": {"cached_tokens": 2.0}}), (7, 3, 2))
        self.assertEqual(extract_usage(None), (None, None, None))
        self.assertIn("no usage", usage_problem(None, None, None))
        self.assertIn("empty", usage_problem({}, None, None))
        self.assertIn("not an object", usage_problem([1], None, None))
        self.assertIn("output", usage_problem({"prompt_tokens": 1}, 1, None))
        self.assertNotIn("input (", usage_problem({"prompt_tokens": 1}, 1, None))
        self.assertIn("input", usage_problem({"completion_tokens": 1}, None, 1))
        self.assertIsNone(usage_problem({"prompt_tokens": 0, "completion_tokens": 0}, 0, 0))


# ----------------------------------------------------------------------------- AC-01 / AC-02: directories no row owns
class UnownedRunDirectories(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ac01-"))
        self.runs = self.tmp / "runs"
        self.runs.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _journal_orphan(self, name: str, open_usd: float, known_usd: float | None = None) -> Path:
        run_dir = self.runs / name
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        if known_usd is not None:
            rid = ledger.reserve("nebius_tokenfactory", "spec", "spec", "m", known_usd * 2)
            ledger.add_call(_call(role="spec", stage="spec", cost_usd=known_usd, reserved_usd=known_usd * 2), rid)
        ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", open_usd)  # the process dies with this request in flight
        return run_dir

    def test_every_process_start_counts_each_orphan_once_and_new_orphans_too(self):
        self._journal_orphan("orphan-a", 0.25)
        first = harness.interrupted_cells(self.runs, [], [])
        second = harness.interrupted_cells(self.runs, [], first)
        self._journal_orphan("orphan-b", 0.05, known_usd=0.02)
        third = harness.interrupted_cells(self.runs, [], second)
        fourth = harness.interrupted_cells(self.runs, [], third)
        for listing in (first, second):
            self.assertEqual([(i["run_id"], i["cost_usd_committed"], i["included_in_batch_total"], i["counted_before"]) for i in listing],
                             [("orphan-a", 0.25, True, False)])
        for listing in (third, fourth):
            self.assertEqual([(i["run_id"], i["cost_usd_committed"], i["included_in_batch_total"]) for i in listing],
                             [("orphan-a", 0.25, True), ("orphan-b", 0.07, True)])
            self.assertAlmostEqual(sum(i["cost_usd_committed"] for i in listing), 0.32)
            self.assertFalse(any(i["counted_before"] for i in listing))
        self.assertEqual(fourth[0]["first_listed_at_utc"], first[0]["first_listed_at_utc"])
        self.assertTrue(fourth[0]["listed_by_earlier_resumption"])
        self.assertEqual((third[1]["kind"], third[1]["source"], third[1]["open_reservations"]), ("interrupted", JOURNAL_FILE, 1))

    def test_an_unowned_finished_bundle_is_recovered_from_its_records(self):
        totals = lambda usd, calls=3: {"totals": {"cost_usd": usd, "cost_usd_committed": usd, "model_calls": calls, "open_reservations": 0,  # noqa: E731
                                                  "open_reserved_usd": 0.0, "uncertain_unpriced_calls": 0}}
        with_totals = self.runs / "finished-with-ledger-json"
        with_totals.mkdir()
        (with_totals / "proof_bundle.json").write_text("{}", encoding="utf-8")
        (with_totals / "ledger.json").write_text(json.dumps(totals(0.3)), encoding="utf-8")
        journal_only = self._journal_orphan("finished-journal-only", 0.25)  # the audit's AC-02 reproduction
        (journal_only / "proof_bundle.json").write_text("{}", encoding="utf-8")
        bundle_only = self.runs / "finished-bundle-only"
        bundle_only.mkdir()
        (bundle_only / "proof_bundle.json").write_text(json.dumps({"ledger": totals(0.11)}), encoding="utf-8")
        unreadable = self.runs / "finished-unreadable"
        unreadable.mkdir()
        (unreadable / "proof_bundle.json").write_text("{}", encoding="utf-8")
        higher_journal = self._journal_orphan("finished-journal-higher", 0.02, known_usd=0.10)  # journal 0.12 against totals 0.10
        (higher_journal / "proof_bundle.json").write_text("{}", encoding="utf-8")
        (higher_journal / "ledger.json").write_text(json.dumps(totals(0.10)), encoding="utf-8")

        found = {i["run_id"]: i for i in harness.interrupted_cells(self.runs, [], [], per_run_cap=0.5)}
        self.assertEqual(set(found), {"finished-with-ledger-json", "finished-journal-only", "finished-bundle-only", "finished-unreadable", "finished-journal-higher"})
        self.assertTrue(all(i["kind"] == "finished_unreported" and i["included_in_batch_total"] for i in found.values()))
        self.assertEqual((found["finished-with-ledger-json"]["source"], found["finished-with-ledger-json"]["cost_usd_committed"]), ("ledger.json", 0.3))
        self.assertEqual((found["finished-journal-only"]["source"], found["finished-journal-only"]["cost_usd_committed"]), (JOURNAL_FILE, 0.25))
        self.assertEqual((found["finished-bundle-only"]["source"], found["finished-bundle-only"]["cost_usd_committed"]), ("proof_bundle.json", 0.11))
        self.assertEqual(found["finished-unreadable"]["cost_usd_committed"], 0.5)
        self.assertIn("per_run_cap", found["finished-unreadable"]["source"])
        self.assertEqual((found["finished-journal-higher"]["source"], found["finished-journal-higher"]["cost_usd_committed"]), (JOURNAL_FILE, 0.12))
        # without a cap an unreadable finished bundle is listed but honestly marked as not counted
        unpriced = {i["run_id"]: i for i in harness.interrupted_cells(self.runs, [], [])}["finished-unreadable"]
        self.assertEqual((unpriced["cost_usd_committed"], unpriced["included_in_batch_total"], unpriced["source"]), (None, False, None))

    def test_owned_directories_are_skipped_by_run_id_or_by_path_spelling(self):
        by_id = self.runs / "owned-by-run-id"
        by_id.mkdir()
        (by_id / "proof_bundle.json").write_text("{}", encoding="utf-8")
        (by_id / "ledger.json").write_text(json.dumps({"totals": {"cost_usd_committed": 0.3}}), encoding="utf-8")
        by_path = self.runs / "owned-by-path"
        by_path.mkdir()
        (by_path / "proof_bundle.json").write_text("{}", encoding="utf-8")
        (by_path / "ledger.json").write_text(json.dumps({"totals": {"cost_usd_committed": 0.3}}), encoding="utf-8")
        self._journal_orphan("nobody-owns-me", 0.25)
        (self.runs / "empty-no-record").mkdir()  # neither journal nor bundle: nothing was spent, nothing to list
        rows = [{"run_id": "owned-by-run-id", "out_dir": None, "status": "completed"},
                {"run_id": "another-id", "out_dir": str(self.runs / "." / "owned-by-path") + "/", "status": "completed"}]  # another spelling
        found = harness.interrupted_cells(self.runs, rows, [])
        self.assertEqual([i["run_id"] for i in found], ["nobody-owns-me"])


class ScriptedCells:
    """A stand-in for one_system that writes a run directory like the pipeline would and returns a completed row costing CELL_USD, or
    plays an interruption script for a scheduled index: 'mid_run' journals an open reservation (ORPHAN_USD) and dies with the request
    in flight; 'after_finish' writes the finished bundle and ledger totals, then dies before the row can be persisted. Once dead,
    every further call dies at once (a dead process runs no more cells)."""
    CELL_USD = 0.10
    ORPHAN_USD = 0.15

    def __init__(self, revision: str):
        self.revision = revision
        self.script: dict[int, str] = {}
        self.executed: list[tuple[int, str]] = []
        self.dead = False
        self.serial = 0

    def restart(self, script: dict[int, str] | None = None):
        self.script, self.dead = dict(script or {}), False

    def __call__(self, cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root):
        if self.dead:
            raise Interrupted("the process is dead")
        self.executed.append((cell["scheduled_index"], provider_name))
        self.serial += 1
        run_id = f"{cell['task']}-{cell['system']}-a{cell['attempt']}-{self.serial:03d}"
        run_dir = Path(out_dir) / run_id
        run_dir.mkdir(parents=True)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        action = self.script.pop(cell["scheduled_index"], None)
        if action == "mid_run":
            ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", self.ORPHAN_USD)
            self.dead = True
            raise Interrupted(run_id)
        rid = ledger.reserve("nebius_tokenfactory", "implement", "implement-1", "m", 0.2)
        ledger.add_call(_call(role="implement", stage="implement-1", cost_usd=self.CELL_USD, reserved_usd=0.2), rid)
        (run_dir / "ledger.json").write_text(json.dumps(ledger.to_dict()), encoding="utf-8")
        (run_dir / "proof_bundle.json").write_text(json.dumps({"run_id": run_id, "ledger": ledger.to_dict()}), encoding="utf-8")
        if action == "after_finish":
            self.dead = True
            raise Interrupted(run_id)
        return {**cell, "status": "completed", "verdict": "BASELINE" if cell["system"] == "baseline" else "VERIFIED", "accepted": True,
                "finished": True, "changed_paths": 1, "held_out_correct": True, "cost_usd": self.CELL_USD, "cost_committed_usd": self.CELL_USD,
                "wall_s": 0.1, "infra_error": False, "uncertain": False, "revision_digest": self.revision, "out_dir": str(run_dir), "run_id": run_id,
                "model_calls": 1}


class DescriptionOnly:
    def describe(self):
        return {"provider": "offline-fake"}


def _provenance_stub() -> dict:
    digests = harness.snapshot_digests(ROOT)
    return {"fresh_process": False, "attest_revision": digests["attest_revision"], "eval_script_sha256": digests["eval_script_sha256"],
            "examples_digest": digests["examples"], "guest_programs": {}, "python": "test", "platform": "test", "note": "offline test stub"}


def _batch_args(out: Path, resume: bool = False, **over) -> argparse.Namespace:
    values = dict(provider="nebius", tasks="durationkit-units-001", systems="baseline,attest", attempts=2, workers=1, usd_cap=0.20, approve_usd=0.80,
                  max_calls=None, max_turns=4, out=str(out), label="offline", suite="examples/eval/SUITE.json", resume=str(out) if resume else "",
                  snapshot_root=str(ROOT), source_root=str(ROOT), register_only=False)
    values.update(over)
    return argparse.Namespace(**values)


def _profile_reasons(report: dict) -> list[str]:
    """Validity reasons about the execution profile (provider or limits); revision reasons can appear when the working tree is
    edited while the tests run, which is unrelated to these repairs."""
    return [r for v in report["provenance_check"]["comparisons"].values() for r in v["reasons"] if "provider" in r or "cap" in r]


class BatchResumeAccounting(unittest.TestCase):
    """run_batch under repeated interruptions, with the harness's real scheduling, budget and persistence; only one_system, the
    provider construction and the provenance probe are stubs."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-batch-"))
        self.provenance = _provenance_stub()
        self.cells = ScriptedCells(self.provenance["attest_revision"]["digest"])
        self.stack = contextlib.ExitStack()
        for patcher in (mock.patch.object(harness, "runtime_provenance", return_value=self.provenance),
                        mock.patch.object(harness, "build_provider", return_value=DescriptionOnly()),
                        mock.patch.object(harness, "codex_governor", side_effect=AssertionError("no Codex runtime in these tests")),
                        mock.patch.object(harness, "one_system", side_effect=self.cells)):
            self.stack.enter_context(patcher)

    def tearDown(self):
        self.stack.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _report(self) -> dict:
        return json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))

    def _drop_rows_after(self, index: int) -> None:
        report = self._report()
        report["rows"] = [r for r in report["rows"] if r["scheduled_index"] <= index]
        report["complete"] = False
        (self.tmp / "evaluation.json").write_text(json.dumps(report), encoding="utf-8")

    def test_three_resumptions_count_each_orphan_and_row_once_and_the_cap_binds_on_the_sum(self):
        # 4 cells (1 task x 2 systems x 2 attempts), $0.10 each when completed; per-run cap $0.20; approved total $0.80
        self.cells.restart({1: "mid_run"})  # process 1: cell 0 completes, cell 1 dies mid-run (orphan A, $0.15 reserved)
        with self.assertRaises(Interrupted):
            quiet(harness.run_batch, _batch_args(self.tmp))
        report = self._report()
        self.assertEqual([r["scheduled_index"] for r in report["rows"]], [0])
        self.assertEqual(report["schedule"]["max_calls_per_run"], 22)  # the default per-run call cap is recorded

        self.cells.restart({2: "after_finish"})  # process 2: cell 1 completes, cell 2 finishes its bundle and dies before its row (orphan B)
        with self.assertRaises(Interrupted):
            quiet(harness.run_batch, _batch_args(self.tmp, resume=True))
        report = self._report()
        self.assertEqual([r["scheduled_index"] for r in report["rows"]], [0, 1])
        self.assertAlmostEqual(report["starting_total"]["committed_usd"], 0.10 + 0.15, places=6)
        self.assertAlmostEqual(report["budget"]["committed_usd"], 0.10 + 0.15 + 0.10, places=4)
        first_seen = {i["run_id"]: i["first_listed_at_utc"] for i in report["interrupted"]}

        self.cells.restart()  # process 3: cells 2 and 3 complete
        self.assertEqual(quiet(harness.run_batch, _batch_args(self.tmp, resume=True)), 0)
        report = self._report()
        self.assertTrue(report["complete"])
        self.assertEqual([r["status"] for r in sorted(report["rows"], key=lambda r: r["scheduled_index"])], ["completed"] * 4)
        self.assertEqual(sorted((i["kind"], i["source"], i["cost_usd_committed"]) for i in report["interrupted"]),  # listed by directory name
                         [("finished_unreported", "ledger.json", 0.10), ("interrupted", JOURNAL_FILE, 0.15)])
        self.assertAlmostEqual(report["starting_total"]["committed_usd"], 0.20 + 0.15 + 0.10, places=6)
        self.assertAlmostEqual(report["budget"]["committed_usd"], 0.40 + 0.15 + 0.10, places=4)
        self.assertEqual(len(first_seen), 1)  # process 2 listed orphan A only; its first-seen time is carried into every later report
        self.assertEqual({i["run_id"]: i["first_listed_at_utc"] for i in report["interrupted"] if i["run_id"] in first_seen}, first_seen)

        # process 4: the report lost row 3 (its finished directory stays: orphan C). Every orphan and every row counts once more, so
        # the next per-run reservation would reach $0.85 against the approved $0.80 and is refused.
        self._drop_rows_after(2)
        self.cells.restart()
        self.assertEqual(quiet(harness.run_batch, _batch_args(self.tmp, resume=True)), 0)
        report = self._report()
        self.assertEqual(len(report["interrupted"]), 3)
        self.assertEqual(len({i["run_id"] for i in report["interrupted"]}), 3)  # each distinct directory once
        self.assertAlmostEqual(sum(i["cost_usd_committed"] for i in report["interrupted"]), 0.35, places=6)
        self.assertAlmostEqual(report["starting_total"]["committed_usd"], 0.30 + 0.35, places=6)
        refused = [r for r in report["rows"] if r["scheduled_index"] == 3][0]
        self.assertEqual(refused["status"], "not_run")
        self.assertIn("batch USD cap $0.80 would be exceeded", refused["reason"])
        self.assertIn("0.6500 committed", refused["reason"])
        self.assertAlmostEqual(report["budget"]["committed_usd"], 0.65, places=4)
        self.assertEqual(sum(1 for index, _ in self.cells.executed if index == 3), 1)  # cell 3 ran once (process 3), never again
        self.assertTrue(all(provider == "nebius" for _, provider in self.cells.executed))
        self.assertEqual(_profile_reasons(report), [])

    def test_a_fresh_start_also_counts_directories_nobody_owns(self):
        orphan = self.tmp / "runs" / "left-over"
        ledger = Ledger()
        ledger.attach_sink(orphan / JOURNAL_FILE)
        ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.33)
        self.cells.restart()
        self.assertEqual(quiet(harness.run_batch, _batch_args(self.tmp, approve_usd=5.0)), 0)
        report = self._report()
        self.assertEqual([(i["run_id"], i["cost_usd_committed"]) for i in report["interrupted"]], [("left-over", 0.33)])
        self.assertAlmostEqual(report["starting_total"]["committed_usd"], 0.33, places=6)
        self.assertAlmostEqual(report["budget"]["committed_usd"], 0.33 + 4 * 0.10, places=4)


class FinishedButUnreportedRun(unittest.TestCase):
    """AC-02 with the harness's real one_system over the offline pipeline fakes: the pipeline finishes (bundle, ledger.json, manifest
    on disk), then the process dies before the row is persisted."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ac02-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self, resume=False):
        return _batch_args(self.tmp, resume=resume, attempts=1, usd_cap=0.5, approve_usd=5.0, max_calls=22)

    def test_the_finished_run_is_counted_exactly_once_and_the_cell_runs_again(self):
        real_one_system = harness.one_system
        state = {"die_after": 1, "dead": False}

        def one_system_then_die(cell, *rest):
            if state["dead"]:
                raise Interrupted("the process is dead")
            row = real_one_system(cell, *rest)  # Pipeline.finish wrote proof_bundle.json, ledger.json and the manifest
            if cell["scheduled_index"] == state["die_after"]:
                state["dead"] = True
                raise Interrupted(row["run_id"])  # ... and the row is never persisted
            return row
        provenance = _provenance_stub()
        with mock.patch.object(harness, "runtime_provenance", return_value=provenance), \
             mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: PaidFakeProvider(ledger)), \
             mock.patch.object(harness, "executor_for", lambda ledger: FakeExecutor(ledger)), \
             mock.patch.object(harness, "one_system", side_effect=one_system_then_die):
            with self.assertRaises(Interrupted):
                quiet(harness.run_batch, self._args())
            report = json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))
            self.assertEqual([r["scheduled_index"] for r in report["rows"]], [0])
            self.assertFalse(report["complete"])
            directories = sorted(p for p in (self.tmp / "runs").iterdir() if p.is_dir())
            self.assertEqual(len(directories), 2)
            orphan = [d for d in directories if d.name != report["rows"][0]["run_id"]][0]
            self.assertTrue((orphan / "proof_bundle.json").is_file() and (orphan / "manifest.json").is_file())
            orphan_totals = json.loads((orphan / "ledger.json").read_text(encoding="utf-8"))["totals"]
            self.assertGreater(orphan_totals["cost_usd_committed"], 0)
            state.update(die_after=None, dead=False)
            self.assertEqual(quiet(harness.run_batch, self._args(resume=True)), 0)
            resumed = json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))
            self.assertEqual(quiet(harness.run_batch, self._args(resume=True)), 0)  # a third process start with nothing left to run
            again = json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))
        self.assertTrue(resumed["complete"])
        rows = sorted(resumed["rows"], key=lambda r: r["scheduled_index"])
        self.assertEqual([r["status"] for r in rows], ["completed", "completed"])
        self.assertNotEqual(rows[1]["run_id"], orphan.name)  # the cell ran again as a fresh attempt
        self.assertEqual([(i["run_id"], i["kind"], i["source"], i["included_in_batch_total"]) for i in resumed["interrupted"]],
                         [(orphan.name, "finished_unreported", "ledger.json", True)])
        self.assertAlmostEqual(resumed["interrupted"][0]["cost_usd_committed"], orphan_totals["cost_usd_committed"], places=6)
        expected = sum(r["cost_committed_usd"] for r in rows) + orphan_totals["cost_usd_committed"]
        self.assertAlmostEqual(resumed["budget"]["committed_usd"], expected, places=4)  # exactly once
        self.assertEqual(len(again["interrupted"]), 1)
        self.assertAlmostEqual(again["budget"]["committed_usd"], expected, places=4)  # and once again on the next start
        self.assertAlmostEqual(again["starting_total"]["committed_usd"], expected, places=4)
        self.assertEqual(_profile_reasons(again), [])


# ----------------------------------------------------------------------------- AC-07: a resumed batch keeps its registration
class ResumeConfiguration(unittest.TestCase):
    REGISTERED = {"provider": "nebius", "per_run_usd_cap": 0.5, "approve_usd": 9.0, "max_calls_per_run": 22, "max_turns": 14, "workers": 2,
                  "attempts_per_cell": 2, "systems": ["baseline", "attest"]}
    UNSET = dict(provider=None, usd_cap=None, approve_usd=None, max_calls=None, max_turns=None, workers=None, attempts=None, systems=None)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-ac07-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_restore_fills_unset_values_and_names_conflicts(self):
        args = argparse.Namespace(**self.UNSET)
        self.assertEqual(harness.restore_registered(args, self.REGISTERED), [])
        self.assertEqual((args.provider, args.usd_cap, args.approve_usd, args.max_calls, args.max_turns, args.workers, args.attempts, args.systems),
                         ("nebius", 0.5, 9.0, 22, 14, 2, 2, "baseline,attest"))
        same = argparse.Namespace(**dict(self.UNSET, provider="nebius", usd_cap=0.50, systems="baseline, attest"))
        self.assertEqual(harness.restore_registered(same, self.REGISTERED), [])
        clash = argparse.Namespace(**dict(self.UNSET, provider="codex", workers=1, max_calls=20, approve_usd=5.0))
        conflicts = harness.restore_registered(clash, self.REGISTERED)
        self.assertEqual([c.split(" ")[0] for c in conflicts], ["--provider", "--approve-usd", "--max-calls", "--workers"])
        self.assertIn("--provider codex (registered: nebius)", conflicts)
        legacy = argparse.Namespace(**self.UNSET)
        self.assertEqual(harness.restore_registered(legacy, {"provider": "nebius"}), [])  # a schedule without the other keys
        self.assertEqual((legacy.provider, legacy.workers), ("nebius", None))

    def test_defaults_apply_after_restoration_and_give_nebius_a_22_call_cap(self):
        nebius = harness.apply_defaults(argparse.Namespace(**dict(self.UNSET, provider="nebius")))
        self.assertEqual((nebius.max_calls, nebius.workers, nebius.usd_cap, nebius.max_turns, nebius.attempts, nebius.systems), (22, 2, 0.5, 14, 1, "baseline,attest"))
        codex = harness.apply_defaults(argparse.Namespace(**self.UNSET))
        self.assertEqual((codex.provider, codex.max_calls), ("codex", None))
        explicit = harness.apply_defaults(argparse.Namespace(**dict(self.UNSET, provider="nebius", max_calls=20)))
        self.assertEqual(explicit.max_calls, 20)
        self.assertEqual(harness.parse_args(["--provider", "nebius"]).workers, None)  # the parser leaves the registered settings unset
        self.assertEqual(harness.parse_args(["--workers", "3"]).workers, 3)

    def _register_nebius_batch(self, cells: ScriptedCells, provenance: dict) -> dict:
        with mock.patch.object(harness, "runtime_provenance", return_value=provenance), \
             mock.patch.object(harness, "build_provider", return_value=DescriptionOnly()), \
             mock.patch.object(harness, "codex_governor", side_effect=AssertionError("no Codex runtime in these tests")), \
             mock.patch.object(harness, "one_system", side_effect=cells):
            self.assertEqual(quiet(harness.run_batch, _batch_args(self.tmp, attempts=1, usd_cap=0.5, approve_usd=1.0)), 0)
        report = json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual(report["schedule"]["max_calls_per_run"], 22)
        self.assertTrue(all((r["executed_provider"], r["usd_cap"], r["max_calls"], r["max_turns"]) == ("nebius", 0.5, 22, 4) for r in report["rows"]))
        report["rows"], report["complete"] = report["rows"][:1], False  # the interruption: the second row was never persisted
        (self.tmp / "evaluation.json").write_text(json.dumps(report), encoding="utf-8")
        return report

    def test_resume_without_flags_keeps_the_registered_nebius_profile(self):
        provenance = _provenance_stub()
        cells = ScriptedCells(provenance["attest_revision"]["digest"])
        self._register_nebius_batch(cells, provenance)
        cells.restart()
        bare = _batch_args(self.tmp, resume=True, **self.UNSET)  # the audit's scenario minus the conflicting flag: nothing given at all
        with mock.patch.object(harness, "runtime_provenance", return_value=provenance), \
             mock.patch.object(harness, "build_provider", return_value=DescriptionOnly()), \
             mock.patch.object(harness, "codex_governor", side_effect=AssertionError("resumed as Codex: the parser default leaked in")), \
             mock.patch.object(harness, "one_system", side_effect=cells):
            self.assertEqual(quiet(harness.run_batch, bare), 0)
        report = json.loads((self.tmp / "evaluation.json").read_text(encoding="utf-8"))
        self.assertEqual((bare.provider, bare.usd_cap, bare.approve_usd, bare.max_calls, bare.max_turns, bare.workers), ("nebius", 0.5, 1.0, 22, 4, 1))
        self.assertEqual([provider for _, provider in cells.executed], ["nebius"] * 3)
        resumed_row = [r for r in report["rows"] if r["scheduled_index"] == 1][0]
        self.assertEqual((resumed_row["executed_provider"], resumed_row["usd_cap"], resumed_row["max_calls"], resumed_row["max_turns"]), ("nebius", 0.5, 22, 4))
        self.assertEqual(report["budget"]["approve_usd"], 1.0)
        self.assertEqual(report["schedule"]["provider"], "nebius")
        self.assertEqual(_profile_reasons(report), [])
        self.assertIn("restored from this schedule", report["schedule"]["resumptions"][0]["configuration"])

    def test_conflicting_flags_are_refused_before_any_runtime_construction(self):
        provenance = _provenance_stub()
        cells = ScriptedCells(provenance["attest_revision"]["digest"])
        self._register_nebius_batch(cells, provenance)
        before = (self.tmp / "evaluation.json").read_text(encoding="utf-8")
        untouched = AssertionError("runtime constructed although the configuration conflicts")
        for flag, override in (("--provider", {"provider": "codex"}), ("--usd-cap", {"usd_cap": 0.7}), ("--max-calls", {"max_calls": 20}),
                               ("--max-turns", {"max_turns": 10}), ("--workers", {"workers": 2}), ("--approve-usd", {"approve_usd": 5.0}),
                               ("--provider", {"approve_usd": None, "provider": "codex"})):  # the audit's exact AC-07 scenario
            with self.subTest(flag=flag, override=override):
                args = _batch_args(self.tmp, resume=True, **dict(self.UNSET, **override))
                with mock.patch.object(harness, "runtime_provenance", side_effect=untouched), mock.patch.object(harness, "build_provider", side_effect=untouched), \
                     mock.patch.object(harness, "codex_governor", side_effect=untouched), mock.patch.object(harness, "one_system", side_effect=untouched), \
                     contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(quiet(harness.run_batch, args), 2)
                self.assertIn("refusing", err.getvalue())
                self.assertIn(flag, err.getvalue())
                self.assertIn("Nothing was constructed or run", err.getvalue())
        self.assertEqual((self.tmp / "evaluation.json").read_text(encoding="utf-8"), before)
        schedule = json.loads((self.tmp / "schedule.json").read_text(encoding="utf-8"))
        self.assertNotIn("resumptions", schedule)  # no resumption was recorded either

    def test_launcher_forwards_the_registered_configuration_or_refuses(self):
        out = (self.tmp / "batch").resolve()  # the launcher resolves the report directory (macOS: /var is /private/var)
        out.mkdir()
        (out / "schedule.json").write_text(json.dumps({**self.REGISTERED, "label": "offline", "cells": []}), encoding="utf-8")
        quiet(harness.make_snapshot, ROOT, out / harness.SNAPSHOT_DIRNAME)
        launched = []

        def fake_call(cmd, cwd=None, env=None):
            launched.append(cmd)
            return 0
        untouched = AssertionError("the launcher must not construct a runtime")
        with mock.patch.object(harness.subprocess, "call", side_effect=fake_call), mock.patch.object(harness, "build_provider", side_effect=untouched), \
             mock.patch.object(harness, "codex_governor", side_effect=untouched), mock.patch.object(harness, "runtime_provenance", side_effect=untouched):
            self.assertEqual(quiet(harness.main, ["--resume", str(out)]), 0)
            self.assertEqual(len(launched), 1)
            forwarded = launched[0]
            self.assertEqual(forwarded[1], str(out / harness.SNAPSHOT_DIRNAME / "scripts" / "run_evaluation.py"))
            flags = " ".join(forwarded[2:])
            for expected in ("--provider nebius", "--usd-cap 0.5", "--approve-usd 9.0", "--max-calls 22", "--max-turns 14", "--workers 2",
                             "--attempts 2", "--systems baseline,attest", f"--resume {out}"):
                self.assertIn(expected, flags)
            self.assertEqual(flags.count("--provider"), 1)
            # the same registered values given explicitly are accepted (and not duplicated); conflicting ones are refused
            self.assertEqual(quiet(harness.main, ["--resume", str(out), "--provider", "nebius", "--max-calls=22"]), 0)
            self.assertEqual(" ".join(launched[1][2:]).count("--max-calls"), 1)
            for conflicting in (["--provider", "codex"], ["--usd-cap", "0.7"], ["--max-calls", "20"], ["--max-turns", "10"], ["--workers", "1"],
                                ["--approve-usd", "5"], ["--attempts", "1"], ["--systems", "attest"]):
                with self.subTest(conflicting=conflicting), contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(quiet(harness.main, ["--resume", str(out), *conflicting]), 2)
                    self.assertIn("refusing", err.getvalue())
                    self.assertIn(conflicting[0], err.getvalue())
            self.assertEqual(len(launched), 2)  # none of the refusals reached the snapshot process

    def test_comparison_validity_marks_provider_and_limit_drift(self):
        schedule = dict(self.REGISTERED)
        rows = [{"task": "t1", "system": "baseline", "attempt": 1, "status": "completed", "revision_digest": "a" * 64, "executed_provider": "nebius",
                 "usd_cap": 0.50, "max_calls": 22, "max_turns": 14},
                {"task": "t1", "system": "attest", "attempt": 1, "status": "completed", "revision_digest": "a" * 64, "executed_provider": "codex",
                 "usd_cap": 0.5, "max_calls": None, "max_turns": 14},
                {"task": "t2", "system": "baseline", "attempt": 1, "status": "completed", "revision_digest": "a" * 64, "executed_provider": "nebius",
                 "usd_cap": 0.5, "max_calls": 20, "max_turns": 14},
                {"task": "t2", "system": "attest", "attempt": 1, "status": "not_run", "executed_provider": None, "usd_cap": 0.7, "max_calls": 22, "max_turns": 14},
                {"task": "t3", "system": "baseline", "attempt": 1, "status": "completed", "revision_digest": "a" * 64}]  # a row from before this revision
        validity = harness.comparison_validity(rows, "a" * 64, snapshot_intact=True, schedule=schedule)
        self.assertFalse(validity["t1"]["valid"])
        self.assertTrue(any("provider 'codex' differs from the registered 'nebius'" in r for r in validity["t1"]["reasons"]))
        self.assertTrue(any("per-run call cap None differs" in r for r in validity["t1"]["reasons"]))
        self.assertFalse(validity["t2"]["valid"])
        self.assertEqual(validity["t2"]["reasons"], ["baseline a1: per-run call cap 20 differs from the registered 22"])  # the not_run row is not judged
        self.assertTrue(validity["t3"]["valid"])
        self.assertTrue(harness.comparison_validity(rows[:1], "a" * 64, snapshot_intact=True)["t1"]["valid"])  # without a schedule, as before


class RenderUnownedDirectories(unittest.TestCase):
    def test_report_shows_the_starting_total_and_each_unowned_directory_once(self):
        rows = [{"status": "completed", "verdict": "VERIFIED", "accepted": True, "held_out_correct": True, "system": "attest", "finished": True, "changed_paths": 1,
                 "confusion": "true_accept", "scheduled_index": 0, "task": "t", "attempt": 1, "cost_committed_usd": 0.1, "wall_s": 10.0}]
        report = {"schedule": {"label": "t", "provider": "nebius", "systems": ["attest"], "tasks": ["t"], "attempts_per_cell": 1, "cells": [{}], "provenance": {}},
                  "rows": rows, "summary": harness.summarize(rows, ["attest"]), "budget": {"committed_usd": 0.35, "approve_usd": 1.0, "per_run_cap_usd": 0.2},
                  "provenance_check": {}, "starting_total": {"committed_usd": 0.25, "completed_rows_usd": 0.1, "completed_rows": 1, "unowned_run_directories_usd": 0.15,
                                                             "unowned_run_directories": 1, "rebuilt_at_utc": "2026-10-19T00:00:00+00:00"},
                  "interrupted": [{"run_id": "t-attest-a1-dead", "kind": "finished_unreported", "source": "ledger.json", "model_calls": 3, "cost_usd_committed": 0.15,
                                   "open_reservations": 0, "included_in_batch_total": True}]}
        text = render_evaluation.render(report)
        self.assertIn("Starting committed total of this process: $0.25", text)
        self.assertIn("| t-attest-a1-dead | finished_unreported | ledger.json | 3 | 0.15 | 0 | yes |", text)
        self.assertEqual(text.count("t-attest-a1-dead"), 1)


if __name__ == "__main__":
    unittest.main()
