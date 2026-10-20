#!/usr/bin/env python3
"""Read-only reconciliation of the two VERIFIED development runs of 17 Oct 2026 that went on after a mutant spawn of uncertain outcome
(revision 10, item 5). Nothing is replayed and no run is started: the only requests are GET /operations (the account's operation list,
with since/until) and GET /operations/{id} (one operation's record) on the Token Factory Sandboxes API, made with attest.http.request_json
and asserted to be GETs. Raw answers are saved next to this script (`listing-*.json`, `operation-*.json`); the matching is in
`sandboxes-reconciliation.json`.

    python reconcile_historical.py --batch reports/attest-reliability-2026-10-17/evaluation-paced-codex --out <dir>

For each uncertain spawn the account's instance operations from two minutes before the run to one hour after it are listed, every listed
operation is matched to the batch's records (each run's ledger and each held-out judge operation), and an operation on the spawn's source
image (the run's own checkpoint image, which nothing outside the run uses) that no record names, created after the spawn was sent, is a
candidate for the spawn's operation; its record is read and analysed (analyze_executed_mutants.py). Positive control: every operation
the run itself recorded in the window must appear in the listing; when one does not, the listing is not complete enough to conclude
anything. (A first pass of this script looked only two minutes past each spawn and missed the semver operation created 4 min 22 s
after its spawn; the window was widened before any conclusion was recorded.)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from attest.http import request_json  # noqa: E402
from attest.secrets import load_secret, project_id  # noqa: E402

BASE = "https://api.tokenfactory.nebius.com/sandboxes/v1"
RUNS = ("balanced-brackets-attest-a1-20261017T121900586528Z", "semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z")
REQUESTS: list[dict] = []


def ts(value: str) -> float:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def get(path: str, expect=dict):
    """The only request this script makes: a GET, recorded."""
    headers = {"Authorization": "Bearer " + load_secret("NEBIUS_API_KEY"), "Project": project_id()}
    status, body, _ = request_json("GET", BASE + path, headers, timeout=60, expect=expect)
    REQUESTS.append({"method": "GET", "path": path.split("?")[0], "query": path.split("?", 1)[1] if "?" in path else "", "status": status,
                     "at_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    return body


def listing(since: float, until: float) -> list[dict]:
    """Every instance operation created in [since, until], paged."""
    found, offset = [], 0
    while True:
        page = get(f"/operations?kind=instance&since={int(since)}&until={int(until) + 1}&limit=1000&offset={offset}", expect=list)
        found += page
        if len(page) < 1000:
            return found
        offset += len(page)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    batch, out = Path(args.batch).resolve(), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    evaluation = json.loads((batch / "evaluation.json").read_text(encoding="utf-8"))
    # every operation the batch recorded: each run's ledger and each judge operation (the judge runs on the run's checkpoint image)
    recorded: dict[str, str] = {}
    for run_dir in sorted((batch / "runs").glob("*/")):
        bundle_path = run_dir / "proof_bundle.json"
        if bundle_path.is_file():
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            for op in (bundle.get("ledger") or {}).get("sandbox_ops") or []:
                if op.get("operation_uuid"):
                    recorded[op["operation_uuid"]] = f"{run_dir.name}:{op.get('stage')}"
    for row in evaluation.get("rows") or []:
        if row.get("judge_operation_uuid"):
            recorded[row["judge_operation_uuid"]] = f"{row.get('run_id')}:judge"
    report = {"note": __doc__.split("\n\n")[0], "batch": str(batch.relative_to(ROOT)) if batch.resolve().is_relative_to(ROOT) else str(batch),
              "operations_recorded_by_the_batch": len(recorded), "runs": []}
    for run_id in RUNS:
        bundle = json.loads((batch / "runs" / run_id / "proof_bundle.json").read_text(encoding="utf-8"))
        own = {op["operation_uuid"]: op for op in bundle["ledger"]["sandbox_ops"] if op.get("operation_uuid")}
        judge = next((r.get("judge_operation_uuid") for r in evaluation["rows"] if r.get("run_id") == run_id), None)
        uncertain = [op for op in bundle["ledger"]["sandbox_ops"] if op.get("status") in ("UNCERTAIN", "ACCEPTED_UNREAD", None, "PENDING") and not op.get("operation_uuid")]
        since, until = ts(bundle["started_at_utc"]) - 120, ts(bundle["finished_at_utc"]) + 3600
        listed = listing(since, until)
        (out / f"listing-{run_id[:40]}.json").write_text(json.dumps({"since_unix": int(since), "until_unix": int(until) + 1, "operations": listed}, indent=2) + "\n",
                                                         encoding="utf-8")
        by_uuid = {op.get("uuid"): op for op in listed if isinstance(op, dict)}
        own_in_window = [u for u, op in own.items() if since <= ts(op["started_at_utc"]) <= until]
        missing_own = sorted(u for u in own_in_window if u not in by_uuid)
        entry = {"run_id": run_id, "verdict": bundle["verdict"]["verdict"], "window_utc": [dt.datetime.fromtimestamp(since, dt.timezone.utc).isoformat(),
                                                                                           dt.datetime.fromtimestamp(until, dt.timezone.utc).isoformat()],
                 "listed": len(listed), "recorded_by_this_run": len(own), "judge_operation_uuid": judge,
                 "positive_control": {"recorded_by_this_run_in_window": len(own_in_window), "of_them_listed": len(own_in_window) - len(missing_own),
                                      "missing": missing_own, "judge_listed": bool(judge and judge in by_uuid)},
                 "listed_by_record": {"this run": sum(1 for u in by_uuid if u in own), "this run's judge": int(bool(judge and judge in by_uuid)),
                                      "other runs of the batch": sum(1 for u in by_uuid if u in recorded and u not in own and u != judge),
                                      "recorded nowhere": sum(1 for u in by_uuid if u not in recorded)},
                 "unrecorded": [{k: op.get(k) for k in ("uuid", "status", "created_at", "duration", "image_uuid", "consumed_cpu")}
                                for u, op in sorted(by_uuid.items(), key=lambda kv: str(kv[1].get("created_at"))) if u not in recorded],
                 "uncertain_spawns": []}
        for op in uncertain:
            sent = ts(op["started_at_utc"])
            candidates = [o for u, o in by_uuid.items() if u not in recorded and o.get("image_uuid") == op.get("image_uuid") and ts(o["created_at"]) >= sent - 5]
            records = {}
            for candidate in candidates:
                record = get(f"/operations/{candidate['uuid']}")
                (out / f"operation-{candidate['uuid']}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                records[candidate["uuid"]] = {"status": record.get("status"), "created_at": record.get("created_at"), "duration": record.get("duration")}
            for candidate in candidates:
                records[candidate["uuid"]]["created_after_the_spawn_s"] = round(ts(candidate["created_at"]) - sent, 1)
            entry["uncertain_spawns"].append({"stage": op.get("stage"), "sent_at_utc": op.get("started_at_utc"), "image_uuid": op.get("image_uuid"),
                                              "same_image_operations_listed": sum(1 for o in by_uuid.values() if o.get("image_uuid") == op.get("image_uuid")),
                                              "candidates": [c["uuid"] for c in candidates], "candidate_records": records})
        report["runs"].append(entry)
    report["requests"] = REQUESTS
    report["requests_summary"] = {"total": len(REQUESTS), "methods": sorted({r["method"] for r in REQUESTS})}
    assert all(r["method"] == "GET" for r in REQUESTS)
    (out / "sandboxes-reconciliation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({r["run_id"]: {"listed": r["listed"], "positive_control": r["positive_control"], "listed_by_record": r["listed_by_record"],
                                    "uncertain_spawns": [{k: s[k] for k in ("stage", "candidates", "same_image_operations_listed")} for s in r["uncertain_spawns"]]}
                      for r in report["runs"]}, indent=2))
    print("requests:", report["requests_summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
