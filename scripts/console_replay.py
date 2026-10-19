#!/usr/bin/env python3
"""Replay a recorded run into a console store as a synthetic fixture, to exercise the queued and running views offline.

The row is created with requester "replay" and profile label "replay-fixture", so the API reports provenance
"synthetic" and the console labels it as a synthetic fixture on screen. Events come from a recorded progress log
(`[HH:MM:SS] message` lines, the text the pipeline sends to its progress callback), from a `console-record.json`
(`{"events": [{at_utc, stage, message}]}`) or, failing both, from the bundle's ledger timestamps. Live meters are
taken from the bundle's ledger up to each event's wall-clock time, so they are the recorded numbers, not guesses.
When the replay ends the row is finalized from the bundle exactly as a restart reconciliation would do.

No inference, no sandboxes, no network. Refuses the production data directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.app.db import Store  # noqa: E402
from attest.ledger import utcnow  # noqa: E402

PRODUCTION_DATA_DIRS = ("/var/lib/attest", "/opt/attest", "/etc/attest")
LOG_LINE = re.compile(r"^\[(\d\d):(\d\d):(\d\d)\]\s+(.*)$")
STAGE_RULES = (
    (r"^frozen task", "freeze"), (r"^creating checkpoint|^checkpoint .* ready|^suite binding|^install", "checkpoint"),
    (r"^specification|^spec:", "spec"), (r"^contract audit", "contract"), (r"^sealing|^sealed \d+", "seal"), (r"red check", "red"),
    (r"^implementation|^turn \d+:", "implement"), (r"^verification|^verify:|^existing suite|^tamper scan", "verify"),
    (r"^held-out", "heldout"), (r"^breaker", "break"), (r"^drift audit", "audit"), (r"^arbitration", "arbitrate"),
    (r"^verdict|^ABORT", "finished"), (r"^MODEL ERROR", "error"),
)


def stage_for(message: str, previous: str | None) -> str | None:
    for pattern, stage in STAGE_RULES:
        if re.search(pattern, message):
            return stage
    return previous


def events_from_log(path: Path, day: dt.date) -> list[dict]:
    events, stage = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = LOG_LINE.match(line)
        if not match:
            continue
        hh, mm, ss, message = match.groups()
        stage = stage_for(message, stage)
        at = dt.datetime.combine(day, dt.time(int(hh), int(mm), int(ss)), tzinfo=dt.timezone.utc)
        events.append({"at_utc": at.isoformat(), "stage": stage, "message": message})
    return events


def events_from_record(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [{"at_utc": e.get("at_utc") or "", "stage": e.get("stage"), "message": e.get("message") or ""} for e in data.get("events") or []]


def events_from_ledger(bundle: dict) -> list[dict]:
    events = []
    for call in (bundle.get("ledger") or {}).get("model_calls") or []:
        events.append({"at_utc": call["started_at_utc"], "stage": stage_for(call["stage"], None) or call["stage"].split("-")[0],
                       "message": f"model call {call['role']} ({call['requested_model']}) at stage {call['stage']}"})
    for op in (bundle.get("ledger") or {}).get("sandbox_ops") or []:
        events.append({"at_utc": op["started_at_utc"], "stage": stage_for(op["stage"], None) or op["stage"].split("-")[0],
                       "message": f"sandbox operation {op['stage']} {op['operation_uuid']}: {op['status']}"})
    events.sort(key=lambda e: e["at_utc"])
    return events


def meters_at(bundle: dict, at_iso: str) -> dict:
    """Ledger totals up to a wall-clock instant: calls started, sandbox operations started, committed USD so far."""
    ledger = bundle.get("ledger") or {}
    calls = [c for c in ledger.get("model_calls") or [] if (c.get("started_at_utc") or "") <= at_iso]
    ops = [o for o in ledger.get("sandbox_ops") or [] if (o.get("started_at_utc") or "") <= at_iso]
    committed = sum((c.get("cost_usd") if c.get("cost_usd") is not None else (c.get("reserved_usd") or 0.0)) for c in calls)
    return {"model_calls": len(calls), "sandbox_ops": len(ops), "cost_committed_usd": round(committed, 6),
            "tokens_in": sum(c.get("tokens_in") or 0 for c in calls), "tokens_out": sum(c.get("tokens_out") or 0 for c in calls)}


def guard_store(path: Path) -> None:
    candidates = {str(path.absolute()), str(path.resolve())}
    candidates |= {c[len("/private"):] for c in list(candidates) if c.startswith("/private/")}  # macOS symlinks /var -> /private/var
    for candidate in candidates:
        for forbidden in PRODUCTION_DATA_DIRS:
            if candidate == forbidden or candidate.startswith(forbidden + "/"):
                raise SystemExit(f"refusing to replay into {candidate}: that is a production data directory")


def replay(store_path: Path, run_dir: Path, events: list[dict], interval: float, run_id: str | None = None,
           delay_start: float = 0.0, quiet: bool = False) -> dict:
    guard_store(store_path)
    bundle = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8"))
    task = bundle.get("task") or {}
    run_id = run_id or f"replay-{task.get('id', 'run')}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    provider = ((bundle.get("profile") or {}).get("provider") or {}).get("provider") or "unknown"
    provider = provider.replace("_gateway", "").replace("_tokenfactory", "")
    store = Store(store_path)
    store.create_run(run_id=run_id, task_id=task.get("id") or "unknown", task_title=task.get("title") or run_id, provider=provider,
                     profile_label="replay-fixture", status="queued", stage="queued", created_at=utcnow(), requester="replay")
    if not quiet:
        print(f"replay {run_id}: queued ({len(events)} events, {interval}s apart, start delay {delay_start}s)", flush=True)
    if delay_start > 0:
        time.sleep(delay_start)
    store.update_run(run_id, status="running", started_at=utcnow(), stage="starting")
    for index, event in enumerate(events):
        meters = meters_at(bundle, event["at_utc"]) if event.get("at_utc") else {}
        store.add_event(run_id, utcnow(), event.get("stage"), event["message"])
        store.update_run(run_id, stage=event.get("stage"), **meters)
        if not quiet:
            print(f"  [{index + 1}/{len(events)}] {event.get('stage') or '-':<10} {event['message'][:100]}", flush=True)
        if interval > 0 and index < len(events) - 1:
            time.sleep(interval)
    totals = (bundle.get("ledger") or {}).get("totals") or {}
    verdict = (bundle.get("verdict") or {})
    store.update_run(run_id, status="finished", verdict=verdict.get("verdict"), finished_at=utcnow(), stage="finished", out_dir=str(run_dir.resolve()),
                     cost_usd=totals.get("cost_usd"), cost_committed_usd=totals.get("cost_usd_committed"), tokens_in=totals.get("tokens_in"),
                     tokens_out=totals.get("tokens_out"), sandbox_ops=totals.get("sandbox_operations"), model_calls=totals.get("model_calls"),
                     reasons=json.dumps(verdict.get("reasons") or []), warnings=json.dumps(verdict.get("warnings") or []))
    if not quiet:
        print(f"replay {run_id}: finished {verdict.get('verdict')}", flush=True)
    return {"run_id": run_id, "events": len(events), "verdict": verdict.get("verdict")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--store", required=True, help="path to the console SQLite store (a test data directory, never production)")
    parser.add_argument("--run-dir", required=True, help="recorded run directory with proof_bundle.json")
    parser.add_argument("--log", help="progress log with [HH:MM:SS] lines (for example reports/attest-m1-2026-10-16/run-brackets-codex.log)")
    parser.add_argument("--events", help="console-record.json with recorded events (overrides --log)")
    parser.add_argument("--interval", type=float, default=1.3, help="seconds between events (default 1.3)")
    parser.add_argument("--delay-start", type=float, default=0.0, help="seconds to stay queued before running")
    parser.add_argument("--run-id")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    bundle = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8"))
    day = dt.datetime.fromisoformat(bundle["started_at_utc"]).date()
    if args.events:
        events = events_from_record(Path(args.events))
    elif args.log:
        events = events_from_log(Path(args.log), day)
    elif (run_dir / "console-record.json").is_file():
        events = events_from_record(run_dir / "console-record.json")
    else:
        events = events_from_ledger(bundle)
    if not events:
        print("no events to replay", file=sys.stderr)
        return 2
    replay(Path(args.store), run_dir, events, args.interval, args.run_id, args.delay_start, args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
