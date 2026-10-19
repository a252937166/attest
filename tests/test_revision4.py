"""Revision 4 (19 Oct 2026): ledger journal and reservations that survive an interruption, the console's reconciliation from the
journal, the harness's no-patch label and interrupted-cell accounting, the implementer's navigation tools, the mechanical
rules behind validated corrections, the contract audit's exhibits, and `attest check` on the new bundle records. Offline only."""

import argparse
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from attest.core import exhibits as exhibits_module
from attest.core.check import check_bundle
from attest.core.pipeline import coverage_gaps, methods_changed
from attest.core.prompts import CONTRACT_AUDIT_SCHEMA, WITNESS_EXIT_CODE, WITNESS_MARKER, contract_audit_prompt, implement_prompt, seal_prompt
from attest.core.task import TaskSpec
from attest.core.workspace import PolicyViolation, Workspace
from attest.http import TransportError
from attest.ledger import JOURNAL_FILE, Ledger, ModelCall, read_journal, utcnow
from attest.models.base import ModelError
from tests.test_budget import COST, RESERVE, PaidFakeProvider, quiet
from tests.test_verification import TASK, FakeExecutor, FakeProvider, run_scenario

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_evaluation as harness  # noqa: E402
import render_evaluation  # noqa: E402


def _call(**over):
    base = dict(provider="nebius_tokenfactory", role="seal", stage="seal-1", requested_model="m", requested_effort=None, returned_model="m",
                returned_effort=None, started_at_utc=utcnow(), elapsed_ms=1, gateway_duration_ms=None, prompt_chars=10, tokens_in=10,
                tokens_out=5, tokens_cached=0, usage_raw={}, cost_usd=0.01, cost_note="t", ok=True, reserved_usd=0.05)
    base.update(over)
    return ModelCall(**base)


class LedgerJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-journal-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reservation_is_written_before_the_call_and_closed_by_its_record(self):
        ledger = Ledger()
        ledger.attach_sink(self.tmp / JOURNAL_FILE)
        rid = ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)
        self.assertEqual(ledger.totals()["open_reservations"], 1)
        self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], 0.05)  # an open reservation is committed at its bound
        lines = [json.loads(l) for l in (self.tmp / JOURNAL_FILE).read_text().splitlines()]
        self.assertEqual([l["event"] for l in lines], ["ledger", "reserve"])
        ledger.add_call(_call(), rid)
        self.assertEqual(ledger.totals()["open_reservations"], 0)
        self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], 0.01)
        lines = [json.loads(l) for l in (self.tmp / JOURNAL_FILE).read_text().splitlines()]
        self.assertEqual(lines[-1]["event"], "call")
        self.assertEqual(lines[-1]["reservation_id"], rid)
        self.assertEqual(lines[-1]["settlement"], "known")

    def test_journal_read_back_counts_known_costs_and_open_reservations(self):
        ledger = Ledger()
        ledger.attach_sink(self.tmp / JOURNAL_FILE)
        r1 = ledger.reserve("nebius_tokenfactory", "spec", "spec", "m", 0.04)
        ledger.add_call(_call(role="spec", stage="spec", cost_usd=0.02, reserved_usd=0.04), r1)
        r2 = ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)
        ledger.add_call(_call(cost_usd=None, ok=False, error="transport: timed out", settlement="unsettled"), r2)  # outcome unknown: reservation kept
        ledger.reserve("nebius_tokenfactory", "implement", "implement-1", "m", 0.06)  # the process dies before this call records
        with (self.tmp / JOURNAL_FILE).open("a") as handle:
            handle.write('{"event": "call", "truncated')  # a write cut short by the interruption
        journal = read_journal(self.tmp / JOURNAL_FILE)
        self.assertEqual(journal["model_calls"], 2)
        self.assertAlmostEqual(journal["cost_usd"], 0.02)
        self.assertAlmostEqual(journal["cost_usd_committed"], 0.02 + 0.05 + 0.06)
        self.assertEqual(journal["open_reservations"], 1)
        self.assertEqual(journal["uncertain_unpriced_calls"], 1)
        self.assertEqual(journal["unparsable_lines"], 1)
        self.assertIsNone(read_journal(self.tmp / "missing.jsonl"))

    def test_nebius_client_journals_the_reservation_and_keeps_it_on_a_transport_failure(self):
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        ledger = Ledger()
        ledger.attach_sink(self.tmp / JOURNAL_FILE)
        client = NebiusTokenFactory("key", ledger, usd_cap=0.5)
        schema = {"type": "object", "additionalProperties": False, "properties": {"x": {"type": "integer"}}, "required": ["x"]}

        def cut(method, url, headers, payload=None, timeout=60, max_bytes=0):
            raise TransportError("timed out")
        with mock.patch("attest.models.nebius_tokenfactory.request_json", cut):
            with self.assertRaises(ModelError) as cm:
                client.structured("seal", "prompt", schema, "seal-1")
        self.assertTrue(cm.exception.uncertain)
        call = ledger.model_calls[-1]
        self.assertEqual(call.settlement, "unsettled")
        self.assertIsNone(call.cost_usd)
        self.assertGreater(call.reserved_usd, 0)
        self.assertEqual(ledger.totals()["open_reservations"], 0)  # the call record closed the reservation and carries it
        self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], call.reserved_usd)
        self.assertAlmostEqual(client.spent_usd(), call.reserved_usd)  # the per-run cap binds on the unsettled reservation too
        events = [json.loads(l)["event"] for l in (self.tmp / JOURNAL_FILE).read_text().splitlines()]
        self.assertEqual(events, ["ledger", "reserve", "call"])

    def test_provider_refusals_are_free_but_server_failures_stay_reserved(self):
        from attest.http import HttpError
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        schema = {"type": "object", "additionalProperties": False, "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        for status, settlement, cost in ((422, "known", 0.0), (429, "known", 0.0), (502, "unsettled", None)):
            ledger = Ledger()
            ledger.attach_sink(self.tmp / f"refusal-{status}" / JOURNAL_FILE)  # a reservation needs a journal before any request (AC-03)
            client = NebiusTokenFactory("key", ledger, usd_cap=0.5)

            def refuse(method, url, headers, payload=None, timeout=60, max_bytes=0, status=status):
                raise HttpError(status, {"error": "x"}, url)
            with mock.patch("attest.models.nebius_tokenfactory.request_json", refuse):
                with self.assertRaises(ModelError):
                    client.structured("seal", "prompt", schema, "seal-1")
            call = ledger.model_calls[-1]
            self.assertEqual(call.settlement, settlement, status)
            self.assertEqual(call.cost_usd, cost, status)
            expected = call.reserved_usd if cost is None else 0.0
            self.assertAlmostEqual(ledger.totals()["cost_usd_committed"], expected, places=6)

    def test_pipeline_attaches_a_journal_to_the_run_directory(self):
        ledger = Ledger()
        from attest.core.pipeline import Pipeline
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=PaidFakeProvider(ledger), executor=FakeExecutor(ledger), ledger=ledger,
                            out_dir=self.tmp, max_turns=4, tavily=None, profile_label="test")
        quiet(pipeline.run)
        journal = read_journal(pipeline.out_dir / JOURNAL_FILE)
        self.assertIsNotNone(journal)
        self.assertEqual(journal["model_calls"], len(ledger.model_calls))
        self.assertAlmostEqual(journal["cost_usd_committed"], ledger.totals()["cost_usd_committed"], places=6)
        manifest = json.loads((pipeline.out_dir / "manifest.json").read_text())
        self.assertIn(JOURNAL_FILE, {f["path"] for f in manifest["files"]})
        # the harness's judge records a sandbox operation after the bundle is sealed: the journal must not change under its manifest
        from attest.ledger import SandboxOp
        ledger.add_op(SandboxOp(stage="judge", operation_uuid="op-judge", image_uuid="i", result_image_uuid=None, disposable=True, networking_enabled=False,
                                status="SUCCESS", exit_code=0, timed_out=False, signal=None, duration_s=1.0, raw_cost_diag=None, stdout_truncated=False,
                                started_at_utc=utcnow()))
        self.assertEqual(read_journal(pipeline.out_dir / JOURNAL_FILE)["sandbox_operations"], journal["sandbox_operations"])
        self.assertTrue(check_bundle(pipeline.out_dir)["ok"], [c for c in check_bundle(pipeline.out_dir)["checks"] if c["ok"] is False])


class ConsoleInterruption(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-console-int-"))
        from attest.app.db import Store
        self.store = Store(self.tmp / "attest.db")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reconciliation_reads_the_journal_of_an_interrupted_run(self):
        run_dir = self.tmp / "runs" / "r1"
        run_dir.mkdir(parents=True)
        ledger = Ledger()
        ledger.attach_sink(run_dir / JOURNAL_FILE)
        rid = ledger.reserve("nebius_tokenfactory", "spec", "spec", "m", 0.04)
        ledger.add_call(_call(role="spec", stage="spec", cost_usd=0.03, reserved_usd=0.04), rid)
        ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)  # in flight when the process died
        self.store.create_run(run_id="r1", task_id="t", task_title="T", provider="nebius", profile_label="x", status="running", stage="seal",
                              created_at="2026-10-19T10:00:00", out_dir=str(run_dir))
        self.store.create_run(run_id="r2", task_id="t", task_title="T", provider="nebius", profile_label="x", status="running", stage="seal",
                              created_at="2026-10-19T10:00:00", out_dir=str(self.tmp / "runs" / "nojournal"))
        reconciled = {r["run_id"]: r for r in self.store.reconcile_interrupted(per_run_cap=0.5)}
        self.assertTrue(reconciled["r1"]["journal"])
        self.assertAlmostEqual(reconciled["r1"]["cost_committed_usd"], 0.03 + 0.05)  # known cost plus the open reservation at its bound
        self.assertFalse(reconciled["r2"]["journal"])
        self.assertEqual(reconciled["r2"]["cost_committed_usd"], 0.5)  # no journal: the per-run cap bounds the unknown spend
        row = self.store.get_run("r1")
        self.assertEqual(row["status"], "error")
        self.assertIn("ledger journal", row["error"])
        self.assertEqual(row["model_calls"], 1)

    def test_worker_meters_land_in_the_store_before_the_process_dies(self):
        from attest.app.worker import Worker
        worker = Worker(self.store, self.tmp, TASK.parent.parent, max_turns=4)
        self.store.create_run(run_id="r1", task_id="durationkit-units-001", task_title="T", provider="nebius", profile_label="judge-demo",
                              status="queued", stage="queued", created_at=utcnow(), requester="t")

        class Dying(FakeExecutor):
            def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
                if stage == "verify":
                    raise SystemExit(137)  # the process is killed: no except-path accounting runs
                return super().run_branch(image, files, steps, stage, deletes, timeout, networking)
        with mock.patch.object(worker, "build_runtime", lambda run_id, provider_name, ledger: (PaidFakeProvider(ledger), Dying(ledger), None)):
            with self.assertRaises(SystemExit):
                quiet(worker._execute, "r1", TASK, "nebius", "judge-demo")
        row = self.store.get_run("r1")
        self.assertEqual(row["status"], "running")  # nothing finalized it
        self.assertGreater(row["model_calls"], 0)
        self.assertAlmostEqual(row["cost_committed_usd"], row["model_calls"] * COST, places=6)  # every call updated the row as it happened
        journal = read_journal(Path(row["out_dir"]) / JOURNAL_FILE)
        self.assertEqual(journal["model_calls"], row["model_calls"])
        reconciled = self.store.reconcile_interrupted(per_run_cap=0.5)[0]
        self.assertTrue(reconciled["journal"])
        self.assertAlmostEqual(reconciled["cost_committed_usd"], row["model_calls"] * COST, places=6)

    def test_health_recheck_counts_no_phantom_reservation_when_idle(self):
        today = "2026-10-19T00:00:00"
        ok, detail = self.store.nebius_budget_ok(0.5, 2.0, today, executing=False)
        self.assertTrue(ok)
        self.assertIn("0 active reservation(s)", detail)
        ok, detail = self.store.nebius_budget_ok(0.5, 2.0, today)  # at execution time the running row itself counts
        self.assertIn("1 active reservation(s)", detail)


class HarnessLabels(unittest.TestCase):
    def test_no_patch_is_its_own_label_for_both_systems(self):
        attest_row = {"status": "completed", "verdict": "NO CHANGE", "accepted": False, "held_out_correct": False, "system": "attest", "finished": False, "changed_paths": 0}
        self.assertEqual(harness.classify(attest_row), "no_patch")
        baseline_row = {"status": "completed", "verdict": "BASELINE", "accepted": False, "held_out_correct": False, "system": "baseline", "finished": False, "changed_paths": 0}
        self.assertEqual(harness.classify(baseline_row), "no_patch")
        baseline_patch = {"status": "completed", "verdict": "BASELINE", "accepted": False, "held_out_correct": False, "system": "baseline", "finished": False, "changed_paths": 1}
        self.assertEqual(harness.classify(baseline_patch), "true_reject")  # an unfinished baseline that did write a wrong patch
        # an INFEASIBLE verdict is a refusal, not a rejected patch: right for an unsatisfiable task, a false refusal for a satisfiable one
        infeasible = {"status": "completed", "verdict": "INFEASIBLE", "accepted": False, "held_out_correct": False, "system": "attest", "finished": False, "changed_paths": 0}
        self.assertEqual(harness.classify(dict(infeasible, ground_truth="unsatisfiable")), "true_reject")
        self.assertEqual(harness.classify(dict(infeasible, ground_truth="held_out_suite")), "false_refusal")
        self.assertEqual(harness.classify(infeasible), "false_refusal")
        rows = [dict(attest_row, confusion="no_patch", scheduled_index=0, task="t", attempt=1, cost_committed_usd=0.1, wall_s=10.0)]
        summary = harness.summarize(rows, ["attest"])
        self.assertEqual(summary["attest"]["no_patch"], 1)
        self.assertEqual(summary["attest"]["needs_human"], 0)
        report = {"schedule": {"label": "t", "provider": "codex", "systems": ["attest"], "tasks": ["t"], "attempts_per_cell": 1, "cells": [{}], "provenance": {}},
                  "rows": rows, "summary": summary, "budget": {}, "provenance_check": {}, "interrupted": []}
        text = render_evaluation.render(report)
        self.assertIn("No patch (unfinished)", text)
        self.assertIn("| 0 | 0 | 0 | 0 | 1 |", text)

    def test_interrupted_run_directories_are_read_back_from_their_journals(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-harness-int-"))
        try:
            runs = tmp / "runs"
            owned = runs / "task-attest-a1-x"
            owned.mkdir(parents=True)
            (owned / "proof_bundle.json").write_text("{}")
            dead = runs / "task-attest-a2-y"
            dead.mkdir()
            ledger = Ledger()
            ledger.attach_sink(dead / JOURNAL_FILE)
            rid = ledger.reserve("nebius_tokenfactory", "spec", "spec", "m", 0.04)
            ledger.add_call(_call(role="spec", stage="spec", cost_usd=0.02, reserved_usd=0.04), rid)
            ledger.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)
            (runs / "task-attest-a3-z").mkdir()  # no journal at all: nothing to count
            found = harness.interrupted_cells(runs, [{"out_dir": str(owned)}], [])
            self.assertEqual([f["run_id"] for f in found], ["task-attest-a2-y"])
            self.assertAlmostEqual(found[0]["cost_usd_committed"], 0.07)
            self.assertEqual(found[0]["open_reservations"], 1)
            self.assertEqual((found[0]["kind"], found[0]["source"], found[0]["included_in_batch_total"]), ("interrupted", JOURNAL_FILE, True))
            # a later process lists the same directory again with the same figure: it is part of every process's starting total
            # (audit finding AC-01); the earlier entry only supplies the time it was first seen
            again = harness.interrupted_cells(runs, [{"out_dir": str(owned)}], found)
            self.assertEqual([(a["run_id"], a["cost_usd_committed"], a["included_in_batch_total"]) for a in again], [("task-attest-a2-y", 0.07, True)])
            self.assertTrue(again[0]["listed_by_earlier_resumption"])
            self.assertEqual(again[0]["first_listed_at_utc"], found[0]["first_listed_at_utc"])
            self.assertFalse(again[0]["counted_before"])  # never a reason to leave a cost out of the current process's total
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ImplementerNavigation(unittest.TestCase):
    def setUp(self):
        src = b"import os\n\n\nclass Version:\n    def __init__(self):\n        pass\n\n    @classmethod\n    def _nat_cmp(cls, a, b):\n        return 0\n\n\ndef helper():\n    return 1\n"
        self.ws = Workspace({"src/pkg/version.py": src, "README.md": b"# readme\n_nat_cmp mentioned here\n"}, ["src/pkg/**"], ["tests/**"])

    def test_search_finds_symbols_with_line_numbers_across_the_tree_or_in_one_file(self):
        hits = self.ws.search("_nat_cmp")
        self.assertIn("src/pkg/version.py:9:     def _nat_cmp(cls, a, b):", hits)
        self.assertIn("README.md:2:", hits)
        only = self.ws.search(r"re:def _nat_cmp\(", "src/pkg/version.py")  # the re: prefix selects a regular expression (bounded child)
        self.assertIn("1 matching line(s)", only)
        self.assertNotIn("README.md", only)
        self.assertIn("no match", self.ws.search("does_not_exist"))
        self.assertIn("no match", self.ws.search(r"def _nat_cmp\(", "src/pkg/version.py"))  # without the prefix the text is literal
        self.assertIn("no match", self.ws.search("[unbalanced", "src/pkg/version.py"))  # a literal too, never a regex error
        self.assertTrue(self.ws.search("re:[unbalanced", "src/pkg/version.py").startswith("INVALID ACTION: invalid regular expression"))

    def test_outline_and_truncated_reads_point_at_definitions(self):
        self.assertEqual(self.ws.outline("src/pkg/version.py"), ["4: class Version:", "5:     def __init__(self):", "9:     def _nat_cmp(cls, a, b):", "13: def helper():"])
        text = self.ws.read("src/pkg/version.py", limit=40)
        self.assertIn("truncated", text)
        self.assertIn("OUTLINE", text)
        self.assertIn("9:     def _nat_cmp(cls, a, b):", text)

    def test_replace_refusal_names_the_closest_lines(self):
        with self.assertRaises(PolicyViolation) as cm:
            self.ws.replace("src/pkg/version.py", "    def _nat_cmp(cls, a, b, c):", "x")
        self.assertIn("occurs 0 times", str(cm.exception))
        self.assertIn("closest lines in the file: line 9: ", str(cm.exception))

    def test_prompts_describe_search_outline_and_coverage(self):
        task = TaskSpec.load(TASK)
        spec = {"restated_task": "r", "interface_contract": [], "acceptance_criteria": ["a", "b"], "out_of_scope": []}
        ws = Workspace({"durationkit/parse.py": b"def parse_duration(text):\n    return 0\n"}, task.allowed_write_globs, task.protected_globs)
        transcript = [{"turn": i, "action": {"action": "read_file", "path": "durationkit/parse.py"}, "observation": "x"} for i in range(1, 4)]
        text = implement_prompt(task, spec, ws, transcript, 4, 12)
        self.assertIn("- search: find", text)
        self.assertIn("OUTLINE OF durationkit/parse.py", text)
        self.assertIn("NAVIGATION WARNING: your last 3 turns only read or searched", text)
        sealed = seal_prompt(task, spec, {"durationkit/parse.py": b""}, None, audit_hint="AUDITOR'S SUSPICION: x")
        self.assertIn("AC1: a", sealed)
        self.assertIn("AUDITOR'S SUSPICION", sealed)
        self.assertIn("coverage (one entry per", sealed)
        audit = contract_audit_prompt(task, dict(spec, feasible=False, infeasibility_reason="because"), {"durationkit/parse.py": b""})
        self.assertIn(WITNESS_MARKER, audit)
        self.assertIn(f"exit\nwith code {WITNESS_EXIT_CODE}" if False else str(WITNESS_EXIT_CODE), audit)
        self.assertIn("ALREADY JUDGED THE TASK INFEASIBLE", audit)
        self.assertEqual(set(CONTRACT_AUDIT_SCHEMA["required"]), {"consistent", "conflicts", "notes"})


class CorrectionRules(unittest.TestCase):
    ORIGINAL = "import unittest\nfrom m import f\n\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(f(1), 2)\n\n    def test_b(self):\n        self.assertEqual(f(2), 3)\n"

    def test_methods_changed_sees_only_real_body_differences_and_module_level_edits(self):
        same_but_comment = self.ORIGINAL.replace("self.assertEqual(f(1), 2)", "self.assertEqual(f(1), 2)  # noqa")
        self.assertEqual(methods_changed(self.ORIGINAL, same_but_comment, "test_x"), set())
        fixed_a = self.ORIGINAL.replace("self.assertEqual(f(1), 2)", "self.assertEqual(f(1), 3)")
        self.assertEqual(methods_changed(self.ORIGINAL, fixed_a, "test_x"), {"test_x.T.test_a"})
        with_import = "import math\n" + fixed_a
        self.assertEqual(methods_changed(self.ORIGINAL, with_import, "test_x"), {"test_x.T.test_a"})  # imports may change
        with_helper = fixed_a + "\n\ndef helper():\n    return 1\n"
        self.assertIn("<module>", methods_changed(self.ORIGINAL, with_helper, "test_x"))  # other module-level code may not

    def test_coverage_gaps_name_unclaimed_criteria_and_ignore_unknown_test_names(self):
        ids = ["test_sealed.T.test_a", "test_sealed.T.test_b"]
        criteria = ["one", "two", "three"]
        self.assertEqual(coverage_gaps([{"criterion": 1, "tests": ["test_a"]}, {"criterion": 2, "tests": ["test_nope"]}], criteria, ids), ["AC2", "AC3"])
        self.assertEqual(coverage_gaps(None, criteria, ids), [])
        self.assertEqual(coverage_gaps([{"criterion": "x", "tests": ["test_a"]}], ["one"], ids), ["AC1"])


class NewBundlesCheckAndRender(unittest.TestCase):
    def _run(self, scenario, **kwargs):
        tmp = Path(tempfile.mkdtemp(prefix=f"attest-r4-{scenario}-"))
        ledger = Ledger()
        from attest.core.pipeline import Pipeline
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=FakeProvider(ledger, scenario), executor=FakeExecutor(ledger, scenario), ledger=ledger,
                            out_dir=tmp, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="r4-offline", run_id=f"r4-{scenario}", **kwargs)
        with contextlib.redirect_stdout(io.StringIO()):
            bundle = pipeline.run()
        return bundle, pipeline.out_dir, tmp

    def test_corrected_adversarial_bundle_passes_check_and_a_tampered_correction_fails_it(self):
        bundle, run_dir, tmp = self._run("arb_clear")
        try:
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
            names = {c["name"] for c in report["checks"]}
            self.assertTrue({"adversarial_corrected_digest", "adversarial_correction_scope", "adversarial_corrected_binding_recomputed", "adversarial_corrected_passes"} <= names, names)
            corrected = run_dir / "arbitration" / "adversarial_corrected.py"
            corrected.write_text(corrected.read_text().replace('self.assertEqual(parse_duration("2m"), 120.0)', 'self.assertTrue(True)'))
            report = check_bundle(run_dir)
            self.assertFalse(report["ok"])
            bad = {c["name"] for c in report["checks"] if c["ok"] is False}
            self.assertIn("adversarial_corrected_digest", bad)
            self.assertIn("adversarial_correction_scope", bad)  # a passing test was touched
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_corrected_sealed_bundle_passes_check_and_renders(self):
        bundle, run_dir, tmp = self._run("sealed_one_timeout")  # the one sealed correction left after CORE-02: a supervisor-killed timeout
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
            proof = (run_dir / "PROOF.md").read_text()
            self.assertIn("Corrected sealed module (E6)", proof)
            self.assertIn("red check preserved", proof)
            decision = exhibits_module.decision(bundle)
            self.assertTrue(any("corrected by the arbiter" in w for w in decision["weak"]), decision["weak"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_infeasible_bundle_records_the_witness_and_passes_check(self):
        bundle, run_dir, tmp = self._run("contract_conflict")
        try:
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
            names = {c["name"] for c in report["checks"]}
            self.assertTrue({"witness_digest", "witness_demonstration_recorded", "infeasible_has_demonstrated_witness"} <= names, names)
            decision = exhibits_module.decision(bundle)
            self.assertEqual(decision["reason_class"], "infeasible")
            self.assertIn("witness program demonstrated", decision["explanation"])
            self.assertEqual(decision["evidence"]["ref"], "contract_audit")
            self.assertIn("CONTRADICTION", decision["evidence"]["text"])
            proof = (run_dir / "PROOF.md").read_text()
            self.assertIn("## 2b. Contract audit (executed witnesses)", proof)
            self.assertIn("demonstrated", proof)
            witness = run_dir / "contract_audit" / "witness_1.py"
            witness.write_text(witness.read_text() + "\n# edited\n")
            self.assertFalse(check_bundle(run_dir)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_unproven_infeasibility_and_unfinished_no_change_have_their_own_copy(self):
        held, run_dir, tmp = self._run("spec_infeasible_unproven")
        try:
            decision = exhibits_module.decision(held)
            self.assertEqual(decision["reason_class"], "infeasibility_unproven")
            self.assertIn("did not demonstrate a", decision["explanation"])
            self.assertTrue(check_bundle(run_dir)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        idle, run_dir, tmp = self._run("implementer_idle")
        try:
            decision = exhibits_module.decision(idle)
            self.assertEqual(decision["reason_class"], "unfinished_no_patch")
            self.assertEqual(decision["statement"], "The implementer did not produce a patch.")
            self.assertIn("unfinished task", decision["explanation"])
            self.assertIn("not a repair", decision["explanation"])
            self.assertTrue(check_bundle(run_dir)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_sealed_assertion_hold_copy_names_the_rule(self):
        bundle, run_dir, tmp = self._run("sealed_one_fail")
        try:
            decision = exhibits_module.decision(bundle)
            self.assertEqual(decision["reason_class"], "sealed_assertion_hold")
            self.assertIn("never overrides it on a model's judgement", decision["explanation"])
            from attest.core.pipeline import oracle_disagreement
            self.assertTrue(oracle_disagreement({"outcome": "FAIL"}))
            self.assertTrue(oracle_disagreement({"outcome": "ERROR", "failure_tail": 'File "/tmp/sealed/test_sealed.py", line 5, in test_a\n    f()\n  File "/tmp/w/pkg/m.py", line 9, in f\n    raise TypeError("bad")\nTypeError: bad'}))
            self.assertTrue(oracle_disagreement({"outcome": "ERROR", "failure_tail": 'File "/tmp/sealed/test_sealed.py", line 5, in test_a\n    m.new_function()\nAttributeError: no attribute'}))
            # CORE-02: an unpacking error in the test body can be the candidate's wrong return shape; it is a disagreement, never a test defect
            self.assertTrue(oracle_disagreement({"outcome": "ERROR", "failure_tail": 'File "/tmp/sealed/test_sealed.py", line 5, in test_a\n    a, b = (1, 2, 3)\nValueError: too many values to unpack (expected 2)'}))
            self.assertFalse(oracle_disagreement({"outcome": "TIMEOUT", "timed_out": True}))
            self.assertEqual(decision["evidence"]["ref"], "E6")
            self.assertTrue(check_bundle(run_dir)["ok"], [c for c in check_bundle(run_dir)["checks"] if c["ok"] is False])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_recorded_bundles_of_earlier_revisions_still_check(self):
        """Every public bundle under reports/ that carries a manifest must still pass the revised checker (no regression)."""
        checked = failed = 0
        for manifest in sorted(ROOT.glob("reports/*/**/manifest.json"))[:40]:
            run_dir = manifest.parent
            if not (run_dir / "proof_bundle.json").is_file() or any(part.startswith("attest-audit-") for part in run_dir.parts):
                continue  # the audit's own synthetic bundles are deliberately defective and must fail
            report = check_bundle(run_dir)
            checked += 1
            if not report["ok"]:
                failed += 1
                print(run_dir, [c for c in report["checks"] if c["ok"] is False][:3])
        self.assertGreater(checked, 5)
        self.assertEqual(failed, 0)


if __name__ == "__main__":
    unittest.main()
