"""Offline tests for the console API additions of milestone M3 (run-row summary, provenance, exhibits, manifest,
estimates, profiles, artifact allowlist) and the replay fixture script. Uses FastAPI's TestClient against a temporary
data directory with recorded evidence imported from the reports; no inference, no sandboxes, no network."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

FIXTURES = {
    "durationkit-judge": ROOT / "reports/attest-verification-2026-10-15/console-run-durationkit-nebius",      # VERIFIED, Nemotron, with console-record.json
    "rle-bug": ROOT / "reports/attest-evaluation-2026-10-16/runs/rle-encode-20261015T180226Z",              # NEEDS HUMAN, implementation bug
    "brackets-m1": ROOT / "reports/attest-m1-2026-10-16/runs/balanced-brackets-20261016T192809Z",           # NEEDS HUMAN, test defect, bound suites
    "error-422": ROOT / "reports/attest-first-slice-2026-10-15/nebius-pilot-attempt1-http422",             # ERROR before any gate
}
try:
    import httpx  # noqa: F401
    from fastapi.testclient import TestClient
    HAVE_CLIENT = True
except ImportError:  # pragma: no cover - the development venv installs httpx; deployments do not need it
    HAVE_CLIENT = False


def _make_app(tmp: Path, admin_token: str = "test-token"):
    imports = tmp / "imports"
    imports.mkdir()
    for name, src in FIXTURES.items():
        if src.is_dir():
            (imports / name).symlink_to(src, target_is_directory=True)
    os.environ["ATTEST_DATA_DIR"] = str(tmp / "data")
    os.environ["ATTEST_IMPORT_DIRS"] = str(imports)
    os.environ["ATTEST_IMPORT_PROVIDERS"] = "nebius,codex"  # the fixtures include development runs; the public default is nebius only
    os.environ["ATTEST_ADMIN_TOKEN"] = admin_token
    os.environ["ATTEST_PUBLIC_RUNS_PER_HOUR"] = "3"
    sys.modules.pop("attest.app.server", None)
    return importlib.import_module("attest.app.server")


@unittest.skipUnless(HAVE_CLIENT, "fastapi.testclient needs httpx in the development venv")
class ConsoleApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls.tmpdir.name)
        cls.server = _make_app(cls.tmp)
        cls.client = TestClient(cls.server.app)
        cls.runs = cls.client.get("/api/runs").json()["runs"]
        cls.by_task = {}
        for row in cls.runs:
            cls.by_task.setdefault(row["task_id"], []).append(row)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _run(self, task_id: str, verdict: str) -> dict:
        for row in self.by_task.get(task_id, []):
            if row["verdict"] == verdict:
                return row
        self.skipTest(f"fixture {task_id}/{verdict} not available")

    def test_health_reports_remaining_budget_and_public_rate(self):
        h = self.client.get("/api/health").json()
        self.assertIn("remaining_usd", h["budget"])
        self.assertAlmostEqual(h["budget"]["remaining_usd"], h["budget"]["daily_cap_usd"])  # nothing spent today in a fresh store
        self.assertEqual(h["public_runs_per_hour"], 3)

    def test_run_rows_carry_summary_and_imported_provenance(self):
        self.assertTrue(self.runs)
        for row in self.runs:
            self.assertIn("summary", row)
            self.assertEqual(row["summary"]["provenance"], "imported")
            self.assertEqual(row["provenance"], "imported")
            self.assertIn("duration_s", row["summary"])
        judge = self._run("durationkit-units-001", "VERIFIED")
        self.assertGreater(judge["summary"]["duration_s"], 100)
        self.assertAlmostEqual(judge["summary"]["cost_usd"], 0.072312)

    def test_tasks_carry_recorded_estimates_from_public_provider_runs(self):
        tasks = {t["task_id"]: t for t in self.client.get("/api/tasks").json()["tasks"]}
        est = tasks["durationkit-units-001"]["estimate"]
        self.assertEqual(est["runs"], 1)  # the ERROR run is excluded from the ranges
        self.assertEqual(est["recorded_runs"], 2)
        self.assertEqual(est["latest_verdict"], "VERIFIED")
        self.assertAlmostEqual(est["cost_min_usd"], 0.072312)
        self.assertGreater(est["duration_min_s"], 100)
        self.assertTrue(est["latest_run_id"])

    def test_run_detail_has_exhibits_manifest_and_counterexamples(self):
        row = self._run("rle-encode", "NEEDS HUMAN")
        d = self.client.get(f"/api/runs/{row['run_id']}").json()
        self.assertEqual(d["provenance"], "imported")
        ex = d["exhibits"]
        self.assertEqual(ex["decision"]["verdict"], "NEEDS HUMAN")
        self.assertEqual(ex["decision"]["statement"], "Hold this patch.")
        self.assertEqual(ex["decision"]["reason_class"], "adversarial_implementation_bug")
        self.assertEqual([e["ref"] for e in ex["exhibits"]], ["E1", "E2", "E3", "E4", "E5", "E6", "E7"])
        self.assertEqual({g["gate"] for g in ex["gates"]} & {"sealed_binding", "adversarial_tests"}, {"sealed_binding", "adversarial_tests"})
        names = {c["name"]: c for c in ex["counterexamples"]}
        self.assertIn("test_roundtrip_with_digits", names)
        self.assertEqual(names["test_roundtrip_with_digits"]["classification"], "implementation_bug")
        self.assertTrue(names["test_roundtrip_with_digits"]["contract_basis"])
        self.assertTrue(ex["proves"]["proves"] and ex["proves"]["does_not_prove"])
        self.assertFalse(d["manifest"]["recorded"])  # recorded before M2: digests computed on request
        self.assertGreater(d["manifest"]["file_count"], 5)
        self.assertTrue(all(len(f["sha256"]) == 64 for f in d["manifest"]["files"]))

    def test_error_run_decision_cites_failure_record(self):
        row = self._run("durationkit-units-001", "ERROR")
        d = self.client.get(f"/api/runs/{row['run_id']}").json()
        self.assertEqual(d["exhibits"]["decision"]["statement"], "This run did not complete.")
        e7 = [e for e in d["exhibits"]["exhibits"] if e["ref"] == "E7"][0]
        self.assertTrue(e7["shown"])
        self.assertEqual(e7["status"], "fail")
        self.assertFalse(e7["detail"]["retried"])

    def test_imported_console_record_events_are_available(self):
        judge = self._run("durationkit-units-001", "VERIFIED")
        body = self.client.get(f"/api/runs/{judge['run_id']}/events?after=0").json()
        self.assertEqual(len(body["events"]), 29)
        self.assertEqual(body["status"], "finished")
        self.assertIn("meters", body)
        self.assertEqual(body["meters"]["model_calls"], 17)

    def test_artifact_allowlist_is_a_closed_set_without_traversal(self):
        row = self._run("balanced-brackets", "NEEDS HUMAN")
        base = f"/api/runs/{row['run_id']}/artifacts/"
        self.assertEqual(self.client.get(base + "tamper_scan.json").status_code, 200)
        self.assertEqual(self.client.get(base + "mutants_m01-17781654c1.py").status_code, 200)
        self.assertEqual(self.client.get(base + "sealed/test_sealed.attempt1.py").status_code, 200)
        self.assertEqual(self.client.get(base + "arbitration/adversarial_corrected.py").status_code, 200)
        self.assertEqual(self.client.get(base + "manifest.json").status_code, 404)  # none written before M2
        self.assertEqual(self.client.get(base + "../proof_bundle.json").status_code, 404)
        self.assertEqual(self.client.get(base + "mutants_..%2F..%2Fetc.py").status_code, 404)
        self.assertEqual(self.client.get(base + "trajectory.jsonl").status_code, 200)

    def test_profiles_hide_the_team_profile_without_the_token(self):
        public = self.client.get("/api/profiles").json()
        self.assertEqual([p["id"] for p in public["profiles"]], ["nebius"])
        self.assertFalse(public["team"])
        wrong = self.client.post("/api/profiles", json={"admin_token": "nope"}).json()
        self.assertEqual(len(wrong["profiles"]), 1)
        self.assertNotIn("codex", json.dumps(public).lower())
        team = self.client.post("/api/profiles", json={"admin_token": "test-token"}).json()
        self.assertTrue(team["team"])
        self.assertEqual(len(team["profiles"]), 2)

    def test_public_page_and_unauthenticated_responses_name_no_gateway(self):
        for path in ("/", "/static/app.js", "/static/styles.css", "/api/health", "/api/tasks", "/api/profiles"):
            body = self.client.get(path).text.lower()
            self.assertNotIn("codex", body, path)
            self.assertNotIn("axiqo", body, path)

    def test_development_provider_still_requires_the_token(self):
        self.assertEqual(self.client.post("/api/runs", json={"task_id": "durationkit-units-001", "provider": "codex"}).status_code, 403)
        self.assertEqual(self.client.post("/api/runs", json={"task_id": "durationkit-units-001", "provider": "other"}).status_code, 400)

    def test_run_page_serves_the_console_for_deep_links(self):
        row = self.runs[0]
        html = self.client.get(f"/runs/{row['run_id']}").text
        self.assertIn('id="main"', html)
        self.assertIn("Browse recorded evidence", html)
        self.assertIn("Planned, not in this build", html)

    def test_replay_fixture_is_reported_as_synthetic(self):
        from console_replay import events_from_record, replay
        src = FIXTURES["durationkit-judge"]
        events = events_from_record(src / "console-record.json")
        self.assertEqual(len(events), 29)
        result = replay(self.tmp / "data" / "attest.db", src, events[:5], interval=0.0, run_id="replay-test-1", quiet=True)
        self.assertEqual(result["verdict"], "VERIFIED")
        d = self.client.get("/api/runs/replay-test-1").json()
        self.assertEqual(d["provenance"], "synthetic")
        self.assertEqual(d["run"]["status"], "finished")
        self.assertEqual(len(d["events"]), 5)
        self.assertEqual(d["run"]["model_calls"], 17)
        ev = self.client.get("/api/runs/replay-test-1/events?after=3").json()
        self.assertEqual([e["seq"] for e in ev["events"]], [4, 5])

    def test_replay_refuses_production_data_directories(self):
        from console_replay import guard_store
        with self.assertRaises(SystemExit):
            guard_store(Path("/var/lib/attest/attest.db"))


class StoreHelpers(unittest.TestCase):
    def test_duration_and_budget_helpers(self):
        from attest.app.db import Store, duration_seconds
        self.assertEqual(duration_seconds("2026-10-15T10:00:00+00:00", "2026-10-15T10:04:30+00:00"), 270.0)
        self.assertIsNone(duration_seconds(None, "2026-10-15T10:04:30+00:00"))
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "s.db")
            store.create_run(run_id="a", task_id="t", task_title="T", provider="nebius", profile_label="judge-demo", status="finished",
                             verdict="VERIFIED", created_at="2026-10-17T01:00:00", started_at="2026-10-17T01:00:00", finished_at="2026-10-17T01:03:00",
                             cost_usd=0.05, cost_committed_usd=0.06, requester="1.2.3.4")
            store.create_run(run_id="b", task_id="t", task_title="T", provider="nebius", profile_label="judge-demo", status="running",
                             created_at="2026-10-17T01:05:00", requester="1.2.3.4")
            remaining = store.nebius_remaining(0.5, 2.0, "2026-10-17T00:00:00")
            self.assertAlmostEqual(remaining["committed_usd"], 0.06)
            self.assertEqual(remaining["active_runs"], 1)
            self.assertAlmostEqual(remaining["remaining_usd"], 2.0 - 0.06 - 0.5)
            est = store.task_estimates()["t"]
            self.assertEqual(est["runs"], 1)
            self.assertAlmostEqual(est["cost_min_usd"], 0.06)
            self.assertEqual(est["duration_min_s"], 180.0)
            self.assertEqual(est["latest_run_id"], "a")


if __name__ == "__main__":
    unittest.main()
