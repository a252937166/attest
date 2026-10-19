"""Budget accounting under failure (17 Oct 2026): paid calls stay accounted for when a later step crashes, an uncertain call
keeps its reservation, a failed judge keeps the verdict and the costs, an interrupted batch resumes without losing rows, and
the console's daily budget counts errored and interrupted runs. Offline: fakes only."""

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

from attest.core.pipeline import Pipeline
from attest.core.task import TaskSpec
from attest.ledger import Ledger, ModelCall, utcnow
from attest.models.base import ModelError, ModelResult
from tests.test_verification import TASK, FakeExecutor, FakeProvider

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_evaluation as harness  # noqa: E402

COST = 0.01
RESERVE = 0.05


class PaidFakeProvider(FakeProvider):
    """Every call costs COST and reserves RESERVE first, like the Token Factory client. Scenario `uncertain_at_break`: the
    breaker call ends transport-uncertain after its reservation was recorded (cost unknown, reservation kept)."""
    name = "fake-paid"

    def structured(self, role, prompt, schema, stage):
        if self.scenario == "uncertain_at_break" and role == "break":
            call = ModelCall(provider=self.name, role=role, stage=stage, requested_model="fake", requested_effort=None, returned_model=None,
                             returned_effort=None, started_at_utc=utcnow(), elapsed_ms=1, gateway_duration_ms=None, prompt_chars=len(prompt),
                             tokens_in=None, tokens_out=None, tokens_cached=None, usage_raw={}, cost_usd=None, cost_note="fake", ok=False,
                             error="transport: timed out", reserved_usd=RESERVE)
            self.ledger.add_call(call)
            raise ModelError("inference outcome uncertain (timed out); not retried", uncertain=True)
        return super().structured(role, prompt, schema, stage)

    def decorate(self, call):
        call.cost_usd = COST
        call.reserved_usd = RESERVE
        call.provider = self.name


class CrashingExecutor(FakeExecutor):
    def __init__(self, ledger, crash_stage):
        super().__init__(ledger, "honest")
        self.crash_stage = crash_stage

    def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
        if stage == self.crash_stage:
            raise RuntimeError(f"sandbox exploded during {stage}")
        return super().run_branch(image, files, steps, stage, deletes, timeout, networking)


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class PipelineCrashAccounting(unittest.TestCase):
    def test_bundle_keeps_the_paid_calls_when_verification_crashes(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-budget-"))
        try:
            ledger = Ledger()
            pipeline = Pipeline(task=TaskSpec.load(TASK), provider=PaidFakeProvider(ledger), executor=CrashingExecutor(ledger, "verify"),
                                ledger=ledger, out_dir=tmp, max_turns=4, tavily=None, profile_label="test")
            with self.assertRaises(RuntimeError):
                quiet(pipeline.run)
            bundle = json.loads((pipeline.out_dir / "proof_bundle.json").read_text())
            self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
            totals = bundle["ledger"]["totals"]
            self.assertGreaterEqual(totals["model_calls"], 3)  # spec, seal, implement turns happened before the crash
            self.assertAlmostEqual(totals["cost_usd_committed"], totals["model_calls"] * COST, places=6)
            self.assertEqual(ledger.totals()["cost_usd_committed"], totals["cost_usd_committed"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class HarnessRowAccounting(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-budget-h-"))
        self.cell = {"scheduled_index": 0, "task": "durationkit-units-001", "task_path": "examples/durationkit-task/task.json",
                     "heldout": "examples/eval/durationkit-task/heldout.py", "system": "attest", "attempt": 1, "ground_truth": "held_out_suite"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cell_with(self, provider_scenario="honest", crash_stage=None):
        budget = harness.Budget(approve_usd=2.0, per_run_cap=0.5)
        with mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: PaidFakeProvider(ledger, provider_scenario)), \
             mock.patch.object(harness, "executor_for", lambda ledger: CrashingExecutor(ledger, crash_stage) if crash_stage else FakeExecutor(ledger)):
            row = quiet(harness.run_cell, self.cell, budget, "nebius", 0.5, 22, self.tmp, 4, ROOT)
        return row, budget

    def test_crash_after_paid_calls_keeps_the_cost_in_the_row_and_the_batch(self):
        row, budget = self.run_cell_with(crash_stage="verify")
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["verdict"], "ERROR")
        self.assertTrue(row["infra_error"])
        self.assertGreater(row["cost_committed_usd"], 0)
        self.assertAlmostEqual(row["cost_committed_usd"], row["model_calls"] * COST, places=6)
        self.assertIn("sandbox exploded during verify", row["error"])
        self.assertAlmostEqual(budget.snapshot()["committed_usd"], row["cost_committed_usd"], places=4)
        self.assertTrue(Path(row["out_dir"]).joinpath("ledger.json").is_file())

    def test_uncertain_call_keeps_its_reservation_and_stops_the_batch(self):
        row, budget = self.run_cell_with(provider_scenario="uncertain_at_break")
        # an uncertain breaker call makes the adversarial gate unusable (NEEDS HUMAN); the accounting is what matters here
        self.assertIn(row["verdict"], ("NEEDS HUMAN", "ERROR"))
        self.assertTrue(row["uncertain"])
        self.assertEqual(row["uncertain_calls"], 1)
        known = (row["model_calls"] - 1) * COST
        self.assertAlmostEqual(row["cost_committed_usd"], known + RESERVE, places=6)  # the unknown call counts at its reservation
        self.assertAlmostEqual(row["cost_usd"], known, places=6)
        self.assertIn("transport-uncertain", budget.snapshot()["stopped"])
        self.assertAlmostEqual(budget.snapshot()["committed_usd"], known + RESERVE, places=4)

    def test_failed_judge_keeps_the_verdict_and_the_costs(self):
        row, budget = self.run_cell_with(crash_stage="judge")
        self.assertEqual(row["verdict"], "VERIFIED")
        self.assertIsNone(row["held_out_correct"])
        self.assertIn("sandbox exploded during judge", row["judge_error"])
        self.assertEqual(row["confusion"] if "confusion" in row else harness.classify(row), "unknown")
        self.assertGreater(row["cost_committed_usd"], 0)
        self.assertFalse(row["infra_error"])
        self.assertAlmostEqual(budget.snapshot()["committed_usd"], row["cost_committed_usd"], places=4)


class InterruptedBatch(unittest.TestCase):
    """A batch interrupted after its first cell resumes from its own report: completed rows are kept verbatim, only the
    never-executed cell runs, and the committed USD of both rows is counted. The interruption is simulated by dropping the second
    row from the report while its finished run directory stays on disk, which is exactly a finished-but-unreported run (audit
    finding AC-02): its spend must be in the resumed batch's total as well, once."""

    def args(self, out: Path, resume: bool = False):
        return argparse.Namespace(provider="nebius", tasks="durationkit-units-001", systems="baseline,attest", attempts=1, workers=1,
                                  usd_cap=0.5, approve_usd=5.0, max_calls=22, max_turns=4, out=str(out), label="t", suite="examples/eval/SUITE.json",
                                  resume=str(out) if resume else "", snapshot_root=str(ROOT), source_root=str(ROOT))

    def test_resume_runs_only_the_missing_cell_and_keeps_costs(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-budget-b-"))
        try:
            digests = harness.snapshot_digests(ROOT)
            provenance = {"fresh_process": False, "attest_revision": digests["attest_revision"], "eval_script_sha256": digests["eval_script_sha256"],
                          "examples_digest": digests["examples"], "guest_programs": {}, "python": "test", "platform": "test", "note": "test stub"}
            patches = [mock.patch.object(harness, "runtime_provenance", lambda snapshot_root, source_root: provenance),
                       mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: PaidFakeProvider(ledger)),
                       mock.patch.object(harness, "executor_for", lambda ledger: FakeExecutor(ledger))]
            with contextlib.ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                self.assertEqual(quiet(harness.run_batch, self.args(tmp)), 0)
                report = json.loads((tmp / "evaluation.json").read_text())
                self.assertTrue(report["complete"])
                self.assertEqual(len(report["rows"]), 2)
                first, dropped = report["rows"]
                full_committed = report["budget"]["committed_usd"]
                self.assertAlmostEqual(full_committed, sum(r["cost_committed_usd"] for r in report["rows"]), places=4)
                self.assertEqual(report["provenance_check"]["invalid_tasks"], [])
                self.assertEqual(report["schedule"]["max_calls_per_run"], 22)
                self.assertTrue(all(r["executed_provider"] == "nebius" and r["max_calls"] == 22 for r in report["rows"]))
                # interruption: the report holds the first row only; the second cell's finished run directory stays on disk
                report["rows"] = report["rows"][:1]
                report["complete"] = False
                (tmp / "evaluation.json").write_text(json.dumps(report, indent=2))
                self.assertEqual(quiet(harness.run_batch, self.args(tmp, resume=True)), 0)
                resumed = json.loads((tmp / "evaluation.json").read_text())
            self.assertTrue(resumed["complete"])
            self.assertEqual(len(resumed["rows"]), 2)
            self.assertEqual(resumed["rows"][0]["run_id"], first["run_id"])  # kept verbatim, not re-run
            self.assertNotEqual(resumed["rows"][1]["run_id"], report["rows"][0]["run_id"])
            # the dropped row's directory is finished but unreported: counted once, from its ledger totals, next to the two rows
            self.assertEqual([(i["run_id"], i["kind"], i["source"], i["included_in_batch_total"]) for i in resumed["interrupted"]],
                             [(dropped["run_id"], "finished_unreported", "ledger.json", True)])
            self.assertAlmostEqual(resumed["interrupted"][0]["cost_usd_committed"], dropped["cost_committed_usd"], places=6)
            self.assertAlmostEqual(resumed["budget"]["committed_usd"],
                                   sum(r["cost_committed_usd"] for r in resumed["rows"]) + dropped["cost_committed_usd"], places=4)
            self.assertAlmostEqual(resumed["starting_total"]["committed_usd"], first["cost_committed_usd"] + dropped["cost_committed_usd"], places=6)
            schedule = json.loads((tmp / "schedule.json").read_text())
            self.assertEqual(schedule["resumptions"][0]["cells"], [1])
            self.assertEqual(len([d for d in (tmp / "runs").iterdir()]), 3)  # two from the first batch, one from the resumption
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ConsoleBudgetAccounting(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-budget-c-"))
        from attest.app.db import Store
        self.store = Store(self.tmp / "attest.db")
        self.today = "2026-10-17T00:00:00"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_daily_budget_counts_errored_runs_and_reserves_for_interrupted_ones(self):
        self.store.create_run(run_id="ok", task_id="t", task_title="T", provider="nebius", profile_label="x", status="finished", stage="finished",
                              created_at="2026-10-17T10:00:00", cost_usd=0.10, cost_committed_usd=0.10)
        self.store.create_run(run_id="crashed", task_id="t", task_title="T", provider="nebius", profile_label="x", status="error", stage="error",
                              created_at="2026-10-17T11:00:00", cost_usd=0.07, cost_committed_usd=0.12)
        self.store.create_run(run_id="orphan", task_id="t", task_title="T", provider="nebius", profile_label="x", status="running", stage="implement",
                              created_at="2026-10-17T12:00:00")
        self.assertAlmostEqual(self.store._nebius_committed(self.today), 0.22, places=6)  # finished plus errored, at the committed figure
        reconciled = self.store.reconcile_interrupted(per_run_cap=0.5)
        self.assertEqual(reconciled[0]["action"], "interrupted")
        self.assertEqual(reconciled[0]["cost_committed_usd"], 0.5)
        self.assertAlmostEqual(self.store._nebius_committed(self.today), 0.72, places=6)
        remaining = self.store.nebius_remaining(0.5, 2.0, self.today)
        self.assertAlmostEqual(remaining["remaining_usd"], 2.0 - 0.72, places=4)

    def test_worker_keeps_the_cost_of_a_run_that_crashed_after_paid_calls(self):
        from attest.app.worker import Worker
        worker = Worker(self.store, self.tmp, TASK.parent.parent, max_turns=4)
        self.store.create_run(run_id="r1", task_id="durationkit-units-001", task_title="T", provider="nebius", profile_label="judge-demo",
                              status="queued", stage="queued", created_at=utcnow(), requester="t")
        with mock.patch.object(worker, "build_runtime", lambda run_id, provider_name, ledger: (PaidFakeProvider(ledger), CrashingExecutor(ledger, "verify"), None)):
            quiet(worker._execute, "r1", TASK, "nebius", "judge-demo")
        row = self.store.get_run("r1")
        self.assertEqual(row["status"], "error")
        self.assertIn("sandbox exploded during verify", row["error"])
        self.assertGreater(row["cost_committed_usd"], 0)
        self.assertAlmostEqual(row["cost_committed_usd"], row["model_calls"] * COST, places=6)
        self.assertGreater(self.store._nebius_committed("2026-10-17T00:00:00"), 0)


if __name__ == "__main__":
    unittest.main()


class RegisterOnly(unittest.TestCase):
    """The documented M5 command registers 8 tasks x 2 systems x 2 attempts = 32 cells and starts nothing."""

    def test_m5_suite_registers_32_cells_without_running(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-register-"))
        try:
            digests = harness.snapshot_digests(ROOT)
            provenance = {"fresh_process": False, "attest_revision": digests["attest_revision"], "eval_script_sha256": digests["eval_script_sha256"],
                          "examples_digest": digests["examples"], "guest_programs": {}, "python": "test", "platform": "test", "note": "test stub"}
            args = argparse.Namespace(provider="nebius", tasks="", systems="baseline,attest", attempts=2, workers=2, usd_cap=0.5, approve_usd=9.0,
                                      max_calls=22, max_turns=14, out=str(tmp), label="m5-final", suite="examples/eval/SUITE-M5.json", resume="",
                                      snapshot_root=str(ROOT), source_root=str(ROOT), register_only=True)
            started = []
            with mock.patch.object(harness, "runtime_provenance", lambda a, b: provenance), \
                 mock.patch.object(harness, "build_provider", lambda name, ledger, cap, calls, notify=None: PaidFakeProvider(ledger)), \
                 mock.patch.object(harness, "run_cell", lambda *a, **k: started.append(a) or {}):
                self.assertEqual(quiet(harness.run_batch, args), 0)
            self.assertEqual(started, [])
            schedule = json.loads((tmp / "schedule.json").read_text())
            self.assertTrue(schedule["register_only"])
            self.assertEqual(len(schedule["cells"]), 32)
            self.assertEqual(len(schedule["tasks"]), 8)
            self.assertEqual(sum(1 for c in schedule["cells"] if c["ground_truth"] == "unsatisfiable"), 4)
            self.assertTrue(all(c["task_spec_sha256"] and c["heldout_sha256"] for c in schedule["cells"]))
            self.assertFalse((tmp / "evaluation.json").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
