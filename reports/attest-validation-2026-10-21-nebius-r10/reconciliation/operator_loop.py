#!/usr/bin/env python3
"""Operator loop for the revision-10 paid evaluation (21 Oct 2026). The frozen method stops the batch at every operation of uncertain
outcome and never replays it; a resume starts nothing until every unresolved item is acknowledged by id with a note saying what read-only
checks found. This loop does exactly what the operator did by hand for the first stops:

1. resume the batch with the frozen command (no acknowledgement); when it exits 4, the gate has listed the pending items;
2. check every pending item read-only with reconcile_uncertain.py right away and again once ten minutes have passed since its request
   was sent (on 17 Oct an operation appeared 4 min 22 s after its spawn); an accepted operation is re-read until the service reports a
   final status;
3. acknowledge the items by id with a note built from those findings, and resume; repeat until no cell is left to run.

It stops and leaves the batch for a person whenever a finding is not conclusive: a positive control that fails (the listing missed an
operation the run itself recorded), an accepted operation still not final after 30 minutes, or an item kind it does not handle (an
uncertain model call, for example). At most 15 resumptions. Every request it makes itself is a GET (through reconcile_uncertain.py).

    python3 operator_loop.py --clone <pinned checkout> --batch <evaluation out dir> --logs <dir> --checks <dir>
"""
import argparse, datetime as dt, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = ["--provider", "nebius", "--suite", "examples/eval/SUITE-M5.json", "--systems", "baseline,attest", "--attempts", "2", "--workers", "2",
          "--usd-cap", "0.5", "--max-calls", "22", "--max-turns", "14", "--approve-usd", "9.00", "--label", "r10-final"]


def now(): return dt.datetime.now(dt.timezone.utc)
def log(msg): print(f"[{now().strftime('%H:%M:%S')}] {msg}", flush=True)
def ts(v): return dt.datetime.fromisoformat(v.replace("Z", "+00:00"))


def check(clone: Path, batch: Path, out: Path) -> dict:
    """One read-only pass of reconcile_uncertain.py over every pending item; returns {item id: finding record}."""
    code = f"import sys; sys.path.insert(0, {str(clone)!r}); sys.argv=['x','--batch',{str(batch)!r},'--out',{str(out)!r}]; exec(open({str(HERE / 'reconcile_uncertain.py')!r}).read())"
    subprocess.run([sys.executable, "-I", "-c", code], cwd=clone, check=True, capture_output=True, text=True)
    latest = sorted(out.glob("reconciliation-*.json"))[-1]
    return {i["id"]: i for i in json.loads(latest.read_text())["items"]}, latest.name


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--clone", required=True); ap.add_argument("--batch", required=True)
    ap.add_argument("--logs", required=True); ap.add_argument("--checks", required=True); ap.add_argument("--max-resumptions", type=int, default=15)
    a = ap.parse_args(); clone, batch, logs, checks = Path(a.clone), Path(a.batch), Path(a.logs), Path(a.checks)
    ack = None
    for n in range(1, a.max_resumptions + 1):
        cmd = [sys.executable, "scripts/run_evaluation.py", *FROZEN, "--resume", str(batch)] + (["--reconciled", ack[0], "--items", ",".join(ack[1])] if ack else [])
        seg = logs / f"loop-segment{n}.log"
        log(f"segment {n}: {'resume with acknowledgement of ' + ','.join(ack[1]) if ack else 'resume'} -> {seg.name}")
        rc = subprocess.run(cmd, cwd=clone, stdout=open(seg, "w"), stderr=subprocess.STDOUT).returncode
        ack = None
        rows = json.loads((batch / "evaluation.json").read_text())["rows"]
        left = sum(1 for r in rows if r.get("status") == "not_run")
        log(f"segment {n} exited {rc}; {left} cell(s) not run; committed ${json.loads((batch / 'evaluation.json').read_text())['budget']['committed_usd']}")
        if left == 0 and rc != 4:
            log("every cell has run: done"); return 0
        if rc != 4:
            # the batch stopped (an uncertain operation); the next plain resume will list what is pending
            continue
        pending = json.loads((batch / "reconciliation-pending.json").read_text())["items"]
        kinds = {i["kind"] for i in pending}
        if not kinds <= {"sandbox_spawn", "sandbox_operation"}:
            log(f"stop: item kinds {sorted(kinds)} need a person"); return 2
        out = checks / f"loop-{n:02d}"; out.mkdir(parents=True, exist_ok=True)
        times = []
        first, _ = check(clone, batch, out)
        log("first check: " + "; ".join(f"{k} {v['finding'][:70]}" for k, v in first.items()))
        sent = max(ts(i["item"]["started_at_utc"]) for i in pending)
        due = sent + dt.timedelta(seconds=605)
        while now() < due:
            time.sleep(10)
        deadline = now() + dt.timedelta(minutes=30)
        while True:
            final, name = check(clone, batch, out); times.append(name)
            spawns = [v for v in final.values() if "positive_control" in v]
            ops = [v for v in final.values() if "service_status" in v]
            if any(not v["positive_control"]["passed"] for v in spawns):
                log("stop: a positive control failed; the listing cannot be trusted"); return 3
            if all(v.get("service_status") in ("SUCCESS", "FAILED", "CANCELLED") for v in ops):
                break
            if now() > deadline:
                log("stop: an accepted operation is still not final after 30 minutes"); return 3
            time.sleep(60)
        first_t = sorted(out.glob("reconciliation-*.json"))[0].name[len("reconciliation-"):-len(".json")]
        last_t = times[-1][len("reconciliation-"):-len(".json")]
        parts = []
        for v in spawns:
            what = (f"no operation on its source image that no record names was listed up to {last_t}, at least 10 minutes after it was sent; "
                    "taken as not executed as of then") if not v["candidates"] else ("executed: " + ", ".join(f"{u} {r['status']}" for u, r in v["candidate_records"].items()))
            parts.append(f"{v['id']} ({v['run_id']}, {v['stage']} spawn answered HTTP {v.get('http_status')} after it was sent at {v['sent_at_utc'][11:19]}): {what}")
        for v in ops:
            parts.append(f"{v['id']} ({v['run_id']}, {v['stage']}, accepted operation {v['operation_uuid']}): the service reports {v['service_status']}")
        note = (f"Read-only checks (GET /operations?kind=instance and GET /operations/{{id}}, from {first_t} to {last_t}; every listing included "
                f"all operations the run recorded): " + "; ".join(parts) + ". Nothing is sent again; the cells stay ERROR (infra_error); "
                "re-checked after the batch. Recorded by operator_loop.py.")
        ack = (note, [i["id"] for i in pending])
        log(f"acknowledging {len(pending)} item(s)")
    log("stop: the resumption bound was reached"); return 4


if __name__ == "__main__":
    sys.exit(main())
