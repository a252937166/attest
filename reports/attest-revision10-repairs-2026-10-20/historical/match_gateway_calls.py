#!/usr/bin/env python3
"""Offline: match every model call the two reconciled runs recorded with the development gateway's ingress log of 17 Oct 2026
(`gateway-ingress-2026-10-17.txt`, extracted read-only), and attribute every /v1/run request of each run's window to a recorded call of
any kept bundle. The two clocks differ: every entry ends 3.0 to 3.9 s after the end of the call it logs (client start + elapsed), and
its request time is 2.2 to 3.3 s shorter than the client's elapsed time (connection set-up and the proxy are outside nginx's timing),
so the median of those offsets over the window is estimated first. A call matches an entry when the offset-corrected end is within 1.5 s
and the entry's request time lies between the gateway's own duration for the call (`gateway_duration_ms`, the backend's time, which nginx
contains) and the client's elapsed time corrected by the median offset plus 1.5 s (a slow connection set-up through the client's proxy
shortens nginx's time, never lengthens it); each entry is used once, nearest end first. Output: gateway-match.json."""

from __future__ import annotations

import datetime as dt
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = dt.date(2026, 10, 17)
RUNS = ("balanced-brackets-attest-a1-20261017T121900586528Z", "semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z")
BATCH = ROOT / "reports/attest-reliability-2026-10-17/evaluation-paced-codex/runs"


def utc(clock: str) -> dt.datetime:
    h, m, s = map(int, clock.split(":"))
    return dt.datetime(DAY.year, DAY.month, DAY.day, h, m, s, tzinfo=dt.timezone.utc)


def parse(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    entries = []
    for line in (HERE / "gateway-ingress-2026-10-17.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        end, start, method, path, status, size, rt = line.split()
        entries.append({"end": utc(end), "start": utc(end) - dt.timedelta(seconds=float(rt)), "method": method, "path": path, "status": int(status),
                        "request_time_s": float(rt)})
    # every gateway call any kept bundle recorded that day
    calls = []
    for path in glob.glob(str(ROOT / "reports/**/proof_bundle.json"), recursive=True):
        try:
            bundle = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for call in (bundle.get("ledger") or {}).get("model_calls") or []:
            if call.get("provider") == "codex_gateway" and str(call.get("started_at_utc", "")).startswith("2026-10-17"):
                calls.append({"run": Path(path).parent.name, "stage": call.get("stage"), "start": parse(call["started_at_utc"]),
                              "elapsed_s": (call.get("elapsed_ms") or 0) / 1000, "ok": call.get("ok"),
                              "gateway_s": (call["gateway_duration_ms"] / 1000) if call.get("gateway_duration_ms") else None})
    runs = []
    posts = [e for e in entries if e["method"] == "POST" and e["path"] == "/v1/run"]
    window_calls = [c for c in calls if posts and posts[0]["start"] - dt.timedelta(minutes=5) <= c["start"] <= posts[-1]["end"]]

    def end_of(call):
        return call["start"] + dt.timedelta(seconds=call["elapsed_s"])

    def median(values):
        values = sorted(values)
        return values[len(values) // 2] if values else 0.0
    nearest = [min(posts, key=lambda e, c=c: abs((e["end"] - end_of(c)).total_seconds())) for c in window_calls]
    end_offset = median([(e["end"] - end_of(c)).total_seconds() for c, e in zip(window_calls, nearest)])
    time_offset = median([e["request_time_s"] - c["elapsed_s"] for c, e in zip(window_calls, nearest)])
    pairs = []
    for ci, call in enumerate(window_calls):
        for ei, entry in enumerate(posts):
            gap = abs((entry["end"] - end_of(call)).total_seconds() - end_offset)
            low = (call["gateway_s"] - 0.5) if call["gateway_s"] else 0.0
            high = call["elapsed_s"] + time_offset + 1.5
            if gap <= 1.5 and low <= entry["request_time_s"] <= high:
                pairs.append((gap, ci, ei))
    taken_calls, taken_entries, matched_all = set(), set(), {}
    for _, ci, ei in sorted(pairs):
        if ci in taken_calls or ei in taken_entries:
            continue
        taken_calls.add(ci)
        taken_entries.add(ei)
        matched_all[id(window_calls[ci])] = posts[ei]
    for run_id in RUNS:
        bundle = json.loads((BATCH / run_id / "proof_bundle.json").read_text(encoding="utf-8"))
        start, end = parse(bundle["started_at_utc"]), parse(bundle["finished_at_utc"])
        own = [c for c in calls if c["run"] == run_id]
        window = [e for e in posts if start - dt.timedelta(seconds=5) <= e["start"] <= end]
        owners = {}
        for entry in window:
            owner = next((c for c in calls if matched_all.get(id(c)) is entry), None)
            owners.setdefault(owner["run"] if owner else "no recorded call", 0)
            owners[owner["run"] if owner else "no recorded call"] += 1
        runs.append({"run_id": run_id, "window_utc": [start.isoformat(), end.isoformat()], "recorded_calls": len(own),
                     "recorded_calls_ok": sum(1 for c in own if c["ok"]), "matched_to_an_ingress_entry": sum(1 for c in own if matched_all.get(id(c))),
                     "matched_entries_status": sorted({matched_all[id(c)]["status"] for c in own if matched_all.get(id(c))}),
                     "unmatched_calls": [{"stage": c["stage"], "start": c["start"].isoformat()} for c in own if not matched_all.get(id(c))],
                     "run_requests_in_window": len(window), "attributed": owners})
    unmatched_entries = [{"end_utc": e["end"].strftime("%H:%M:%S"), "request_time_s": e["request_time_s"], "status": e["status"]}
                         for i, e in enumerate(posts) if i not in taken_entries]
    report = {"note": __doc__.split("\n\n")[0], "ingress_entries": len(entries), "ingress_run_requests": len(posts), "recorded_gateway_calls_that_day": len(calls),
              "recorded_calls_in_the_log_window": len(window_calls), "matched_pairs": len(matched_all),
              "estimated_offsets_s": {"entry_end_minus_call_end": round(end_offset, 2), "request_time_minus_elapsed": round(time_offset, 2)},
              "recorded_calls_without_an_entry": [{"run": c["run"], "stage": c["stage"], "start": c["start"].isoformat()} for c in window_calls if id(c) not in matched_all],
              "entries_without_a_recorded_call": unmatched_entries, "runs": runs}
    (HERE / "gateway-match.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
