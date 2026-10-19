#!/usr/bin/env python3
"""Bounded revision-5 residual checks; synthetic token/data, idled worker, blocked sockets.
Run with PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B <this file> from the repository root.
Uses the reviewed acceptance harness. No source edits or production calls.
"""
import io
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import quote
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
sys.path.insert(0, str(ROOT))
from tests.test_audit_console import ConsoleHarness, TOKEN, _bundle, _row
from attest.ledger import utcnow

C = ConsoleHarness
C.setUpClass()
results = {"scope": "temporary synthetic data; worker idled; build_runtime and socket connections blocked", "checks": {}}
try:
    marker = "SYNTHETIC_RAW_DIAGNOSTIC /opt/attest/private_module.py"
    C.store.create_run(run_id="sanitized-row", **_row(status="queued", verdict=None))
    with unittest.TestCase().assertLogs("attest.app", level="ERROR"):
        C.store.record_failure("sanitized-row", "worker_error", marker, detail="Traceback: " + marker)
    clean = {}
    for route in ("/api/runs", "/api/runs/sanitized-row", "/api/runs/sanitized-row/events"):
        response = C.client.get(route)
        clean[route] = {"status": response.status_code, "diagnostic_present": marker in response.text}
        assert response.status_code == 200 and marker not in response.text
    results["checks"]["row_only_error_is_sanitized"] = clean

    out = C.tmp / "data" / "runs" / "error-bundle"
    out.mkdir(parents=True)
    bundle = _bundle("error-bundle", verdict="ERROR")
    bundle["verdict"]["reasons"] = ["RuntimeError: " + marker]
    (out / "proof_bundle.json").write_text(json.dumps(bundle))
    (out / "PROOF.md").write_text("Synthetic ERROR record: " + marker)
    C.store.create_run(run_id="error-bundle", **_row(status="finished", verdict="ERROR", out_dir=str(out),
                       finished_at=utcnow(), reasons=json.dumps(bundle["verdict"]["reasons"])))
    C.store.add_event("error-bundle", utcnow(), "error", "MODEL ERROR: " + marker)
    exposed = {}
    for route in ("/api/runs", "/api/runs/error-bundle", "/api/runs/error-bundle/events",
                  "/api/runs/error-bundle/artifacts/proof_bundle.json", "/api/runs/error-bundle/artifacts/PROOF.md"):
        response = C.client.get(route)
        exposed[route] = {"status": response.status_code, "diagnostic_present": marker in response.text}
        assert response.status_code == 200 and marker in response.text
    zipped = C.client.get("/api/runs/error-bundle/bundle.zip")
    with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
        marker_in_zip = any(marker.encode() in archive.read(name) for name in archive.namelist())
    assert zipped.status_code == 200 and marker_in_zip
    exposed["/api/runs/error-bundle/bundle.zip"] = {"status": zipped.status_code, "diagnostic_present_in_member": marker_in_zip}
    results["checks"]["bundle_reasons_and_events_still_public"] = exposed

    denied = C.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "codex"})
    query_team = C.client.post("/api/runs?token=" + quote(TOKEN), json={"task_id": "audit-sample", "provider": "codex"})
    assert denied.status_code == 403 and query_team.status_code == 200
    team_id = query_team.json()["run_id"]
    anonymous = C.client.get("/api/runs").json()
    authenticated = C.client.get("/api/runs?token=" + quote(TOKEN)).json()
    assert team_id not in {r["run_id"] for r in anonymous["runs"]}
    assert team_id in {r["run_id"] for r in authenticated["runs"]}
    for i in range(3):
        C.store.create_run(run_id=f"quota-seed-{i}", **_row(created_at=utcnow(), requester="testclient", cost_usd=0))
    exhausted = C.client.post("/api/runs", json={"task_id": "audit-sample", "provider": "nebius"})
    query_admin = C.client.post("/api/runs?token=" + quote(TOKEN), json={"task_id": "audit-sample", "provider": "nebius"})
    assert exhausted.status_code == 429 and query_admin.status_code == 200
    results["checks"]["query_token_has_full_team_privileges"] = {
        "no_token_team_enqueue": denied.status_code, "query_token_team_enqueue": query_team.status_code,
        "team_run_hidden_anonymously": True, "query_token_lists_team_run": True,
        "exhausted_public_visitor": exhausted.status_code, "query_token_bypasses_visitor_quota": query_admin.status_code,
        "token_kind": "synthetic test constant; no token value retained",
    }
finally:
    C.tearDownClass()
(OUT / "api-review-repro-results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps({"checks": len(results["checks"]), "all_current_behavior_assertions_passed": True}))
