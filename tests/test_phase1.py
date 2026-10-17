"""Phase-1 hardening unit tests: conservative ledger accounting, atomic budget reservation, restart reconciliation
and bounded retention that never touches imported evidence."""

import json
import tempfile
import unittest
from pathlib import Path

from attest.app.db import BudgetError, Store
from attest.ledger import Ledger, ModelCall, utcnow


def _call(cost, reserved, ok=True):
    return ModelCall(provider="nebius_tokenfactory", role="implement", stage="s", requested_model="m", requested_effort=None,
                     returned_model="m", returned_effort=None, started_at_utc=utcnow(), elapsed_ms=1, gateway_duration_ms=None,
                     prompt_chars=10, tokens_in=1, tokens_out=1, tokens_cached=0, usage_raw={}, cost_usd=cost,
                     cost_note="n", ok=ok, reserved_usd=reserved)


class LedgerAccounting(unittest.TestCase):
    def test_uncertain_calls_use_reservation_in_committed_total(self):
        ledger = Ledger()
        ledger.add_call(_call(0.01, 0.05))           # priced
        ledger.add_call(_call(None, 0.07, ok=False))  # uncertain: no price returned, reservation stands
        totals = ledger.totals()
        self.assertAlmostEqual(totals["cost_usd"], 0.01, places=6)              # only the priced call
        self.assertAlmostEqual(totals["cost_usd_committed"], 0.08, places=6)    # priced + reservation
        self.assertEqual(totals["uncertain_unpriced_calls"], 1)


class Budgeting(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-p1-"))
        self.store = Store(self.tmp / "t.db")
        self.today = "2026-10-15T00:00:00"

    def _reserve(self, run_id):
        self.store.create_run_reserving(0.5, 2.0, self.today, run_id=run_id, task_id="t", task_title="T", provider="nebius",
                                        profile_label="judge", status="queued", stage="queued", created_at=utcnow(), requester="x")

    def test_reservations_are_atomic_and_cap_binds(self):
        for i in range(4):
            self._reserve(f"r{i}")           # 4 * 0.5 = 2.0 reserved == cap
        with self.assertRaises(BudgetError):
            self._reserve("r4")              # the 5th cannot be reserved
        for i in range(4):
            self.store.update_run(f"r{i}", status="finished", cost_usd=0.03, cost_committed_usd=0.03, finished_at=utcnow())
        self._reserve("r5")                  # once the reservations clear, room returns
        self.assertIsNotNone(self.store.get_run("r5"))

    def test_recheck_counts_active_runs(self):
        self._reserve("a")
        self.store.update_run("a", status="running")
        ok, _ = self.store.nebius_budget_ok(0.5, 2.0, self.today)
        self.assertTrue(ok)

    def test_reconcile_marks_interrupted_and_finalizes_from_bundle(self):
        self.store.create_run(run_id="lost", task_id="t", task_title="T", provider="nebius", profile_label="judge",
                              status="running", stage="verify", created_at=utcnow(), requester="x")
        bundle_dir = self.tmp / "runs" / "done"
        bundle_dir.mkdir(parents=True)
        (bundle_dir / "proof_bundle.json").write_text(
            '{"verdict":{"verdict":"VERIFIED","reasons":[]},"ledger":{"totals":{"cost_usd":0.04,"cost_usd_committed":0.04}},'
            '"finished_at_utc":"2026-10-15T01:00:00+00:00"}', encoding="utf-8")
        self.store.create_run(run_id="done", task_id="t", task_title="T", provider="nebius", profile_label="judge",
                              status="running", stage="verify", created_at=utcnow(), out_dir=str(bundle_dir), requester="x")
        actions = {r["run_id"]: r["action"] for r in self.store.reconcile_interrupted()}
        self.assertEqual(actions, {"lost": "interrupted", "done": "finalized"})
        self.assertEqual(self.store.get_run("lost")["status"], "error")
        self.assertEqual(self.store.get_run("done")["verdict"], "VERIFIED")

    def test_prune_keeps_recent_protects_verified_and_imported_evidence(self):
        runs = self.tmp / "runs"
        runs.mkdir(exist_ok=True)
        evidence = self.tmp / "reports" / "ev"
        evidence.mkdir(parents=True)
        (evidence / "proof_bundle.json").write_text("{}", encoding="utf-8")
        self.store.create_run(run_id="imported", task_id="t", task_title="T", provider="nebius", profile_label="imported",
                              status="finished", verdict="NEEDS HUMAN", created_at="2026-10-01T00:00:00",
                              out_dir=str(evidence), requester="import")
        for i in range(5):
            d = runs / f"c{i}"
            d.mkdir()
            (d / "x").write_text("y", encoding="utf-8")
            self.store.create_run(run_id=f"c{i}", task_id="t", task_title="T", provider="nebius", profile_label="judge",
                                  status="finished", verdict="VERIFIED" if i == 0 else "NEEDS HUMAN",
                                  created_at=f"2026-10-10T00:00:0{i}", out_dir=str(d), requester="x")
        pruned = self.store.prune_runs(runs, keep=2)
        self.assertTrue(evidence.exists(), "imported evidence outside the run dir must never be pruned")
        self.assertTrue((runs / "c0").exists(), "a VERIFIED run is protected from pruning")
        self.assertNotIn("imported", pruned)
        self.assertNotIn("c0", pruned)


class ImportDedupe(unittest.TestCase):
    """M1.6: the store recognises its own runs when importing from disk and removes legacy duplicate rows."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-dedupe-"))
        self.store = Store(self.tmp / "t.db")
        self.run_dir = self.tmp / "runs" / "task-20261016T100000Z"
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "proof_bundle.json").write_text(json.dumps({
            "run_id": "task-20261016T100000Z", "started_at_utc": "2026-10-16T10:00:00+00:00", "finished_at_utc": "2026-10-16T10:04:00+00:00",
            "task": {"id": "task", "title": "T"}, "profile": {"label": "judge-demo", "provider": {"provider": "nebius_tokenfactory"}},
            "verdict": {"verdict": "VERIFIED", "reasons": [], "warnings": []}, "ledger": {"totals": {"cost_usd": 0.05, "cost_usd_committed": 0.05}}}), encoding="utf-8")

    def test_import_skips_a_directory_the_console_already_owns(self):
        # pre-M1 console rows carried a microsecond id that differs from the bundle's second-resolution run_id
        self.store.create_run(run_id="task-20261016T100000123456Z", task_id="task", task_title="T", provider="nebius", profile_label="judge-demo",
                              status="finished", verdict="VERIFIED", created_at="2026-10-16T10:00:00", out_dir=str(self.run_dir), requester="1.2.3.4")
        self.assertFalse(self.store.import_run_dir(self.run_dir), "the directory is already owned by a row")
        self.assertEqual(len(self.store.list_runs()), 1)

    def test_dedupe_removes_the_later_duplicate_and_keeps_the_console_row(self):
        self.store.create_run(run_id="task-20261016T100000123456Z", task_id="task", task_title="T", provider="nebius", profile_label="judge-demo",
                              status="finished", verdict="VERIFIED", created_at="2026-10-16T10:00:00", out_dir=str(self.run_dir), requester="1.2.3.4")
        self.store.create_run(run_id="task-20261016T100000Z", task_id="task", task_title="T", provider="nebius", profile_label="imported",
                              status="finished", verdict="VERIFIED", created_at="2026-10-16T10:00:00+00:00", out_dir=str(self.run_dir), requester="import")
        self.store.add_event("task-20261016T100000Z", utcnow(), "x", "imported duplicate")
        removed = self.store.dedupe_imports()
        self.assertEqual([r["run_id"] for r in removed], ["task-20261016T100000Z"])
        self.assertEqual(removed[0]["kept"], "task-20261016T100000123456Z")
        self.assertEqual([r["run_id"] for r in self.store.list_runs()], ["task-20261016T100000123456Z"])
        self.assertEqual(self.store.events("task-20261016T100000Z"), [])
        self.assertTrue(self.run_dir.exists(), "rows are removed, run directories never")


if __name__ == "__main__":
    unittest.main()
