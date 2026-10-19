#!/usr/bin/env python3
"""Bounded, offline console audit. No real credentials, inference, Sandboxes or sockets.

Run from the repository root:
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B reports/attest-audit-2026-10-19/repro_api_offline.py

The worker loop is disabled before the app module is imported. Every Store and
artifact lives in a temporary directory beneath this report directory and is
removed at exit. Only api-repro-results.json is retained. Findings assert the
current behavior, rather than encoding the desired repaired behavior.
"""

from __future__ import annotations

import concurrent.futures
import importlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
from unittest.mock import patch
import zipfile

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent.parent
sys.path.insert(0, str(ROOT))


def no_network(*args, **kwargs):
    raise AssertionError("External network is blocked by the offline audit")


def run() -> dict:
    from fastapi.testclient import TestClient
    from attest.app.worker import Worker
    from attest.core.manifest import build_manifest, verify_manifest
    from attest.ledger import utcnow

    results: dict = {"scope": "offline synthetic data only", "network": "blocked", "checks": {}}
    with tempfile.TemporaryDirectory(prefix="api-repro-", dir=AUDIT) as scratch:
        tmp = Path(scratch)
        examples = tmp / "examples" / "sample"
        examples.mkdir(parents=True)
        (examples / "task.json").write_text(json.dumps({
            "id": "audit-sample", "title": "Synthetic offline task", "statement": "No execution is performed.",
            "acceptance_criteria": ["offline"],
        }))
        env = {
            "ATTEST_DATA_DIR": str(tmp / "data"), "ATTEST_EXAMPLES_DIR": str(examples.parent),
            "ATTEST_IMPORT_DIRS": str(tmp / "no-imports"), "ATTEST_IMPORT_PROVIDERS": "nebius",
            "ATTEST_ADMIN_TOKEN": "synthetic-team-token", "ATTEST_PUBLIC_RUNS_PER_HOUR": "3",
            "ATTEST_DAILY_USD_CAP": "100", "ATTEST_MIN_FREE_MB": "0", "ATTEST_MIN_FREE_FRAC": "0",
        }
        with patch.dict(os.environ, env), patch.object(Worker, "_loop", lambda self: None), \
             patch.object(Worker, "build_runtime", no_network), \
             patch.object(socket.socket, "connect", no_network), \
             patch.object(socket.socket, "connect_ex", no_network), \
             patch.object(socket, "create_connection", no_network):
            sys.modules.pop("attest.app.server", None)
            server = importlib.import_module("attest.app.server")
            client = TestClient(server.app, raise_server_exceptions=False)
            try:
                # Positive control: enqueue and profile selection do enforce the token.
                denied = client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex"})
                assert denied.status_code == 403
                assert [p["id"] for p in client.get("/api/profiles").json()["profiles"]] == ["nebius"]
                results["checks"]["public_team_enqueue_guard"] = {"status": denied.status_code, "passed": True}
                invalid_provider = client.post("/api/runs", json={"task_id": "audit-sample", "provider": "invalid"})
                traversal_task = client.post("/api/runs", json={"task_id": "../outside"})
                invalid_type = client.post("/api/runs", json={"task_id": {"unexpected": True}})
                assert [invalid_provider.status_code, traversal_task.status_code, invalid_type.status_code] == [400, 404, 422]
                results["checks"]["input_validation_controls"] = {"unknown_provider": 400, "task_path_traversal": 404, "non_string_task_id": 422, "passed": True}

                # Start a team row through the actual admin API; supply synthetic evidence locally.
                created = client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex", "admin_token": "synthetic-team-token"},
                                      headers={"x-forwarded-for": "198.51.100.10"})
                assert created.status_code == 200
                run_id = created.json()["run_id"]
                assert client.get("/api/health").json()["worker_alive"] is False
                assert server.store.get_run(run_id)["status"] == "queued"
                results["checks"]["dead_worker_admission"] = {"worker_alive": False, "enqueue_status": created.status_code,
                                                               "queued_row_created": True, "confirmed": True,
                                                               "setup": "worker loop disabled, so no consumer or paid work exists"}
                out = tmp / "data" / "runs" / run_id
                out.mkdir(parents=True)
                bundle = {
                    "run_id": run_id, "task": {"id": "audit-sample", "title": "Synthetic team evidence"},
                    "verdict": {"verdict": "ERROR", "reasons": ["synthetic private marker"], "warnings": []},
                    "profile": {"label": "development", "provider": {"provider": "codex_gateway"}},
                    "ledger": {"totals": {}, "model_calls": [], "sandbox_operations": []},
                }
                (out / "proof_bundle.json").write_text(json.dumps(bundle))
                (out / "candidate.patch").write_text("SYNTHETIC_TEAM_PATCH\n")
                server.store.update_run(run_id, out_dir=str(out), status="finished", verdict="ERROR", stage="finished", finished_at=utcnow())
                server.store.add_event(run_id, utcnow(), "pacing", "SYNTHETIC_TEAM_EVENT")
                paths = ["/api/runs", f"/api/runs/{run_id}", f"/api/runs/{run_id}/events",
                         f"/api/runs/{run_id}/artifacts/candidate.patch", f"/api/runs/{run_id}/bundle.zip"]
                responses = {p: client.get(p) for p in paths}
                assert all(r.status_code == 200 for r in responses.values())
                assert run_id in responses["/api/runs"].text
                assert "codex_gateway" in responses[f"/api/runs/{run_id}"].text
                assert "SYNTHETIC_TEAM_EVENT" in responses[f"/api/runs/{run_id}/events"].text
                assert responses[f"/api/runs/{run_id}/artifacts/candidate.patch"].text == "SYNTHETIC_TEAM_PATCH\n"
                results["checks"]["team_read_routes_without_token"] = {"http_statuses": {p.replace(run_id, "TEAM_RUN"): r.status_code for p, r in responses.items()}, "confirmed": True}
                row = next(r for r in client.get("/api/runs").json()["runs"] if r["run_id"] == run_id)
                assert row["requester"] == "198.51.100.10" and row["out_dir"] == str(out)
                assert "path" in client.get("/api/tasks").json()["tasks"][0]
                results["checks"]["unnecessary_public_metadata"] = {"requester": row["requester"], "out_dir_returned": True, "task_path_returned": True, "confirmed": True}

                # A denied request becomes allowed by changing only the attacker-controlled first XFF item.
                for i in range(3):
                    server.store.create_run(run_id=f"rate-seed-{i}", task_id="audit-sample", task_title="Synthetic seed", provider="nebius",
                                            profile_label="judge-demo", status="finished", created_at=utcnow(), requester="198.51.100.20")
                limited = client.post("/api/runs", json={"task_id": "audit-sample"}, headers={"x-forwarded-for": "198.51.100.20, 192.0.2.1"})
                changed = client.post("/api/runs", json={"task_id": "audit-sample"}, headers={"x-forwarded-for": "198.51.100.21, 192.0.2.1"})
                assert limited.status_code == 429 and changed.status_code == 200
                results["checks"]["forwarded_for_rotation"] = {"same_connection_original_header": limited.status_code, "same_connection_rotated_first_item": changed.status_code, "confirmed": True}

                # Keep only fake queued tuples; no consumer or execution exists.
                while not server.worker.queue.empty():
                    server.worker.queue.get_nowait()
                    server.worker.queue.task_done()
                # Deterministic scheduling barrier after the independent rate check and before admission.
                barrier = threading.Barrier(4, timeout=10)
                original_enqueue = server.worker.enqueue
                original_count_recent = server.store.count_recent
                read_lock = threading.Lock()

                def serialized_count_recent(*args, **kwargs):
                    # Isolate the separate shared-cursor defect recorded in sqlite-concurrency-probe.json.
                    # This does not make count-and-insert atomic: no insert occurs until the barrier opens.
                    with read_lock:
                        return original_count_recent(*args, **kwargs)

                def synchronized_enqueue(*args, **kwargs):
                    barrier.wait()
                    return original_enqueue(*args, **kwargs)

                def simultaneous_request(_):
                    with TestClient(server.app, raise_server_exceptions=False) as local:
                        response = local.post("/api/runs", json={"task_id": "audit-sample"}, headers={"x-forwarded-for": "198.51.100.30"})
                        return {"status": response.status_code, "body": response.json()}

                with patch.object(server.worker, "enqueue", synchronized_enqueue), \
                     patch.object(server.store, "count_recent", serialized_count_recent), \
                     concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    concurrent_responses = list(pool.map(simultaneous_request, range(4)))
                statuses = [r["status"] for r in concurrent_responses]
                admitted = server.store.count_recent("198.51.100.30", "2000-01-01")
                assert statuses == [200] * 4 and admitted == 4, (concurrent_responses, admitted)
                results["checks"]["rate_check_insert_race"] = {"configured_limit": 3, "simultaneous_requests": 4, "statuses": statuses, "admitted_rows": admitted, "scheduling_barrier": "enqueue entry, after count_recent; count_recent calls serialized only to isolate a separate runtime-specific shared-cursor defect", "confirmed": True}

                # An explicitly disallowed artifact is nevertheless returned by the zip; links are followed too.
                (out / "private-notes.env").write_text("SYNTHETIC_UNPUBLISHED_NOTE=offline-marker\n")
                outside = tmp / "outside-run-sentinel.txt"
                outside.write_text("SYNTHETIC_OUTSIDE_RUN\n")
                (out / "ledger.json").symlink_to(outside)
                direct_private = client.get(f"/api/runs/{run_id}/artifacts/private-notes.env")
                direct_symlink = client.get(f"/api/runs/{run_id}/artifacts/ledger.json")
                zipped = client.get(f"/api/runs/{run_id}/bundle.zip")
                with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
                    private_member = f"{run_id}/private-notes.env"
                    assert archive.read(private_member).startswith(b"SYNTHETIC_UNPUBLISHED_NOTE")
                    assert archive.read(f"{run_id}/ledger.json") == b"SYNTHETIC_OUTSIDE_RUN\n"
                assert direct_private.status_code == 404 and direct_symlink.text == "SYNTHETIC_OUTSIDE_RUN\n"
                results["checks"]["archive_and_symlink_boundary"] = {"non_allowlisted_direct_status": direct_private.status_code, "non_allowlisted_in_zip": True, "symlink_target_outside_run_returned": True, "precondition": "a local/imported run directory contains a non-public file or symlink; no remote file-creation primitive demonstrated", "confirmed": True}
                (out / "ledger.json").unlink()
                (out / "private-notes.env").unlink()

                # The exact per-file size boundary silently omits a manifested artifact.
                (out / "verify_raw.json").write_bytes(b" " * 5_000_000)
                manifest = build_manifest(out, run_id)
                (out / "manifest.json").write_text(json.dumps(manifest))
                assert verify_manifest(out, manifest)["ok"]
                archive_response = client.get(f"/api/runs/{run_id}/bundle.zip")
                extracted = tmp / "downloaded"
                with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
                    assert f"{run_id}/verify_raw.json" not in archive.namelist()
                    archive.extractall(extracted)  # entries originate exclusively from this script's synthetic directory
                downloaded = verify_manifest(extracted / run_id, manifest)
                assert downloaded["missing"] == ["verify_raw.json"]
                results["checks"]["zip_silent_artifact_omission"] = {"response_status": archive_response.status_code, "source_manifest_ok": True, "artifact_bytes": 5_000_000, "downloaded_missing": downloaded["missing"], "confirmed": True}

                # Failure output is returned verbatim, including traceback details and internal paths.
                synthetic_failure = 'Traceback (most recent call last):\n  File "/opt/attest/app/private_module.py", line 1\nRuntimeError: SYNTHETIC_INTERNAL_DETAIL'
                server.store.update_run(run_id, status="error", error=synthetic_failure)
                err = client.get(f"/api/runs/{run_id}/events")
                assert err.json()["error"] == synthetic_failure
                with patch.object(server.store, "list_runs", side_effect=RuntimeError("SYNTHETIC_BACKEND_DETAIL /private/synthetic-path")):
                    raw_error = client.get("/api/runs")
                assert raw_error.status_code == 500 and "SYNTHETIC_BACKEND_DETAIL" in raw_error.text
                results["checks"]["raw_error_detail_public"] = {"stored_traceback_returned_verbatim": True, "unhandled_http_status": raw_error.status_code, "raw_exception_detail_returned": True, "confirmed": True}

                # The download/detail readers do not handle a partially written/corrupt proof bundle.
                (out / "proof_bundle.json").write_text('{"run_id":')
                partial = client.get(f"/api/runs/{run_id}")
                assert partial.status_code == 500 and partial.json()["error"] == "JSONDecodeError"
                results["checks"]["partial_bundle_detail_failure"] = {"response_status": partial.status_code, "exception_type": partial.json()["error"], "confirmed": True, "precondition": "partial or corrupt proof_bundle.json; normal writer uses write_text rather than atomic replace"}

                # Bounded retention skips every error row, including its on-disk partial output.
                retention = tmp / "retention"
                for status in ("finished", "error"):
                    candidate = retention / status
                    candidate.mkdir(parents=True)
                    (candidate / "trajectory.jsonl").write_text("synthetic partial output\n")
                    server.store.create_run(run_id=f"retention-{status}", task_id="audit-sample", task_title="Synthetic retention", provider="nebius",
                                            profile_label="judge-demo", status=status, created_at="2000-01-01T00:00:00Z", out_dir=str(candidate))
                pruned = server.store.prune_runs(retention, keep=0, protect=())
                assert pruned == ["retention-finished"] and (retention / "error").is_dir()
                results["checks"]["error_directories_escape_retention"] = {"keep": 0, "pruned_finished": True, "error_directory_still_present": True, "confirmed": True}
            finally:
                client.close()
                server.store._conn.close()
    return results


if __name__ == "__main__":
    results = run()
    target = AUDIT / "api-repro-results.json"
    target.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"retained_report": str(target.relative_to(ROOT)), "check_count": len(results["checks"]), "all_behavior_assertions_passed": True}, indent=2))
