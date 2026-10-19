"""Acceptance tests for the console, API and accounting repairs of the 19 October 2026 audit: API-01 to API-11, AC-05, AC-06,
the publication contract for team runs, the containment of artifact downloads and the revision-5 follow-up finding R5-07
(the team token is read from the X-Attest-Token header only; team downloads use short-lived, run-scoped tickets). Offline
only: FastAPI's TestClient against a temporary data directory, the worker loop idled (alive but consuming nothing) or stopped,
sockets blocked, no inference, no sandboxes, no network. The auditor's reproductions under reports/attest-audit-2026-10-19/
and reports/attest-revision5-review-2026-10-19/ assert the faulty behaviour; these tests assert the repaired behaviour."""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import hmac
import importlib
import io
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from attest.app import db as db_module  # noqa: E402
from attest.app.db import PUBLIC, TEAM, BudgetError, Store  # noqa: E402
from attest.app.worker import Worker  # noqa: E402
from attest.core.manifest import build_manifest, verify_manifest  # noqa: E402
from attest.ledger import JOURNAL_FILE, Ledger, utcnow  # noqa: E402
from tests.test_phase1 import _call as paid_call  # noqa: E402

try:
    import httpx  # noqa: F401
    from fastapi.testclient import TestClient
    HAVE_CLIENT = True
except ImportError:  # pragma: no cover - the development venv installs httpx
    HAVE_CLIENT = False

NODE = shutil.which("node")
TOKEN = "synthetic-" + "team-token"  # assembled at run time: the public export scans tests/ for secret-shaped assignments
TEAM_HEADERS = {"X-Attest-Token": TOKEN}
MARKER_IP = "198.51.100.10"
MARKER_PATH = "/opt/attest/private_module.py"
MARKER = "SYNTHETIC_INTERNAL_DETAIL"


def no_network(*args, **kwargs):
    raise AssertionError("network access is blocked by this offline test")


def idle_loop(self):
    """A worker thread that stays alive but consumes nothing: admission is open and queued runs stay queued."""
    self._stop.wait()


def dead_loop(self):
    """A worker thread that dies at once."""
    return None


def today_start() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT00:00:00")


class PeerAddress:
    """ASGI shim that sets the peer address the application sees; this starlette's TestClient cannot."""

    def __init__(self, app, host: str):
        self.app, self.host = app, host

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            scope = dict(scope, client=(self.host, 50000))
        await self.app(scope, receive, send)


def _bundle(run_id: str, provider: str = "nebius_tokenfactory", verdict: str = "VERIFIED", started: str | None = None,
            finished: str | None = None, totals: dict | None = None, ledger: dict | None = None) -> dict:
    body = {"run_id": run_id, "started_at_utc": started or utcnow(), "finished_at_utc": finished or utcnow(),
            "task": {"id": "audit-sample", "title": "Synthetic offline task"},
            "profile": {"label": "synthetic", "provider": {"provider": provider}},
            "verdict": {"verdict": verdict, "reasons": [], "warnings": []},
            "ledger": {"totals": totals if totals is not None else {"cost_usd": 0.01, "cost_usd_committed": 0.01}, "model_calls": [],
                       "sandbox_operations": []}}
    if ledger is not None:
        body["ledger"] = ledger
    return body


def _row(**over) -> dict:
    base = dict(task_id="audit-sample", task_title="Synthetic offline task", provider="nebius", profile_label="judge-demo", status="finished",
                verdict="VERIFIED", created_at=utcnow(), requester="x")
    base.update(over)
    return base


@unittest.skipUnless(HAVE_CLIENT, "fastapi.testclient needs httpx in the development venv")
class ConsoleHarness(unittest.TestCase):
    """A fresh application module per test class: temporary data directory, idled (or dead) worker loop, blocked sockets."""

    LOOP = staticmethod(idle_loop)
    ENV: dict = {}

    @classmethod
    def extra_env(cls, tmp: Path) -> dict:
        return {}

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory(prefix="attest-audit-console-")
        cls.tmp = Path(cls.tmpdir.name)
        examples = cls.tmp / "examples" / "sample"
        examples.mkdir(parents=True)
        (examples / "task.json").write_text(json.dumps({"id": "audit-sample", "title": "Synthetic offline task",
                                                        "statement": "No execution is performed.", "acceptance_criteria": ["offline"]}), encoding="utf-8")
        env = {"ATTEST_DATA_DIR": str(cls.tmp / "data"), "ATTEST_EXAMPLES_DIR": str(examples.parent), "ATTEST_IMPORT_DIRS": str(cls.tmp / "no-imports"),
               "ATTEST_IMPORT_PROVIDERS": "nebius", "ATTEST_ADMIN_TOKEN": TOKEN, "ATTEST_PUBLIC_RUNS_PER_HOUR": "3", "ATTEST_DAILY_USD_CAP": "100",
               "ATTEST_MIN_FREE_MB": "0", "ATTEST_MIN_FREE_FRAC": "0", "ATTEST_TRUSTED_PROXIES": "127.0.0.1,::1", "ATTEST_RETENTION_KEEP_ERRORS": "10"}
        env.update(cls.ENV)
        env.update(cls.extra_env(cls.tmp))
        cls.patches = [patch.dict(os.environ, env), patch.object(Worker, "_loop", cls.LOOP), patch.object(Worker, "build_runtime", no_network),
                       patch.object(socket.socket, "connect", no_network), patch.object(socket.socket, "connect_ex", no_network),
                       patch.object(socket, "create_connection", no_network)]
        for item in cls.patches:
            item.start()
        sys.modules.pop("attest.app.server", None)
        cls.server = importlib.import_module("attest.app.server")
        cls.store = cls.server.store
        cls.worker = cls.server.worker
        cls.client = TestClient(cls.server.app, raise_server_exceptions=False)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.worker.stop()
        cls.store._conn.close()
        sys.modules.pop("attest.app.server", None)
        for item in reversed(cls.patches):
            item.stop()
        cls.tmpdir.cleanup()

    def run_dir(self, run_id: str) -> Path:
        out = self.tmp / "data" / "runs" / run_id
        out.mkdir(parents=True, exist_ok=True)
        return out


# ---------------------------------------------------------------------------------------------------------------- API-01
class TrustedProxyIdentity(ConsoleHarness):
    def test_requester_policy_is_explicit(self):
        requester = self.server.requester_from
        self.assertEqual(requester("203.0.113.9", "198.51.100.20, 192.0.2.1"), "203.0.113.9")  # untrusted peer: the header is ignored
        self.assertEqual(requester("testclient", "198.51.100.20"), "testclient")
        self.assertEqual(requester("127.0.0.1", "198.51.100.20, 192.0.2.1"), "192.0.2.1")  # trusted proxy: the LAST item, which it appended
        self.assertEqual(requester("127.0.0.1", "198.51.100.21, 192.0.2.1"), "192.0.2.1")  # the caller's first item changes nothing
        self.assertEqual(requester("::1", "2001:db8::7"), "2001:db8::7")
        self.assertEqual(requester("127.0.0.1", "not-an-address"), "127.0.0.1")  # malformed: attributed to the proxy itself
        self.assertEqual(requester("127.0.0.1", ""), "127.0.0.1")
        self.assertEqual(requester("127.0.0.1", None), "127.0.0.1")
        self.assertEqual(requester(None, "198.51.100.20"), "unknown")
        self.assertEqual([str(n) for n in self.server.TRUSTED_PROXIES], ["127.0.0.1/32", "::1/128"])

    def test_forwarded_header_rotation_does_not_reset_the_quota_behind_the_proxy(self):
        proxied = TestClient(PeerAddress(self.server.app, "127.0.0.1"), raise_server_exceptions=False)
        for i in range(3):
            self.store.create_run(run_id=f"seed-{i}", **_row(created_at=utcnow(), requester="192.0.2.1"))
        body = {"task_id": "audit-sample", "provider": "nebius"}
        limited = proxied.post("/api/runs", json=body, headers={"x-forwarded-for": "198.51.100.20, 192.0.2.1"})
        rotated = proxied.post("/api/runs", json=body, headers={"x-forwarded-for": "198.51.100.21, 192.0.2.1"})
        self.assertEqual((limited.status_code, rotated.status_code), (429, 429))
        self.assertIn("rate limit", rotated.json()["detail"])
        self.assertEqual(self.store.count_recent("192.0.2.1", "2000-01-01"), 3, "no row was created for the refused requests")
        other = proxied.post("/api/runs", json=body, headers={"x-forwarded-for": "198.51.100.20, 192.0.2.77"})
        self.assertEqual(other.status_code, 200, "a different visitor behind the same proxy is admitted")
        self.assertEqual(self.store.get_run(other.json()["run_id"])["requester"], "192.0.2.77")

    def test_untrusted_peer_cannot_choose_its_identity(self):
        # the TestClient peer is not a trusted proxy: three runs whatever the header says, then 429 for the fourth
        statuses = [self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"}, headers={"x-forwarded-for": f"198.51.100.{30 + i}"}).status_code
                    for i in range(4)]
        self.assertEqual(statuses, [200, 200, 200, 429])
        self.assertEqual(self.store.count_recent("testclient", "2000-01-01"), 3)


# ---------------------------------------------------------------------------------------------------------------- API-02
class AtomicAdmission(ConsoleHarness):
    def test_simultaneous_requests_from_one_visitor_admit_at_most_the_quota(self):
        barrier = threading.Barrier(4, timeout=10)
        original = self.worker.enqueue

        def synchronized(*args, **kwargs):
            barrier.wait()  # all four admissions start together; the quota check and the insert share the store lock
            return original(*args, **kwargs)

        def request(_):
            with TestClient(self.server.app, raise_server_exceptions=False) as local:
                response = local.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
                return response.status_code, response.json()

        with patch.object(self.worker, "enqueue", synchronized), concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(request, range(4)))
        self.assertEqual(sorted(status for status, _ in responses), [200, 200, 200, 429], responses)
        rejected = next(body for status, body in responses if status == 429)
        self.assertIn("rate limit", rejected["detail"])
        self.assertEqual(self.store.count_recent("testclient", "2000-01-01"), 3, "the rejected request left no row")
        self.assertEqual(self.store.active_count(), 3)
        self.assertEqual(self.worker.queue.qsize(), 3)
        self.assertEqual(self.store.nebius_remaining(0.5, 100.0, "2000-01-01")["active_runs"], 3, "exactly three reservations")


# ---------------------------------------------------------------------------------------------------------------- API-03
class MaterialisedReads(unittest.TestCase):
    def test_concurrent_reads_and_writes_on_the_shared_connection_never_fail(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-audit-sqlite-"))
        try:
            store = Store(tmp / "s.db")
            for i in range(5):
                store.create_run(run_id=f"r{i}", **_row(created_at=f"2026-10-19T00:00:0{i}", requester="synthetic-visitor", cost_usd=0.01, cost_committed_usd=0.01))
                store.add_event(f"r{i}", utcnow(), "s", "m")
            failures: list[str] = []

            def reader(_):
                for _ in range(120):
                    try:
                        if store.count_recent("synthetic-visitor", "2000-01-01") != 5:
                            failures.append("count")
                        if len(store.list_runs(include_team=True)) != 5:
                            failures.append("list")
                        if store.get_run("r1")["run_id"] != "r1":
                            failures.append("detail")
                        if len(store.events("r2")) != 1:
                            failures.append("events")
                        if abs(store.nebius_remaining(0.5, 2.0, "2000-01-01")["committed_usd"] - 0.05) > 1e-9:
                            failures.append("budget")
                    except Exception as error:  # noqa: BLE001 - every exception is a finding
                        failures.append(f"{type(error).__name__}: {error}")

            def writer(_):
                for n in range(120):
                    try:
                        store.update_run("r3", stage=f"s{n}")
                    except Exception as error:  # noqa: BLE001
                        failures.append(f"write {type(error).__name__}: {error}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(reader, k) for k in range(4)] + [pool.submit(writer, 0)]
                for future in futures:
                    future.result()
            self.assertEqual(failures, [])
            self.assertFalse(hasattr(store, "_exec"), "no helper may hand a live cursor out from under the lock")
            for helper in ("_rows", "_row_one", "_write"):
                self.assertTrue(callable(getattr(store, helper)))
            store._conn.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------------------- API-04
class PublicProjection(ConsoleHarness):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        out = cls.tmp / "data" / "runs" / "proj-1"
        out.mkdir(parents=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("proj-1")), encoding="utf-8")
        cls.store.create_run(run_id="proj-1", **_row(started_at=utcnow(), finished_at=utcnow(), out_dir=str(out), requester=MARKER_IP, cost_usd=0.01))
        cls.store.create_run(run_id="proj-2", **_row(status="error", verdict=None, finished_at=utcnow(), out_dir="/opt/attest/private/runs/proj-2",
                                                      requester=MARKER_IP, error=f"RuntimeError: {MARKER} at {MARKER_PATH}", error_code="pipeline_error",
                                                      error_ref="abc123def456",
                                                      error_detail=f'Traceback (most recent call last):\n  File "{MARKER_PATH}", line 1\nRuntimeError: {MARKER}'))
        cls.store.add_event("proj-1", utcnow(), "s", "event text")

    def assert_clean(self, text: str, where: str):
        for forbidden in (MARKER_IP, MARKER_PATH, MARKER, str(self.tmp), "/opt/attest", '"requester"', '"out_dir"', '"error_detail"', '"error_ref"', "Traceback"):
            self.assertNotIn(forbidden, text, f"{forbidden!r} leaked through {where}")

    def test_public_responses_carry_no_identity_paths_or_diagnostics(self):
        for path in ("/api/runs", "/api/runs/proj-1", "/api/runs/proj-2", "/api/runs/proj-1/events", "/api/runs/proj-2/events", "/api/tasks", "/api/health"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assert_clean(response.text, path)
        rows = {r["run_id"]: r for r in self.client.get("/api/runs").json()["runs"]}
        allowed = set(self.server.PUBLIC_RUN_FIELDS) | {"has_artifacts", "error_code", "error_public", "summary", "provenance"}
        for row in rows.values():
            self.assertTrue(set(row) <= allowed, set(row) - allowed)
        self.assertTrue(rows["proj-1"]["has_artifacts"])
        self.assertIsNone(rows["proj-1"]["error_code"])
        self.assertIsNone(rows["proj-1"]["error_public"])
        self.assertFalse(rows["proj-2"]["has_artifacts"])
        self.assertEqual(rows["proj-2"]["error_code"], "pipeline_error")
        self.assertEqual(rows["proj-2"]["error_public"], "the run failed before completion; reference abc123def456")
        tasks = self.client.get("/api/tasks").json()["tasks"]
        self.assertTrue(tasks and all("path" not in task for task in tasks))
        health = self.client.get("/api/health").json()
        for dropped in ("data_dir", "reconciled_at_startup", "deduplicated_at_startup"):
            self.assertNotIn(dropped, health)
        self.assertEqual(health["startup"], {"reconciled": 0, "deduplicated": 0})
        self.assertIn("UTC day", health["budget"]["policy"])
        events = self.client.get("/api/runs/proj-2/events").json()
        self.assertNotIn("error", events)
        self.assertEqual(events["error_code"], "pipeline_error")
        self.assertIn("position", events)

    def test_console_page_still_renders_from_the_public_fields(self):
        html = self.client.get("/").text
        self.assertIn('id="main"', html)
        self.assertIn("visible to the team only", html)
        self.assertNotIn("Everything on this console is public", html)
        js = (ROOT / "attest/app/static/app.js").read_text(encoding="utf-8")
        self.assertIn("run.has_artifacts", js)
        self.assertIn("error_public", js)
        self.assertNotIn("run.out_dir", js)
        self.assertNotIn("run.error ", js)
        detail = self.client.get("/api/runs/proj-1").json()
        self.assertEqual(detail["run"]["status"], "finished")
        self.assertTrue(detail["bundle"])
        self.assertEqual(len(detail["events"]), 1)
        self.assertEqual(detail["exhibits"]["decision"]["verdict"], "VERIFIED")


# ---------------------------------------------------------------------------------------- API-05 and the artifact publication boundary
class ZipExportAndContainment(ConsoleHarness):
    def _run(self, run_id: str) -> Path:
        out = self.run_dir(run_id)
        if not self.store.has_run(run_id):
            self.store.create_run(run_id=run_id, **_row(finished_at=utcnow(), out_dir=str(out)))
        return out

    def test_manifested_large_artifact_is_included_and_verifies_or_is_refused_explicitly(self):
        out = self._run("zip-large")
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("zip-large")), encoding="utf-8")
        (out / "verify_raw.json").write_bytes(b" " * 5_000_000)
        manifest = build_manifest(out, "zip-large")
        (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.assertTrue(verify_manifest(out, manifest)["ok"])
        response = self.client.get("/api/runs/zip-large/bundle.zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/zip")
        self.assertEqual(int(response.headers["content-length"]), len(response.content))
        extracted = self.tmp / "extracted-large"
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            self.assertIn("zip-large/verify_raw.json", archive.namelist())
            archive.extractall(extracted)  # entries originate exclusively from this test's own directory
        downloaded = verify_manifest(extracted / "zip-large", manifest)
        self.assertEqual(downloaded["missing"], [])
        self.assertEqual(downloaded["mismatched"], [])
        self.assertTrue(downloaded["ok"], downloaded)
        with patch.object(self.server, "ZIP_MAX_FILE_BYTES", 1_000_000):
            refused = self.client.get("/api/runs/zip-large/bundle.zip")
        self.assertEqual(refused.status_code, 413)
        self.assertEqual(refused.json()["error"], "export_too_large")
        self.assertEqual(refused.json()["limit_bytes"], 1_000_000)
        self.assertIn("1000000", refused.json()["detail"])
        with patch.object(self.server, "ZIP_MAX_TOTAL_BYTES", 4_000_000):
            refused = self.client.get("/api/runs/zip-large/bundle.zip")
        self.assertEqual(refused.status_code, 413)
        self.assertEqual(refused.json()["limit_bytes"], 4_000_000)

    def test_zip_never_silently_omits_a_manifested_file(self):
        out = self._run("zip-mismatch")
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("zip-mismatch")), encoding="utf-8")
        (out / "verify.json").write_text("{}", encoding="utf-8")
        manifest = build_manifest(out, "zip-mismatch")
        (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (out / "verify.json").unlink()  # the directory no longer matches its manifest
        response = self.client.get("/api/runs/zip-mismatch/bundle.zip")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "manifest_mismatch")
        self.assertIn("verify.json", response.json()["detail"])

    def test_symlinks_and_non_allowlisted_files_are_unavailable_through_both_routes(self):
        out = self._run("zip-contain")
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("zip-contain")), encoding="utf-8")
        (out / "candidate.patch").write_text("SYNTHETIC_PATCH\n", encoding="utf-8")
        (out / "private-notes.env").write_text("SYNTHETIC_UNPUBLISHED_NOTE=offline-marker\n", encoding="utf-8")
        outside = self.tmp / "outside-sentinel.txt"
        outside.write_text("SYNTHETIC_OUTSIDE_RUN\n", encoding="utf-8")
        (out / "ledger.json").symlink_to(outside)
        outside_dir = self.tmp / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "test_sealed.py").write_text("SYNTHETIC_OUTSIDE_DIR\n", encoding="utf-8")
        (out / "sealed").symlink_to(outside_dir, target_is_directory=True)
        base = "/api/runs/zip-contain/artifacts/"
        self.assertEqual(self.client.get(base + "private-notes.env").status_code, 404)
        self.assertEqual(self.client.get(base + "ledger.json").status_code, 404)
        self.assertEqual(self.client.get(base + "sealed/test_sealed.py").status_code, 404)
        self.assertEqual(self.client.get(base + "candidate.patch").text, "SYNTHETIC_PATCH\n")
        zipped = self.client.get("/api/runs/zip-contain/bundle.zip")
        self.assertEqual(zipped.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
            self.assertEqual(set(archive.namelist()), {"zip-contain/proof_bundle.json", "zip-contain/candidate.patch"})
        for sentinel in (b"SYNTHETIC_OUTSIDE_RUN", b"SYNTHETIC_UNPUBLISHED_NOTE", b"SYNTHETIC_OUTSIDE_DIR"):
            self.assertNotIn(sentinel, zipped.content)
        # a manifest that lists the link is an explicit error, never the outside bytes
        manifest = build_manifest(out, "zip-contain")
        manifest["files"].append({"path": "ledger.json", "bytes": 22, "sha256": "0" * 64, "purpose": "x"})
        (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        listed = self.client.get("/api/runs/zip-contain/bundle.zip")
        self.assertEqual(listed.status_code, 409)
        self.assertEqual(listed.json()["error"], "manifest_mismatch")
        self.assertNotIn(b"SYNTHETIC_OUTSIDE_RUN", listed.content)

    def test_a_symlinked_run_directory_is_not_served(self):
        real = self.tmp / "elsewhere" / "real-run"
        real.mkdir(parents=True)
        (real / "proof_bundle.json").write_text(json.dumps(_bundle("zip-linkroot")), encoding="utf-8")
        link = self.tmp / "data" / "runs" / "zip-linkroot"
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(real, target_is_directory=True)
        self.store.create_run(run_id="zip-linkroot", **_row(finished_at=utcnow(), out_dir=str(link)))
        self.assertEqual(self.client.get("/api/runs/zip-linkroot/artifacts/proof_bundle.json").status_code, 404)
        self.assertEqual(self.client.get("/api/runs/zip-linkroot/bundle.zip").status_code, 404)

    def test_traversal_shaped_names_stay_closed(self):
        out = self._run("zip-names")
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("zip-names")), encoding="utf-8")
        # literal dot segments are normalised away by the HTTP client before the server sees them; the encoded forms reach the route
        for rel in ("../proof_bundle.json", "%2Fetc%2Fpasswd", "sealed%2F..%2Fproof_bundle.json", "mutants_..%2F..%2Fetc.py", "sealed/%2E%2E/proof_bundle.json"):
            self.assertEqual(self.client.get(f"/api/runs/zip-names/artifacts/{rel}").status_code, 404, rel)
        self.assertIsNone(self.server.contained_file(out, "../proof_bundle.json"))
        self.assertIsNone(self.server.contained_file(out, "/proof_bundle.json"))
        self.assertIsNone(self.server.contained_file(out, "a/../proof_bundle.json"))
        self.assertIsNotNone(self.server.contained_file(out, "proof_bundle.json"))


# ---------------------------------------------------------------------------------------------------------------- API-06
class ErrorRetention(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-audit-retention-"))
        self.store = Store(self.tmp / "attest.db")
        self.runs = self.tmp / "runs"
        self.runs.mkdir()

    def tearDown(self):
        self.store._conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _dir(self, name: str, status: str, created: str, verdict: str | None = None, outside: bool = False) -> Path:
        out = (self.tmp / "elsewhere" if outside else self.runs) / name
        out.mkdir(parents=True)
        (out / "trajectory.jsonl").write_text("synthetic partial output\n", encoding="utf-8")
        self.store.create_run(run_id=name, **_row(status=status, verdict=verdict, created_at=created, out_dir=str(out)))
        return out

    def test_old_error_directories_beyond_the_budget_are_reclaimed_and_protected_items_remain(self):
        errors = [self._dir(f"err-{i:02d}", "error", f"2026-10-01T00:00:{i:02d}") for i in range(12)]
        running = self._dir("running-1", "running", "2026-09-01T00:00:00")
        queued = self._dir("queued-1", "queued", "2026-09-01T00:00:01")
        verified = self._dir("verified-old", "finished", "2026-09-01T00:00:02", verdict="VERIFIED")
        finished = [self._dir(f"fin-{i}", "finished", f"2026-10-02T00:00:0{i}", verdict="NEEDS HUMAN") for i in range(3)]
        outside = self._dir("imported-error", "error", "2026-01-01T00:00:00", outside=True)
        pruned = self.store.prune_runs(self.runs, keep=2, keep_errors=10)
        self.assertEqual(sorted(pruned), ["err-00", "err-01", "fin-0"])  # the two oldest errors beyond ten, the oldest finished beyond two
        for kept in errors[2:] + finished[1:] + [running, queued, verified, outside]:
            self.assertTrue(kept.is_dir(), kept)
        for gone in errors[:2] + [finished[0]]:
            self.assertFalse(gone.exists(), gone)
        row = self.store.get_run("err-00")
        self.assertEqual((row["status"], row["stage"], row["out_dir"]), ("error", "pruned", None))  # the row and its accounting stay
        self.assertEqual(self.store.prune_runs(self.runs, keep=2, keep_errors=10), [])  # idempotent

    def test_the_run_root_itself_is_never_removed(self):
        self.store.create_run(run_id="root-row", **_row(status="error", verdict=None, created_at="2026-01-01T00:00:00", out_dir=str(self.runs)))
        self.assertEqual(self.store.prune_runs(self.runs, keep=0, keep_errors=0), [])
        self.assertTrue(self.runs.is_dir())

    def test_the_failure_path_and_idle_housekeeping_prune_without_a_successful_run(self):
        old = [self._dir(f"old-err-{i}", "error", f"2026-10-01T00:00:0{i}") for i in range(3)]
        with patch.object(Worker, "_loop", idle_loop):
            worker = Worker(self.store, self.tmp, self.tmp / "examples", retention_keep_errors=1)
            try:
                self.store.create_run(run_id="fails", **_row(status="queued", verdict=None, created_at=utcnow()))
                item = ("fails", Path("unused"), "nebius", "judge-demo")
                worker.queue.put_nowait(item)
                worker.queue.get_nowait()
                with patch.object(worker, "_execute", side_effect=RuntimeError("synthetic failure")), self.assertLogs("attest.app", level="ERROR"):
                    worker._run_one(item)
                self.assertEqual(self.store.get_run("fails")["status"], "error")
                self.assertTrue(old[2].is_dir(), "the newest error directory is within the budget of one")
                self.assertFalse(old[0].exists() or old[1].exists(), "older error directories were reclaimed on the failure path")
            finally:
                worker.stop()
                worker.thread.join(timeout=5)
        # the idle timer prunes as well: no run has to finish for retention to happen
        fresh = [self._dir(f"idle-err-{i}", "error", f"2026-10-03T00:00:0{i}") for i in range(3)]
        worker = Worker(self.store, self.tmp, self.tmp / "examples", retention_keep_errors=0, housekeeping_s=0.05)
        try:
            deadline = dt.datetime.now() + dt.timedelta(seconds=5)
            while dt.datetime.now() < deadline and any(d.exists() for d in fresh):
                threading.Event().wait(0.05)
            self.assertFalse(any(d.exists() for d in fresh), "idle housekeeping reclaimed the error directories")
        finally:
            worker.stop()
            worker.thread.join(timeout=5)


# ---------------------------------------------------------------------------------------------------------------- API-07
class WorkerReadiness(ConsoleHarness):
    LOOP = staticmethod(dead_loop)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.worker.thread.join(timeout=5)
        cls.worker.stop()  # a stopped worker: no restart until start()

    def test_admission_requires_a_live_worker_and_resumes_after_recovery(self):
        health = self.client.get("/api/health").json()
        self.assertFalse(health["worker_alive"])
        self.assertFalse(health["ready"])
        public = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
        team = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex", "admin_token": TOKEN})
        self.assertEqual((public.status_code, team.status_code), (503, 503))
        self.assertIn("worker", public.json()["detail"])
        self.assertEqual(self.store.list_runs(include_team=True), [], "nothing was created")
        self.assertEqual(self.store.active_count(), 0)
        self.assertEqual(self.worker.queue.qsize(), 0)
        self.assertEqual(self.store.nebius_remaining(0.5, 100.0, "2000-01-01")["active_runs"], 0, "no reservation was taken")
        with patch.object(Worker, "_loop", idle_loop):  # recovery: the loop comes back
            self.assertTrue(self.worker.start())
            health = self.client.get("/api/health").json()
            self.assertTrue(health["worker_alive"])
            self.assertTrue(health["ready"])
            admitted = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
            self.assertEqual(admitted.status_code, 200)
            self.assertEqual(self.store.get_run(admitted.json()["run_id"])["status"], "queued")
            self.worker.stop()


class WorkerSupervision(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-audit-worker-"))
        self.store = Store(self.tmp / "attest.db")

    def tearDown(self):
        self.store._conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ensure_alive_restarts_a_thread_that_died_unexpectedly(self):
        starts = []

        def dying_then_idle(self):
            starts.append(1)
            if len(starts) == 1:
                return  # dies at once the first time
            self._stop.wait()

        with patch.object(Worker, "_loop", dying_then_idle):
            worker = Worker(self.store, self.tmp, self.tmp / "examples")
            worker.thread.join(timeout=5)
            self.assertFalse(worker.alive())
            with self.assertLogs("attest.app", level="ERROR"):
                self.assertTrue(worker.ensure_alive())
            self.assertEqual(worker.restarts, 1)
            self.assertTrue(worker.alive())
            self.assertTrue(worker.ensure_alive())  # already alive: no second restart
            self.assertEqual(worker.restarts, 1)
            worker.stop()
            worker.thread.join(timeout=5)
            self.assertFalse(worker.ensure_alive(), "a deliberate stop is respected")

    def _worker_with_item(self, run_id: str, provider: str = "nebius"):
        worker = Worker(self.store, self.tmp, self.tmp / "examples")
        self.store.create_run(run_id=run_id, **_row(provider=provider, status="queued", verdict=None, created_at=utcnow()))
        item = (run_id, Path("unused"), provider, "judge-demo")
        worker.queue.put_nowait(item)
        worker.queue.get_nowait()
        return worker, item

    def test_the_loop_survives_any_exception_and_records_the_failure(self):
        class Boom(BaseException):
            pass

        with patch.object(Worker, "_loop", idle_loop):
            worker, item = self._worker_with_item("boom-1")
            try:
                with patch.object(worker, "_execute", side_effect=Boom(f"{MARKER} at {MARKER_PATH}")), self.assertLogs("attest.app", level="ERROR"):
                    worker._run_one(item)  # no exception escapes
                row = self.store.get_run("boom-1")
                self.assertEqual((row["status"], row["error_code"], row["error"]), ("error", "worker_error", "the worker failed before completion"))
                self.assertIn("Boom", row["error_detail"])
                self.assertIn(MARKER, row["error_detail"])
                self.assertEqual(len(row["error_ref"]), 12)
                self.assertIsNone(worker.current)
                self.assertEqual(worker.queue.unfinished_tasks, 0)
            finally:
                worker.stop()

    def test_a_dying_thread_settles_the_running_row_before_it_goes(self):
        with patch.object(Worker, "_loop", idle_loop):
            worker, item = self._worker_with_item("exit-1")
            try:
                with patch.object(worker, "_execute", side_effect=SystemExit(137)), self.assertLogs("attest.app", level="ERROR"):
                    with self.assertRaises(SystemExit):
                        worker._run_one(item)
                row = self.store.get_run("exit-1")
                self.assertEqual((row["status"], row["error_code"], row["stage"]), ("error", "worker_interrupted", "interrupted"))
                self.assertEqual(row["cost_committed_usd"], 0.5, "no journal: the per-run cap bounds the unknown spend")
                self.assertIn("SystemExit", row["error_detail"])
                self.assertIsNone(worker.current)
            finally:
                worker.stop()

    def test_a_row_that_execute_already_finalized_is_left_alone(self):
        with patch.object(Worker, "_loop", idle_loop):
            worker, item = self._worker_with_item("done-1")
            try:
                def finish_then_raise(run_id, path, provider, profile):
                    self.store.update_run(run_id, status="finished", verdict="VERIFIED", finished_at=utcnow())
                    raise RuntimeError("after the fact")
                with patch.object(worker, "_execute", finish_then_raise):
                    worker._run_one(item)
                self.assertEqual(self.store.get_run("done-1")["status"], "finished")
            finally:
                worker.stop()


# ---------------------------------------------------------------------------------------------------------------- API-08
class BundleIncomplete(ConsoleHarness):
    def test_a_partial_bundle_is_a_retryable_503_not_a_500(self):
        out = self.run_dir("partial-1")
        (out / "proof_bundle.json").write_text('{"run_id":', encoding="utf-8")
        self.store.create_run(run_id="partial-1", **_row(finished_at=utcnow(), out_dir=str(out)))
        response = self.client.get("/api/runs/partial-1")
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual((body["error"], body["retry_after_s"]), ("bundle_incomplete", 2))
        self.assertEqual(response.headers["retry-after"], "2")
        self.assertNotIn("JSONDecodeError", response.text)
        (out / "proof_bundle.json").write_text("[]", encoding="utf-8")  # valid JSON, not a bundle
        self.assertEqual(self.client.get("/api/runs/partial-1").status_code, 503)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("partial-1")), encoding="utf-8")
        complete = self.client.get("/api/runs/partial-1")
        self.assertEqual(complete.status_code, 200)
        self.assertEqual(complete.json()["run"]["verdict"], "VERIFIED")


@unittest.skipUnless(NODE, "node is not installed")
class ConsoleClient(unittest.TestCase):
    """API-08 (client), API-10 and API-11 (client): the functions are extracted from app.js and run in a fake context."""

    def test_app_js_parses(self):
        result = subprocess.run([NODE, "--check", str(ROOT / "attest/app/static/app.js")], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_client_functions_behave_as_repaired(self):
        result = subprocess.run([NODE, str(ROOT / "tests/console_client_test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertTrue(report["ok"])
        self.assertEqual(set(report["checks"]), {"copy_patch_requires_ok", "queue_position_is_authoritative", "terminal_detail_retried",
                                                 "download_urls_carry_tickets_never_the_token"})

    def test_client_sends_the_token_in_the_header_only_and_tickets_on_team_download_links(self):
        js = (ROOT / "attest/app/static/app.js").read_text(encoding="utf-8")
        self.assertIn('"X-Attest-Token": state.token', js)
        self.assertNotIn("?token=", js)  # R5-07: the team token never enters a URL
        self.assertNotIn("token=${", js)
        self.assertNotIn("tokenQuery", js)
        self.assertIn("?ticket=${encodeURIComponent(state.ticket.value)}", js)
        self.assertIn("/download-ticket`, { method: \"POST\" }", js)
        self.assertIn("fetch(patchUrl, { headers: authHeaders() })", js)  # Copy patch: header, no credential in the URL
        self.assertNotIn("data-patch-url", js)
        self.assertNotIn("localStorage.setItem(\"attest.token", js)
        self.assertNotIn("sessionStorage.setItem(\"attest.token", js)
        self.assertNotIn("Storage.setItem(\"attest.ticket", js)


# ---------------------------------------------------------------------------------------------------------------- API-09
class SanitizedErrors(ConsoleHarness):
    def test_unhandled_exception_returns_a_correlation_id_and_logs_the_traceback(self):
        with patch.object(self.store, "list_runs", side_effect=RuntimeError(f"SYNTHETIC_BACKEND_DETAIL {MARKER_PATH}")), \
             self.assertLogs("attest.app", level="ERROR") as logs:
            response = self.client.get("/api/runs")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(set(body), {"error", "correlation_id"})
        self.assertEqual(body["error"], "internal_error")
        self.assertRegex(body["correlation_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(response.headers["x-correlation-id"], body["correlation_id"])
        self.assertNotIn("SYNTHETIC_BACKEND_DETAIL", response.text)
        self.assertNotIn(MARKER_PATH, response.text)
        joined = "\n".join(logs.output)
        self.assertIn(body["correlation_id"], joined)
        self.assertIn("SYNTHETIC_BACKEND_DETAIL", joined)
        self.assertIn("Traceback", joined)

    def test_worker_failure_detail_stays_server_side(self):
        self.store.create_run(run_id="fail-1", **_row(status="queued", verdict=None, stage="queued", created_at=utcnow()))
        item = ("fail-1", Path("unused"), "nebius", "judge-demo")
        self.worker.queue.put_nowait(item)
        self.worker.queue.get_nowait()
        with patch.object(self.worker, "_execute", side_effect=RuntimeError(f"{MARKER} at {MARKER_PATH}")), self.assertLogs("attest.app", level="ERROR") as logs:
            self.worker._run_one(item)
        row = self.store.get_run("fail-1")
        self.assertEqual((row["status"], row["error_code"]), ("error", "worker_error"))
        self.assertIn(MARKER, row["error_detail"])
        self.assertIn("Traceback", row["error_detail"])
        self.assertIn(row["error_ref"], "\n".join(logs.output))
        for path in ("/api/runs", "/api/runs/fail-1", "/api/runs/fail-1/events"):
            text = self.client.get(path).text
            for forbidden in (MARKER, MARKER_PATH, "Traceback", '"error_detail"', '"error_ref"'):
                self.assertNotIn(forbidden, text, path)
        public = self.client.get("/api/runs/fail-1").json()["run"]
        self.assertEqual(public["error_code"], "worker_error")
        self.assertEqual(public["error_public"], f"the run failed before completion; reference {row['error_ref']}")
        self.assertEqual(set(public) & {"error", "error_detail", "error_ref", "requester", "out_dir"}, set())

    def test_legacy_imported_and_replayed_error_rows_are_projected_too(self):
        self.store.create_run(run_id="legacy-1", **_row(status="error", verdict=None, requester="import", error=f"RuntimeError: {MARKER} {MARKER_PATH}"))
        self.store.create_run(run_id="replay-1", **_row(status="error", verdict=None, requester="replay", profile_label="replay-fixture", error=MARKER))
        for run_id, provenance in (("legacy-1", "imported"), ("replay-1", "synthetic")):
            public = self.client.get(f"/api/runs/{run_id}").json()["run"]
            self.assertEqual(public["error_code"], "run_failed")
            self.assertEqual(public["error_public"], f"the run failed before completion; reference {run_id}")
            self.assertEqual(public["provenance"], provenance)
        self.assertNotIn(MARKER, self.client.get("/api/runs").text)


# ---------------------------------------------------------------------------------------------------------------- API-11
class QueuePosition(ConsoleHarness):
    def test_position_counts_only_the_runs_ahead(self):
        ids = []
        for _ in range(3):
            response = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius", "admin_token": TOKEN})
            self.assertEqual(response.status_code, 200, response.text)
            ids.append(response.json()["run_id"])
        a, b, c = ids
        position = lambda run_id: self.client.get(f"/api/runs/{run_id}/events").json()["position"]  # noqa: E731
        self.assertEqual([position(i) for i in ids], [0, 1, 2], "nothing executing yet: A starts next")
        item = self.worker.queue.get_nowait()  # the worker takes A
        self.assertEqual(item[0], a)
        self.worker._begin(a)
        self.store.update_run(a, status="running", started_at=utcnow())
        self.assertEqual([position(i) for i in ids], [0, 1, 2])
        d = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius", "admin_token": TOKEN}).json()
        self.assertEqual(d["position"], 3)
        self.assertEqual([position(i) for i in ids + [d["run_id"]]], [0, 1, 2, 3], "appending D changes nothing ahead of it")
        events = self.client.get(f"/api/runs/{b}/events").json()
        self.assertEqual((events["current"], events["queue"], events["busy"]), (a, 3, True))
        self.assertEqual(self.client.get("/api/runs").json()["current"], a)
        self.store.create_run(run_id="finished-elsewhere", **_row())
        self.assertIsNone(position("finished-elsewhere"), "a run that is neither executing nor queued has no position")
        self.assertEqual(self.client.get("/api/runs/unknown/events").status_code, 404)


# ------------------------------------------------------------------------------------------------------------------ AC-05
class ImportedCommittedCost(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-audit-import-"))
        self.store = Store(self.tmp / "attest.db")

    def tearDown(self):
        self.store._conn.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _bundle_dir(self, name: str, **kwargs) -> Path:
        out = self.tmp / "runs" / name
        out.mkdir(parents=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle(name, **kwargs)), encoding="utf-8")
        return out

    def test_import_preserves_the_committed_cost_and_the_daily_cap_binds(self):
        today = today_start()
        out = self._bundle_dir("imp-1", verdict="ERROR", totals={"cost_usd": None, "cost_usd_committed": 0.5})
        self.assertTrue(self.store.import_run_dir(out))
        row = self.store.get_run("imp-1")
        self.assertIsNone(row["cost_usd"])
        self.assertEqual(row["cost_committed_usd"], 0.5)
        self.assertEqual(row["visibility"], PUBLIC)
        remaining = self.store.nebius_remaining(0.5, 0.5, today)
        self.assertAlmostEqual(remaining["committed_usd"], 0.5)
        self.assertAlmostEqual(remaining["remaining_usd"], 0.0)
        self.assertFalse(remaining["fits_another_run"])
        with self.assertRaises(BudgetError):
            self.store.create_run_reserving(0.5, 0.5, today, run_id="next", **_row(status="queued", verdict=None))
        self.assertFalse(self.store.import_run_dir(out), "a second import is a no-op")
        self.assertEqual(len(self.store.list_runs()), 1)
        fresh = Store(self.tmp / "rebuilt.db")  # rebuilding a database from the run directories reproduces the figure
        self.assertTrue(fresh.import_run_dir(out))
        self.assertEqual(fresh.get_run("imp-1")["cost_committed_usd"], 0.5)
        self.assertEqual(fresh.dedupe_imports(), [])
        self.assertEqual(fresh.get_run("imp-1")["cost_committed_usd"], 0.5)
        fresh._conn.close()

    def test_legacy_bundles_recompute_the_figure_from_call_records_or_the_journal(self):
        ledger = {"totals": {"cost_usd": 0.02}, "model_calls": [{"cost_usd": 0.02, "reserved_usd": 0.04}, {"cost_usd": None, "reserved_usd": 0.05}],
                  "open_reservations": [{"reserved_usd": 0.06}]}
        self.assertTrue(self.store.import_run_dir(self._bundle_dir("legacy-calls", ledger=ledger)))
        self.assertAlmostEqual(self.store.get_run("legacy-calls")["cost_committed_usd"], 0.13)  # known cost, reservation of the uncertain call, open reservation
        out = self._bundle_dir("legacy-journal", ledger={"totals": {"cost_usd": 0.03}})  # no call records: the journal in the directory is the fallback
        journal = Ledger()
        journal.attach_sink(out / JOURNAL_FILE)
        rid = journal.reserve("nebius_tokenfactory", "spec", "spec", "m", 0.04)
        journal.add_call(paid_call(0.03, 0.04), rid)
        journal.reserve("nebius_tokenfactory", "seal", "seal-1", "m", 0.05)  # in flight when the process died
        self.assertTrue(self.store.import_run_dir(out))
        self.assertAlmostEqual(self.store.get_run("legacy-journal")["cost_committed_usd"], 0.08)
        self.assertTrue(self.store.import_run_dir(self._bundle_dir("legacy-none", ledger={"totals": {"cost_usd": 0.03}})))
        self.assertIsNone(self.store.get_run("legacy-none")["cost_committed_usd"])  # nothing to recompute from: the known cost stands
        self.assertAlmostEqual(self.store._nebius_committed("2000-01-01"), 0.13 + 0.08 + 0.03)
        self.assertEqual(db_module.committed_from_ledger({"model_calls": []}, None), 0.0)
        self.assertIsNone(db_module.committed_from_ledger({"totals": {}}, None))
        self.assertEqual(db_module.committed_from_ledger({"model_calls": [{"cost_usd": None}]}, 0.02), 0.02)  # never below the known cost

    def test_dedupe_carries_the_committed_cost_to_the_kept_row(self):
        out = self._bundle_dir("dup", totals={"cost_usd": 0.02, "cost_usd_committed": 0.5})
        self.store.create_run(run_id="dup-console", **_row(created_at="2026-10-19T10:00:00", out_dir=str(out), requester="1.2.3.4"))
        self.store.create_run(run_id="dup", **_row(created_at="2026-10-19T10:00:00+00:00", out_dir=str(out), requester="import", cost_usd=0.02, cost_committed_usd=0.5))
        removed = self.store.dedupe_imports()
        self.assertEqual([r["run_id"] for r in removed], ["dup"])
        kept = self.store.get_run("dup-console")
        self.assertEqual((kept["cost_committed_usd"], kept["cost_usd"]), (0.5, 0.02))
        self.assertAlmostEqual(self.store._nebius_committed("2000-01-01"), 0.5)


class ImportedBudgetAtStartup(ConsoleHarness):
    ENV = {"ATTEST_DAILY_USD_CAP": "0.5"}

    @classmethod
    def extra_env(cls, tmp: Path) -> dict:
        out = tmp / "imports" / "imp-startup"
        out.mkdir(parents=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("imp-startup", verdict="ERROR", totals={"cost_usd": None, "cost_usd_committed": 0.5})), encoding="utf-8")
        return {"ATTEST_IMPORT_DIRS": str(tmp / "imports")}

    def test_the_imported_committed_cost_counts_against_today_and_refuses_another_run(self):
        health = self.client.get("/api/health").json()
        self.assertAlmostEqual(health["budget"]["committed_today_usd"], 0.5)
        self.assertAlmostEqual(health["budget"]["remaining_usd"], 0.0)
        rows = self.client.get("/api/runs").json()["runs"]
        self.assertEqual([(r["run_id"], r["cost_committed_usd"], r["provenance"]) for r in rows], [("imp-startup", 0.5, "imported")])
        refused = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
        self.assertEqual(refused.status_code, 503)
        self.assertIn("daily Nebius budget", refused.json()["detail"])
        self.assertEqual(self.store.active_count(), 0)


# ------------------------------------------------------------------------------------------------------------------ AC-06
class DayBoundaryAccounting(unittest.TestCase):
    def test_a_run_straddling_midnight_counts_against_the_new_day_before_and_after_it_finishes(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-audit-day-"))
        try:
            store = Store(tmp / "attest.db")
            store.create_run(run_id="late", **_row(status="queued", verdict=None, stage="queued", created_at="2026-10-18T23:59:59+00:00"))
            new_day = "2026-10-19T00:00:00"
            self.assertAlmostEqual(store.nebius_remaining(0.5, 0.5, new_day)["remaining_usd"], 0.0)  # queued: reserved on any day
            store.update_run("late", status="running", started_at="2026-10-19T00:01:00+00:00", stage="implement")
            self.assertAlmostEqual(store.nebius_remaining(0.5, 0.5, new_day)["remaining_usd"], 0.0)  # running: still reserved
            store.update_run("late", status="finished", verdict="VERIFIED", finished_at="2026-10-19T00:05:00+00:00", cost_usd=0.5, cost_committed_usd=0.5)
            after = store.nebius_remaining(0.5, 0.5, new_day)
            self.assertAlmostEqual(after["committed_usd"], 0.5)
            self.assertAlmostEqual(after["remaining_usd"], 0.0)  # finished: the spend stays on the day it happened
            self.assertFalse(after["fits_another_run"])
            self.assertIn("UTC day", after["policy"])
            ok, detail = store.nebius_budget_ok(0.5, 0.5, new_day, executing=False)
            self.assertTrue(ok)
            self.assertIn("0.5000 committed", detail)
            with self.assertRaises(BudgetError):
                store.create_run_reserving(0.5, 0.5, new_day, run_id="next", **_row(status="queued", verdict=None))
            self.assertAlmostEqual(store.nebius_remaining(0.5, 0.5, "2026-10-18T00:00:00")["committed_usd"], 0.5)  # and against the day it was queued
            self.assertAlmostEqual(store.nebius_remaining(0.5, 0.5, "2026-10-20T00:00:00")["committed_usd"], 0.0)  # but not against a day it never touched
            # a run whose calls straddle midnight (started before, finished after) is charged to both days as well
            store.create_run(run_id="straddle", **_row(created_at="2026-10-19T23:50:00+00:00", started_at="2026-10-19T23:55:00+00:00",
                                                        finished_at="2026-10-20T00:10:00+00:00", cost_usd=0.2, cost_committed_usd=0.2))
            self.assertAlmostEqual(store.nebius_remaining(0.5, 2.0, "2026-10-20T00:00:00")["committed_usd"], 0.2)
            self.assertAlmostEqual(store.nebius_remaining(0.5, 2.0, new_day)["committed_usd"], 0.7)
            self.assertIn("UTC day", Store.__doc__)
            self.assertIn("UTC day", db_module.BUDGET_POLICY)
            store._conn.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------------------------------- publication contract for team runs
class TeamVisibility(ConsoleHarness):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        created = cls.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex", "admin_token": TOKEN})
        assert created.status_code == 200, created.text
        assert created.json()["visibility"] == TEAM
        cls.team_id = created.json()["run_id"]
        out = cls.tmp / "data" / "runs" / cls.team_id
        out.mkdir(parents=True)
        bundle = _bundle(cls.team_id, provider="codex_gateway", verdict="VERIFIED")
        bundle["profile"]["label"] = "development"
        bundle["verdict"]["reasons"] = ["SYNTHETIC_TEAM_REASON"]
        (out / "proof_bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
        (out / "candidate.patch").write_text("SYNTHETIC_TEAM_PATCH\n", encoding="utf-8")
        cls.worker.queue.get_nowait()  # the worker takes the team run and it completes
        cls.worker._begin(cls.team_id)
        cls.store.update_run(cls.team_id, out_dir=str(out), status="finished", verdict="VERIFIED", stage="finished", finished_at=utcnow())
        cls.store.add_event(cls.team_id, utcnow(), "pacing", "SYNTHETIC_TEAM_EVENT")
        public = cls.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius", "admin_token": TOKEN})
        assert public.status_code == 200, public.text
        cls.public_id = public.json()["run_id"]

    def test_anonymous_reads_never_see_the_team_run(self):
        listing = self.client.get("/api/runs")
        self.assertEqual(listing.status_code, 200)
        ids = [r["run_id"] for r in listing.json()["runs"]]
        self.assertNotIn(self.team_id, ids)
        self.assertIn(self.public_id, ids)
        self.assertIsNone(listing.json()["current"], "the executing team run is not referenced")
        self.assertTrue(listing.json()["busy"])
        for path in (f"/api/runs/{self.team_id}", f"/api/runs/{self.team_id}/events", f"/api/runs/{self.team_id}/artifacts/candidate.patch",
                     f"/api/runs/{self.team_id}/bundle.zip", f"/api/runs/{self.team_id}/artifacts/proof_bundle.json"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("SYNTHETIC_TEAM", response.text)
            self.assertNotIn("codex", response.text.lower())
        for path in ("/api/runs", "/api/health", "/api/tasks", "/api/profiles", "/api/openapi.json", f"/api/runs/{self.public_id}", f"/api/runs/{self.public_id}/events"):
            text = self.client.get(path).text.lower()
            self.assertNotIn("codex", text, path)
            self.assertNotIn("gateway", text, path)
            self.assertNotIn(self.team_id, text, path)
            self.assertNotIn("synthetic_team", text, path)
        health = self.client.get("/api/health").json()
        self.assertIsNone(health["current"])
        self.assertTrue(health["busy"])
        self.assertFalse(health["team"])
        estimate = self.client.get("/api/tasks").json()["tasks"][0]["estimate"]
        self.assertNotEqual(estimate["latest_run_id"], self.team_id)
        self.assertEqual(estimate["recorded_runs"], 0)
        wrong = {"X-Attest-Token": "not-the-token"}
        self.assertEqual(self.client.get(f"/api/runs/{self.team_id}", headers=wrong).status_code, 404)
        self.assertEqual(self.client.get(f"/api/runs/{self.team_id}/bundle.zip?token=not-the-token").status_code, 404)

    def test_the_team_token_reveals_the_team_run_on_every_route(self):
        listing = self.client.get("/api/runs", headers=TEAM_HEADERS).json()
        self.assertIn(self.team_id, [r["run_id"] for r in listing["runs"]])
        self.assertEqual(listing["current"], self.team_id)
        detail = self.client.get(f"/api/runs/{self.team_id}", headers=TEAM_HEADERS)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["run"]["visibility"], TEAM)
        self.assertIn("SYNTHETIC_TEAM_REASON", detail.text)
        self.assertIn("SYNTHETIC_TEAM_EVENT", self.client.get(f"/api/runs/{self.team_id}/events", headers=TEAM_HEADERS).text)
        self.assertEqual(self.client.get(f"/api/runs/{self.team_id}/artifacts/candidate.patch", headers=TEAM_HEADERS).text, "SYNTHETIC_TEAM_PATCH\n")
        zipped = self.client.get(f"/api/runs/{self.team_id}/bundle.zip", headers=TEAM_HEADERS)
        self.assertEqual(zipped.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
            self.assertIn(f"{self.team_id}/candidate.patch", archive.namelist())
        health = self.client.get("/api/health", headers=TEAM_HEADERS).json()
        self.assertEqual(health["current"], self.team_id)
        self.assertTrue(health["team"])
        estimate = self.client.get("/api/tasks", headers=TEAM_HEADERS).json()["tasks"][0]["estimate"]
        self.assertEqual(estimate["latest_run_id"], self.team_id)
        self.assertEqual(estimate["recorded_runs"], 1)

    def test_a_query_token_is_ignored_on_every_route(self):
        """R5-07: `?token=` is read nowhere, so its bearer is an anonymous caller on reads and on admission alike. The review's
        reproduction (reports/attest-revision5-review-2026-10-19/api-review-repro.py) asserts the old, faulty behaviour."""
        query = f"?token={TOKEN}"
        anonymous = self.client.get("/api/runs").json()
        with_query = self.client.get("/api/runs" + query).json()
        self.assertEqual([r["run_id"] for r in with_query["runs"]], [r["run_id"] for r in anonymous["runs"]])
        self.assertNotIn(self.team_id, [r["run_id"] for r in with_query["runs"]])
        self.assertIsNone(with_query["current"], "the executing team run is not referenced")
        for path in (f"/api/runs/{self.team_id}", f"/api/runs/{self.team_id}/events", f"/api/runs/{self.team_id}/artifacts/candidate.patch",
                     f"/api/runs/{self.team_id}/bundle.zip", f"/api/runs/{self.team_id}/artifacts/proof_bundle.json"):
            response = self.client.get(path + query)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("SYNTHETIC_TEAM", response.text)
        health = self.client.get("/api/health" + query).json()
        self.assertFalse(health["team"])
        self.assertIsNone(health["current"])
        self.assertEqual(self.client.get("/api/tasks" + query).json()["tasks"][0]["estimate"]["recorded_runs"], 0)
        self.assertFalse(self.client.get("/api/profiles" + query).json()["team"])
        self.assertEqual(self.client.post(f"/api/runs/{self.team_id}/download-ticket" + query).status_code, 403)
        before = len(self.store.list_runs(include_team=True))
        self.assertEqual(self.client.post("/api/runs" + query, json={"task_id": "audit-sample", "provider": "codex"}).status_code, 403)
        self.assertEqual(len(self.store.list_runs(include_team=True)), before, "the refused request left no row")

    def test_a_download_ticket_opens_the_team_runs_downloads_and_nothing_else(self):
        """R5-07: the header token mints a ticket for the run; the ticket opens that run's artifact and zip routes and no other route."""
        self.assertEqual(self.client.post(f"/api/runs/{self.team_id}/download-ticket").status_code, 403, "minting needs the header token")
        minted = self.client.post(f"/api/runs/{self.team_id}/download-ticket", headers=TEAM_HEADERS)
        self.assertEqual(minted.status_code, 200, minted.text)
        ticket = minted.json()["ticket"]
        self.assertTrue(ticket.startswith(self.team_id + "."))
        self.assertNotIn(TOKEN, ticket)
        query = f"?ticket={ticket}"
        self.assertEqual(self.client.get(f"/api/runs/{self.team_id}/artifacts/candidate.patch{query}").text, "SYNTHETIC_TEAM_PATCH\n")
        zipped = self.client.get(f"/api/runs/{self.team_id}/bundle.zip{query}")
        self.assertEqual(zipped.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
            self.assertIn(f"{self.team_id}/candidate.patch", archive.namelist())
        for path in (f"/api/runs/{self.team_id}", f"/api/runs/{self.team_id}/events"):
            response = self.client.get(path + query)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("SYNTHETIC_TEAM", response.text)
        listing = self.client.get("/api/runs" + query).json()
        self.assertNotIn(self.team_id, [r["run_id"] for r in listing["runs"]])
        self.assertIsNone(listing["current"])
        self.assertFalse(self.client.get("/api/health" + query).json()["team"])
        self.assertEqual(self.client.post("/api/runs" + query, json={"task_id": "audit-sample", "provider": "codex"}).status_code, 403)
        self.assertEqual(self.client.get(f"/api/runs/{self.public_id}").status_code, 200, "public rows need neither token nor ticket")

    def test_imported_development_bundles_become_team_rows_and_old_rows_are_backfilled(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-audit-visibility-"))
        try:
            store = Store(tmp / "attest.db")
            for name, provider in (("dev-import", "codex_gateway"), ("judge-import", "nebius_tokenfactory")):
                out = tmp / "runs" / name
                out.mkdir(parents=True)
                (out / "proof_bundle.json").write_text(json.dumps(_bundle(name, provider=provider)), encoding="utf-8")
                self.assertTrue(store.import_run_dir(out))
            self.assertEqual(store.get_run("dev-import")["visibility"], TEAM)
            self.assertEqual(store.get_run("judge-import")["visibility"], PUBLIC)
            self.assertEqual([r["run_id"] for r in store.list_runs()], ["judge-import"])
            self.assertEqual(len(store.list_runs(include_team=True)), 2)
            store.create_run(run_id="dev-live", **_row(provider="codex", profile_label="development"))
            self.assertEqual(store.get_run("dev-live")["visibility"], TEAM)
            # a row recorded before the column existed: back-filled when the store opens
            store._write("INSERT INTO runs (run_id, task_id, task_title, provider, profile_label, status, created_at, visibility) "
                         "VALUES ('dev-old', 't', 'T', 'codex', 'development', 'finished', '2026-10-01T00:00:00', 'public')")
            store._conn.close()
            reopened = Store(tmp / "attest.db")
            self.assertEqual(reopened.get_run("dev-old")["visibility"], TEAM)
            self.assertEqual(reopened.task_estimates()["audit-sample"]["recorded_runs"], 1)  # judge-import only
            self.assertEqual(reopened.task_estimates(include_team=True)["audit-sample"]["recorded_runs"], 3)  # plus dev-import and dev-live
            reopened._conn.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------------------- R5-07: run-scoped download tickets
class DownloadTickets(ConsoleHarness):
    """R5-07: the team token is accepted in the X-Attest-Token header only, and a team run's downloads from a plain link use a
    short-lived, run-scoped, read-only ticket that opens nothing but that run's artifact and zip routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.team_a = cls._team_run("ticket-team-a")
        cls.team_b = cls._team_run("ticket-team-b")
        out = cls.tmp / "data" / "runs" / "ticket-public"
        out.mkdir(parents=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("ticket-public")), encoding="utf-8")
        (out / "candidate.patch").write_text("SYNTHETIC_PUBLIC_PATCH\n", encoding="utf-8")
        cls.store.create_run(run_id="ticket-public", **_row(finished_at=utcnow(), out_dir=str(out)))

    @classmethod
    def _team_run(cls, run_id: str) -> str:
        out = cls.tmp / "data" / "runs" / run_id
        out.mkdir(parents=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle(run_id, provider="codex_gateway")), encoding="utf-8")
        (out / "candidate.patch").write_text(f"SYNTHETIC_PATCH_{run_id}\n", encoding="utf-8")
        (out / "private-notes.env").write_text("SYNTHETIC_UNPUBLISHED_NOTE=offline-marker\n", encoding="utf-8")
        cls.store.create_run(run_id=run_id, **_row(provider="codex", profile_label="development", finished_at=utcnow(), out_dir=str(out)))
        assert cls.store.get_run(run_id)["visibility"] == TEAM
        cls.store.add_event(run_id, utcnow(), "pacing", f"SYNTHETIC_EVENT_{run_id}")
        return run_id

    def mint(self, run_id: str) -> dict:
        response = self.client.post(f"/api/runs/{run_id}/download-ticket", headers=TEAM_HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_minting_needs_the_header_token_and_a_visible_run(self):
        a = self.team_a
        self.assertEqual(self.client.post(f"/api/runs/{a}/download-ticket").status_code, 403)
        self.assertEqual(self.client.post(f"/api/runs/{a}/download-ticket?token={TOKEN}").status_code, 403, "the query token is not read")
        self.assertEqual(self.client.post(f"/api/runs/{a}/download-ticket", json={"admin_token": TOKEN}).status_code, 403, "header only")
        self.assertEqual(self.client.post(f"/api/runs/{a}/download-ticket", headers={"X-Attest-Token": "not-the-token"}).status_code, 403)
        self.assertEqual(self.client.post("/api/runs/no-such-run/download-ticket", headers=TEAM_HEADERS).status_code, 404)
        self.assertEqual(self.client.get(f"/api/runs/{a}/download-ticket", headers=TEAM_HEADERS).status_code, 405)
        body = self.mint(a)
        self.assertEqual(set(body), {"run_id", "ticket", "expires_at", "expires_in_s"})
        self.assertEqual(body["run_id"], a)
        self.assertEqual(body["expires_in_s"], 600)
        self.assertRegex(body["ticket"], rf"^{re.escape(a)}\.[0-9]+\.[0-9a-f]{{64}}$")
        expires = dt.datetime.fromisoformat(body["expires_at"])
        self.assertAlmostEqual((expires - dt.datetime.now(dt.timezone.utc)).total_seconds(), 600, delta=5)
        self.assertEqual(int(body["ticket"].split(".")[-2]), int(expires.timestamp()))
        self.assertEqual(self.server.ticket_run_id(body["ticket"]), a)
        self.assertEqual(self.client.post("/api/runs/ticket-public/download-ticket", headers=TEAM_HEADERS).status_code, 200,
                         "a public run is visible to the team as well, though its downloads need no ticket")

    def test_a_ticket_opens_only_its_own_runs_downloads(self):
        a, b = self.team_a, self.team_b
        ticket = self.mint(a)["ticket"]
        query = f"?ticket={ticket}"
        patch_response = self.client.get(f"/api/runs/{a}/artifacts/candidate.patch{query}")
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.text, f"SYNTHETIC_PATCH_{a}\n")
        self.assertEqual(patch_response.headers["cache-control"], "no-store")
        zipped = self.client.get(f"/api/runs/{a}/bundle.zip{query}")
        self.assertEqual(zipped.status_code, 200)
        self.assertEqual(zipped.headers["cache-control"], "no-store")
        with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
            self.assertEqual(set(archive.namelist()), {f"{a}/proof_bundle.json", f"{a}/candidate.patch"})
        self.assertNotIn(b"SYNTHETIC_UNPUBLISHED_NOTE", zipped.content)
        # run B is as unknown to the bearer of A's ticket as to an anonymous caller
        for path in (f"/api/runs/{b}/artifacts/candidate.patch", f"/api/runs/{b}/bundle.zip", f"/api/runs/{b}/artifacts/proof_bundle.json"):
            response = self.client.get(path + query)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("SYNTHETIC", response.text)
        # the artifact allowlist and the containment checks apply to a ticketed download as to any other
        self.assertEqual(self.client.get(f"/api/runs/{a}/artifacts/private-notes.env{query}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/runs/{a}/artifacts/mutants_..%2F..%2Fetc.py{query}").status_code, 404)

    def test_an_expired_ticket_is_refused(self):
        a, server = self.team_a, self.server
        frozen = 1_800_000_000.0
        with patch.object(server, "_now", lambda: frozen):
            ticket = self.mint(a)["ticket"]
        self.assertEqual(int(ticket.split(".")[-2]), int(frozen) + 600)
        artifact = f"/api/runs/{a}/artifacts/candidate.patch?ticket={ticket}"
        archive = f"/api/runs/{a}/bundle.zip?ticket={ticket}"
        with patch.object(server, "_now", lambda: frozen + 599):
            self.assertEqual((self.client.get(artifact).status_code, self.client.get(archive).status_code), (200, 200))
        with patch.object(server, "_now", lambda: frozen + 600):
            self.assertEqual((self.client.get(artifact).status_code, self.client.get(archive).status_code), (404, 404))
            self.assertIsNone(server.ticket_run_id(ticket))
        with patch.object(server, "_now", lambda: frozen + 3600):
            self.assertEqual(self.client.get(artifact).status_code, 404)
        # a non-positive lifetime issues tickets that are already dead; the header token is unaffected by any of this
        with patch.object(server, "DOWNLOAD_TICKET_SECONDS", -1):
            dead = self.mint(a)["ticket"]
        self.assertEqual(self.client.get(f"/api/runs/{a}/artifacts/candidate.patch?ticket={dead}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/runs/{a}/artifacts/candidate.patch", headers=TEAM_HEADERS).status_code, 200)

    def test_a_ticket_grants_nothing_but_downloads(self):
        a = self.team_a
        ticket = self.mint(a)["ticket"]
        query = f"?ticket={ticket}"
        anonymous = self.client.get("/api/runs").json()
        listing = self.client.get("/api/runs" + query).json()
        self.assertEqual([r["run_id"] for r in listing["runs"]], [r["run_id"] for r in anonymous["runs"]])
        self.assertNotIn(a, [r["run_id"] for r in listing["runs"]])
        self.assertIsNone(listing["current"])
        for path in (f"/api/runs/{a}", f"/api/runs/{a}/events"):
            response = self.client.get(path + query)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("SYNTHETIC", response.text)
        self.assertEqual(self.client.get("/api/tasks" + query).json(), self.client.get("/api/tasks").json())
        self.assertEqual(self.client.get("/api/profiles" + query).json(), {"profiles": self.server.PUBLIC_PROFILES, "team": False})
        health = self.client.get("/api/health" + query).json()
        self.assertFalse(health["team"])
        self.assertIsNone(health["current"])
        # a ticket is not a token: in the header or the body it is just a wrong token, and it cannot mint another ticket
        self.assertEqual(self.client.get(f"/api/runs/{a}", headers={"X-Attest-Token": ticket}).status_code, 404)
        self.assertEqual(self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex", "admin_token": ticket}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/runs/{a}/download-ticket{query}").status_code, 403)
        self.assertEqual(self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex"}, headers={"X-Attest-Token": ticket}).status_code, 403)
        # admission: neither the ticket nor a query token carries team authority or an exemption from the visitor quota
        self.assertEqual(self.client.post("/api/runs" + query, json={"task_id": "audit-sample", "provider": "codex"}).status_code, 403)
        for i in range(3):
            self.store.create_run(run_id=f"ticket-quota-{i}", **_row(status="queued", verdict=None, created_at=utcnow(), requester="testclient"))
        self.assertEqual(self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"}).status_code, 429)
        self.assertEqual(self.client.post("/api/runs" + query, json={"task_id": "audit-sample", "provider": "nebius"}).status_code, 429)
        self.assertEqual(self.client.post(f"/api/runs?token={TOKEN}", json={"task_id": "audit-sample", "provider": "nebius"}).status_code, 429)
        self.assertEqual(self.client.post(f"/api/runs?token={TOKEN}", json={"task_id": "audit-sample", "provider": "codex"}).status_code, 403)
        self.assertEqual(self.store.count_recent("testclient", "2000-01-01"), 3, "no refused request left a row")
        admitted = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"}, headers=TEAM_HEADERS)  # the header is the credential
        self.assertEqual(admitted.status_code, 200, admitted.text)

    def test_forged_and_malformed_tickets_are_refused(self):
        a, b, server = self.team_a, self.team_b, self.server
        genuine = self.mint(a)["ticket"]
        run_id, expiry, signature = genuine.rsplit(".", 2)
        self.assertEqual(run_id, a)
        flipped = signature[:-1] + ("0" if signature[-1] != "0" else "1")
        other_secret = hmac.new(b"not-the-process-secret", f"{a}\n{expiry}".encode("utf-8"), hashlib.sha256).hexdigest()
        forged = [f"{a}.{expiry}.{flipped}",                 # one bit of the signature
                  f"{b}.{expiry}.{signature}",               # run B under A's signature
                  f"{a}.{int(expiry) + 86400}.{signature}",  # an extended expiry
                  f"{a}.{expiry}.{other_secret}",            # signed with another secret
                  f"{a}.{expiry}.{signature.upper()}",       # not the canonical encoding
                  f"{a}.{expiry}", a, "", ".", "..", f"{a}..{signature}", f"{a}.{expiry}.", f"{a}.notanumber.{signature}",
                  f"{a}.{expiry}.{signature}.{signature}", f" {genuine}", genuine + " ", genuine.replace(".", "%2E"), "x" * 600]
        for ticket in forged:
            self.assertIsNone(server.ticket_run_id(ticket), ticket)
            for path in (f"/api/runs/{a}/artifacts/candidate.patch", f"/api/runs/{a}/bundle.zip", f"/api/runs/{b}/artifacts/candidate.patch"):
                response = self.client.get(path, params={"ticket": ticket})
                self.assertEqual(response.status_code, 404, (ticket, path))
                self.assertNotIn("SYNTHETIC", response.text)
        self.assertEqual(server.ticket_run_id(genuine), a)
        self.assertEqual(self.client.get(f"/api/runs/{a}/artifacts/candidate.patch", params={"ticket": genuine}).status_code, 200)
        # another process (a restart) has another secret: the old ticket is refused and the page asks for a new one
        with patch.object(server, "_TICKET_SECRET", secrets.token_bytes(32)):
            self.assertIsNone(server.ticket_run_id(genuine))
            self.assertEqual(self.client.get(f"/api/runs/{a}/bundle.zip", params={"ticket": genuine}).status_code, 404)
            reissued = self.mint(a)["ticket"]
            self.assertEqual(self.client.get(f"/api/runs/{a}/bundle.zip", params={"ticket": reissued}).status_code, 200)
        self.assertIsNone(server.ticket_run_id(reissued), "nor does this process honour the other one's tickets")

    def test_public_runs_download_without_any_credential(self):
        for path in ("/api/runs/ticket-public/artifacts/candidate.patch", "/api/runs/ticket-public/bundle.zip", "/api/runs/ticket-public/artifacts/proof_bundle.json"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertNotEqual(response.headers.get("cache-control"), "no-store", "public downloads are unchanged")
        self.assertEqual(self.client.get("/api/runs/ticket-public/artifacts/candidate.patch").text, "SYNTHETIC_PUBLIC_PATCH\n")
        # a stray or foreign credential on a public download changes nothing
        self.assertEqual(self.client.get("/api/runs/ticket-public/bundle.zip?ticket=garbage").status_code, 200)
        self.assertEqual(self.client.get(f"/api/runs/ticket-public/bundle.zip?token={TOKEN}").status_code, 200)
        self.assertEqual(self.client.get("/api/runs/ticket-public/bundle.zip", params={"ticket": self.mint(self.team_a)["ticket"]}).status_code, 200)


if __name__ == "__main__":
    unittest.main()


# ------------------------------------------------------------------------------------------- revision-6 review, item 2
INCIDENT_BODY = {"task_id": "audit-sample", "profile": "development"}  # the shape of the 19 Oct 2026 verification request


class StrictRunRequests(ConsoleHarness):
    """Admission requests are explicit: unknown fields are refused and the provider has no default, so the request that started an
    unapproved paid run on 19 Oct 2026 (`profile` instead of `provider`, a junk query token) is a 422 now. A refused request never
    reaches the handler or the worker: no row, no queue entry, no budget reservation, no provider. Every check runs against an idle
    worker whose runtime builder and sockets are blocked; nothing is dispatched anywhere."""

    def setUp(self):
        self.enqueued: list = []
        self.built: list = []
        original = self.worker.enqueue

        def recording_enqueue(*args, **kwargs):
            self.enqueued.append((args, kwargs))
            return original(*args, **kwargs)

        def recording_runtime(*args, **kwargs):
            self.built.append(args)
            raise AssertionError("no provider may be built by an admission test")

        self.patchers = [patch.object(self.worker, "enqueue", recording_enqueue), patch.object(Worker, "build_runtime", recording_runtime)]
        for item in self.patchers:
            item.start()

    def tearDown(self):
        for item in reversed(self.patchers):
            item.stop()

    def state(self) -> dict:
        budget = self.client.get("/api/health").json()["budget"]
        return {"rows": sorted(r["run_id"] for r in self.store.list_runs(limit=100000, include_team=True)), "queue": self.worker.queue.qsize(),
                "queued": list(self.worker._queued), "reserved_usd": budget["reserved_usd"], "active_runs": budget["active_runs"]}

    def assert_refused_without_trace(self, response, before: dict, *fields: str) -> None:
        self.assertEqual(response.status_code, 422, response.text)
        body = response.json()
        self.assertEqual(body["error"], "invalid_request")
        for field in fields:
            self.assertIn(field, body["detail"])
        self.assertEqual(self.state(), before, "a refused request left a row, a queue entry or a reservation")
        self.assertEqual(self.enqueued, [], "a refused request reached the worker's admission")
        self.assertEqual(self.built, [], "a refused request built a provider")

    def test_the_incident_request_is_refused_and_leaves_no_trace(self):
        before = self.state()
        for query in ("?token=junk", ""):
            response = self.client.post("/api/runs" + query, json=INCIDENT_BODY)
            self.assert_refused_without_trace(response, before, "provider: Field required", "profile: Extra inputs are not permitted")

    def test_missing_invalid_and_extra_fields_are_refused_before_admission(self):
        before = self.state()
        secret = "synthetic-" + "admin-value-0451"
        bodies = {
            "missing provider": ({"task_id": "audit-sample"}, "provider"),
            "empty provider": ({"task_id": "audit-sample", "provider": ""}, "provider"),
            "unknown provider": ({"task_id": "audit-sample", "provider": "openai"}, "unknown inference profile"),
            "provider in the wrong case": ({"task_id": "audit-sample", "provider": "Nebius"}, "unknown inference profile"),
            "null provider": ({"task_id": "audit-sample", "provider": None}, "provider"),
            "numeric provider": ({"task_id": "audit-sample", "provider": 7}, "provider"),
            "list provider": ({"task_id": "audit-sample", "provider": ["nebius"]}, "provider"),
            "profile next to a valid provider": ({"task_id": "audit-sample", "provider": "nebius", "profile": "development"}, "profile"),
            "an unknown field with an admin token": ({"task_id": "audit-sample", "provider": "codex", "admin_token": secret, "team": True}, "team"),
            "missing task": ({"provider": "nebius"}, "task_id"),
            "not an object": (["audit-sample", "nebius"], "body"),
        }
        for name, (body, field) in bodies.items():
            for headers in ({}, TEAM_HEADERS):  # a team caller's malformed request is refused exactly like a visitor's
                response = self.client.post("/api/runs", json=body, headers=headers)
                with self.subTest(name, team=bool(headers)):
                    self.assert_refused_without_trace(response, before, field)
                    self.assertNotIn(secret, response.text, "the submitted values are not echoed")
        for raw, content_type in ((b"", "application/json"), (b"task_id=audit-sample&provider=nebius", "application/x-www-form-urlencoded"),
                                  (b"{not json", "application/json")):
            response = self.client.post("/api/runs", content=raw, headers={"Content-Type": content_type})
            self.assert_refused_without_trace(response, before)

    def test_valid_requests_keep_their_authorization_rules(self):
        before = self.state()
        refused = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex"})
        self.assertEqual(refused.status_code, 403, "the development profile still needs the team token")
        self.assertEqual(self.state(), before)
        public = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
        self.assertEqual(public.status_code, 200, public.text)
        self.assertEqual(public.json()["visibility"], PUBLIC)
        by_body = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex", "admin_token": TOKEN})
        by_header = self.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex"}, headers=TEAM_HEADERS)
        self.assertEqual((by_body.status_code, by_header.status_code), (200, 200), (by_body.text, by_header.text))
        self.assertEqual({by_body.json()["visibility"], by_header.json()["visibility"]}, {TEAM})
        self.assertEqual([args[1] for args, _ in self.enqueued], ["nebius", "codex", "codex"])
        self.assertEqual(self.built, [], "the idle worker built nothing")
        unknown = self.client.post("/api/runs", json={"task_id": "no-such-task", "provider": "nebius"})
        self.assertEqual(unknown.status_code, 404)
        # the visitor quota still applies to valid public requests (a distinct visitor behind the trusted proxy, three seeded runs)
        proxied = TestClient(PeerAddress(self.server.app, "127.0.0.1"), raise_server_exceptions=False)
        for i in range(3):
            self.store.create_run(run_id=f"strict-quota-{i}", **_row(status="queued", verdict=None, created_at=utcnow(), requester="192.0.2.61"))
        limited = proxied.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"}, headers={"x-forwarded-for": "192.0.2.61"})
        self.assertEqual(limited.status_code, 429, limited.text)

    def test_a_download_ticket_never_authorizes_admission(self):
        out = self.tmp / "data" / "runs" / "strict-team-run"
        out.mkdir(parents=True, exist_ok=True)
        (out / "proof_bundle.json").write_text(json.dumps(_bundle("strict-team-run", provider="codex_gateway")), encoding="utf-8")
        self.store.create_run(run_id="strict-team-run", **_row(provider="codex", profile_label="development", finished_at=utcnow(), out_dir=str(out)))
        ticket = self.server.mint_download_ticket("strict-team-run")["ticket"]
        self.assertEqual(self.server.ticket_run_id(ticket), "strict-team-run", "the ticket itself is valid")
        before = self.state()
        team_body = {"task_id": "audit-sample", "provider": "codex"}
        for response in (self.client.post(f"/api/runs?ticket={ticket}", json=team_body),
                         self.client.post("/api/runs", json=team_body, headers={"X-Attest-Token": ticket}),
                         self.client.post("/api/runs", json=dict(team_body, admin_token=ticket))):
            self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.state(), before)
        self.assert_refused_without_trace(self.client.post(f"/api/runs?ticket={ticket}", json=INCIDENT_BODY), before, "provider")
        self.assert_refused_without_trace(self.client.post("/api/runs", json=INCIDENT_BODY, headers={"X-Attest-Token": ticket}), before, "provider")
        # nor an exemption from the visitor quota
        proxied = TestClient(PeerAddress(self.server.app, "127.0.0.1"), raise_server_exceptions=False)
        for i in range(3):
            self.store.create_run(run_id=f"strict-ticket-quota-{i}", **_row(status="queued", verdict=None, created_at=utcnow(), requester="192.0.2.62"))
        for headers, query in (({"x-forwarded-for": "192.0.2.62"}, f"?ticket={ticket}"),
                               ({"x-forwarded-for": "192.0.2.62", "X-Attest-Token": ticket}, "")):
            response = proxied.post("/api/runs" + query, json={"task_id": "audit-sample", "provider": "nebius"}, headers=headers)
            self.assertEqual(response.status_code, 429, response.text)
        # both reached admission as an ordinary visitor (quota applied, the public profile) and the quota refused them atomically
        self.assertEqual([(args[1], args[3], kwargs["quota"] is not None) for args, kwargs in self.enqueued], [("nebius", "judge-demo", True)] * 2)
        self.assertEqual(self.store.count_recent("192.0.2.62", "2000-01-01"), 3, "no ticket-carrying request left a row")

    def test_the_public_schema_declares_the_strict_body_without_naming_the_gateway(self):
        response = self.client.get("/api/openapi.json")
        schema = response.json()["components"]["schemas"]["RunRequest"]
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(sorted(schema["required"]), ["provider", "task_id"])
        self.assertNotIn("default", schema["properties"]["provider"])
        self.assertNotIn("enum", schema["properties"]["provider"])
        self.assertNotIn("codex", response.text.lower())
