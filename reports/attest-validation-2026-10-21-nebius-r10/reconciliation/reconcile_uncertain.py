#!/usr/bin/env python3
"""Read-only reconciliation of an evaluation batch's uncertain Sandboxes spawns (21 Oct 2026, the revision-10 paid validation).

The resume gate of scripts/run_evaluation.py lists every unresolved item in reconciliation-pending.json and starts nothing until each one is
acknowledged by id with a note saying what read-only checks found. For each pending item of kind sandbox_spawn this script lists the
account's instance operations from two minutes before the item's run started to now (GET /operations?kind=instance&since=&until=, paged),
matches every listed operation to the batch's records (each run's ledger, each held-out judge operation), and treats an operation on the
spawn's source image (the run's own checkpoint image, which nothing outside the run uses) that no record names, created after the spawn
was sent, as the spawn's operation; its record is read with GET /operations/{id}. Positive control: every operation the item's run itself
recorded in the window must appear in the listing, or nothing is concluded. For each pending item of kind sandbox_operation (an operation
the service accepted, with its id, whose result the halted run never read) its record is read with GET /operations/{id} and its final
status, duration and exit code are reported; it is never spawned again. Nothing is replayed and no run is started: the only requests
are GETs made with attest.http.request_json, asserted at the end. A spawn with no candidate is reported as "not found up to <time>": a late
operation can still appear (on 17 Oct one was created 4 min 22 s after its spawn), so the window and the time of the check are recorded.

    PYTHONPATH=<pinned checkout> python reconcile_uncertain.py --batch <evaluation out dir> --out <dir> [--items u-...,u-...]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from attest.http import request_json
from attest.secrets import load_secret, project_id

BASE = "https://api.tokenfactory.nebius.com/sandboxes/v1"
REQUESTS: list[dict] = []


def ts(value: str) -> float:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def iso(value: float) -> str:
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()


def get(path: str, expect=dict):
    """The only request this script makes: a GET, recorded."""
    headers = {"Authorization": "Bearer " + load_secret("NEBIUS_API_KEY"), "Project": project_id()}
    status, body, _ = request_json("GET", BASE + path, headers, timeout=60, expect=expect)
    REQUESTS.append({"method": "GET", "path": path.split("?")[0], "query": path.split("?", 1)[1] if "?" in path else "", "status": status,
                     "at_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    return body


def listing(since: float, until: float) -> list[dict]:
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
    ap.add_argument("--items", default="", help="comma-separated item ids (default: every pending sandbox_spawn item)")
    args = ap.parse_args(argv)
    batch, out = Path(args.batch).resolve(), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pending = json.loads((batch / "reconciliation-pending.json").read_text(encoding="utf-8"))
    wanted = {i for i in args.items.split(",") if i}
    items = [i for i in pending["items"] if i["kind"] == "sandbox_spawn" and (not wanted or i["id"] in wanted)]
    accepted = [i for i in pending["items"] if i["kind"] == "sandbox_operation" and (not wanted or i["id"] in wanted)]
    evaluation = json.loads((batch / "evaluation.json").read_text(encoding="utf-8"))
    recorded: dict[str, str] = {}
    for run_dir in sorted((batch / "runs").glob("*/")):
        bundle_path = run_dir / "proof_bundle.json"
        if bundle_path.is_file():
            for op in (json.loads(bundle_path.read_text(encoding="utf-8")).get("ledger") or {}).get("sandbox_ops") or []:
                if op.get("operation_uuid"):
                    recorded[op["operation_uuid"]] = f"{run_dir.name}:{op.get('stage')}"
    for row in evaluation.get("rows") or []:
        if row.get("judge_operation_uuid"):
            recorded[row["judge_operation_uuid"]] = f"{row.get('run_id')}:judge"
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    report = {"note": __doc__.split("\n\n")[0], "checked_at_utc": iso(now), "operations_recorded_by_the_batch": len(recorded), "items": []}
    for item in items:
        bundle = json.loads((batch / "runs" / item["run_id"] / "proof_bundle.json").read_text(encoding="utf-8"))
        own = {op["operation_uuid"]: op for op in bundle["ledger"]["sandbox_ops"] if op.get("operation_uuid")}
        spawn = item["item"]
        sent = ts(spawn["started_at_utc"])
        since, until = ts(bundle["started_at_utc"]) - 120, now
        listed = listing(since, until)
        (out / f"listing-{item['id']}-{dt.datetime.fromtimestamp(now, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(json.dumps({"since_unix": int(since), "until_unix": int(until) + 1, "operations": listed},
                                                                  indent=2) + "\n", encoding="utf-8")
        by_uuid = {op.get("uuid"): op for op in listed if isinstance(op, dict)}
        own_in_window = [u for u, op in own.items() if since <= ts(op["started_at_utc"]) <= until]
        missing_own = sorted(u for u in own_in_window if u not in by_uuid)
        candidates = [o for u, o in by_uuid.items() if u not in recorded and o.get("image_uuid") == spawn.get("image_uuid") and ts(o["created_at"]) >= sent - 5]
        records = {}
        for candidate in candidates:
            record = get(f"/operations/{candidate['uuid']}")
            (out / f"operation-{candidate['uuid']}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            records[candidate["uuid"]] = {"status": record.get("status"), "created_at": record.get("created_at"), "duration": record.get("duration"),
                                          "created_after_the_spawn_s": round(ts(candidate["created_at"]) - sent, 1)}
        report["items"].append({
            "id": item["id"], "run_id": item["run_id"], "stage": spawn.get("stage"), "sent_at_utc": spawn.get("started_at_utc"),
            "image_uuid": spawn.get("image_uuid"), "http_status": spawn.get("http_status"), "window_utc": [iso(since), iso(until)],
            "listed": len(listed), "recorded_by_this_run": len(own),
            "positive_control": {"recorded_by_this_run_in_window": len(own_in_window), "of_them_listed": len(own_in_window) - len(missing_own),
                                 "missing": missing_own, "passed": not missing_own and bool(own_in_window)},
            "same_image_operations_listed": sum(1 for o in by_uuid.values() if o.get("image_uuid") == spawn.get("image_uuid")),
            "unrecorded_on_other_images": sum(1 for u, o in by_uuid.items() if u not in recorded and o.get("image_uuid") != spawn.get("image_uuid")),
            "candidates": [c["uuid"] for c in candidates], "candidate_records": records,
            "finding": ("executed: " + ", ".join(f"{u} ({r['status']}, created {r['created_after_the_spawn_s']} s after the spawn was sent)" for u, r in records.items()))
                       if candidates else f"no operation on the spawn's image that no record names was listed up to {iso(until)}",
        })
    for item in accepted:
        op = item["item"]
        record = get(f"/operations/{op['operation_uuid']}")
        (out / f"operation-{op['operation_uuid']}-{dt.datetime.fromtimestamp(now, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8")
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        report["items"].append({
            "id": item["id"], "run_id": item["run_id"], "stage": op.get("stage"), "operation_uuid": op["operation_uuid"],
            "recorded_status": op.get("status"), "service_status": record.get("status"), "created_at": record.get("created_at"),
            "duration": record.get("duration"), "exit_code": result.get("exit_code", record.get("exit_code")),
            "finding": f"accepted operation {op['operation_uuid']}: the service reports {record.get('status')}"
                       + (f", exit code {result.get('exit_code', record.get('exit_code'))}" if result.get("exit_code", record.get("exit_code")) is not None else ""),
        })
    report["requests"] = REQUESTS
    report["requests_summary"] = {"total": len(REQUESTS), "methods": sorted({r["method"] for r in REQUESTS})}
    assert all(r["method"] == "GET" for r in REQUESTS)
    (out / f"reconciliation-{dt.datetime.fromtimestamp(now, dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: i[k] for k in ("id", "positive_control", "candidates", "finding") if k in i} for i in report["items"]], indent=1))
    print("requests:", report["requests_summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
