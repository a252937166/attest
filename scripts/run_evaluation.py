#!/usr/bin/env python3
"""Controlled evaluation harness: a plain agent vs Attest on the frozen suite (M1 revision, 16 Oct 2026; provenance and
pacing revision, 17 Oct 2026).

Method:
* Every scheduled attempt is pre-registered in `schedule.json` before any run starts and reported in `evaluation.json`,
  whether it completed, failed on infrastructure, or was never executed (with the reason). There is no merge and no
  best-of selection.
* The held-out suite is stripped from the task handed to BOTH systems; only the judge sees it. The judge runs the
  existing suite plus the held-out suite on the final patch in a fresh branch from the checkpoint, bound through the
  supervisor when the repository allows (evidence class recorded per row).
* Both systems share the implementation model, tools, turn budget and per-run caps; Attest pays its verification
  overhead out of the same per-run cap.

Provenance (17 Oct 2026): a batch runs from an immutable snapshot in a fresh process. The launcher copies the `attest`
package, this script and `examples/` into `<out>/snapshot/`, records their digests, and re-executes itself from the copy;
the snapshot process imports the package from the snapshot only. `schedule.json` records the application revision, the
evaluation-script digest, the examples digest and the guest-program digests actually executed; every row records the
revision its bundle carries, and the report marks a task's comparison invalid when any of its cells ran a different
revision or the snapshot changed during the batch. The working tree may be edited while a batch runs; that is detected and
reported, and it cannot affect the batch.

Pacing (17 Oct 2026): on the Codex gateway all roles and workers draw from one hourly budget (attest/models/pacing.py).
The harness waits, visibly and with a bound, for enough headroom before it starts a cell, and the provider waits and
retries after a definite HTTP 429. Exhaustion beyond the bound ends the cell as ERROR (reported); nothing falls back to
Nebius. `--resume DIR` continues an interrupted batch from the same snapshot, running only the cells that never executed.

Codex-first policy: the default provider is the self-hosted Codex gateway (allowance, no USD). `--provider nebius` is
refused unless a batch approval is given explicitly: `--approve-usd TOTAL` (hard cap on the committed USD of the whole
batch, reserved per run before it starts) and `--max-calls N` (per-run call cap). A per-run USD cap alone does not
control a batch. Stop conditions: batch cap reached; three consecutive infrastructure errors; any transport-uncertain
operation (never replayed). Remaining cells are reported as not run.

Usage:
  run_evaluation.py [--provider codex|nebius] [--tasks id,id] [--systems baseline,attest] [--attempts 1] [--workers 2]
                    [--usd-cap 0.5] [--approve-usd TOTAL] [--max-calls N] [--max-turns 14] [--out DIR] [--label TEXT]
                    [--suite PATH] [--resume DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import attest  # noqa: E402
from attest import __version__  # noqa: E402
from attest.core.pipeline import Pipeline  # noqa: E402
from attest.core.provenance import attest_revision, guest_digests  # noqa: E402
from attest.core.sealed import sha256_text  # noqa: E402
from attest.core.task import TaskSpec  # noqa: E402
from attest.ledger import Ledger, utcnow  # noqa: E402
from attest.secrets import load_secret, project_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACCEPTED_VERDICTS = {"VERIFIED"}
INFRA_VERDICTS = {"ERROR", "HARNESS_ERROR"}
MAX_CONSECUTIVE_INFRA = 3
# Requests a cell needs on the Codex gateway, from the recorded dry runs (baseline 5 to 6; Attest 10 to 12 plus repair and
# arbitration calls). The harness waits for this much headroom before starting a cell so a run does not stall mid-way.
CALLS_PER_CELL = {"baseline": 6, "attest": 15}
SNAPSHOT_DIRNAME = "snapshot"


def log(message: str) -> None:
    print(f"[{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {message}", flush=True)


# ----------------------------------------------------------------------------- snapshot and provenance
def tree_digest(root: Path, patterns: tuple[str, ...] = ("*",)) -> dict:
    """sha256 over relative path and content of every regular file under root (sorted), skipping caches."""
    digest = hashlib.sha256()
    count = 0
    for path in sorted(p for p in Path(root).rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if not any(path.match(pattern) for pattern in patterns):
            continue
        digest.update(rel.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
        count += 1
    return {"digest": digest.hexdigest(), "files": count}


def make_snapshot(source_root: Path, dest: Path) -> dict:
    """Copy the code and the frozen tasks that a batch executes into `dest` and return their digests."""
    if dest.exists():
        raise FileExistsError(f"snapshot directory already exists: {dest}")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    shutil.copytree(source_root / "attest", dest / "attest", ignore=ignore)
    (dest / "scripts").mkdir()
    shutil.copy2(source_root / "scripts" / "run_evaluation.py", dest / "scripts" / "run_evaluation.py")
    # symlinks are copied as links (the python-semver checkout has docs symlinks that point outside tests/); a dangling
    # link is skipped by snapshot_repo and by tree_digest alike, so the frozen task digest is unaffected
    shutil.copytree(source_root / "examples", dest / "examples", ignore=ignore, symlinks=True)
    record = snapshot_digests(dest)
    record.update({"created_at_utc": utcnow(), "source_root": str(source_root), "snapshot_root": str(dest),
                   "working_tree_revision_at_launch": attest_revision(source_root / "attest")["digest"],
                   "source_git_commit": attest_revision(source_root / "attest")["git_commit"]})
    (dest / "SNAPSHOT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def snapshot_digests(root: Path) -> dict:
    return {"attest_revision": attest_revision(root / "attest"),
            "eval_script_sha256": hashlib.sha256((root / "scripts" / "run_evaluation.py").read_bytes()).hexdigest(),
            "examples": tree_digest(root / "examples")}


def runtime_provenance(snapshot_root: Path, source_root: Path | None) -> dict:
    """What this process actually executes: the imported package (must live in the snapshot), its digests and the guests."""
    package_dir = Path(attest.__file__).resolve().parent
    digests = snapshot_digests(snapshot_root)
    if package_dir != (snapshot_root / "attest").resolve():
        raise SystemExit(f"refusing to run: the imported attest package is {package_dir}, not the snapshot {snapshot_root / 'attest'}")
    source_commit = None
    try:
        source_commit = json.loads((snapshot_root / "SNAPSHOT.json").read_text(encoding="utf-8")).get("source_git_commit")
    except (OSError, json.JSONDecodeError):
        pass
    return {"fresh_process": True, "pid": os.getpid(), "snapshot_root": str(snapshot_root), "source_root": str(source_root) if source_root else None,
            "source_git_commit": source_commit,
            "attest_version": __version__, "attest_revision": digests["attest_revision"], "eval_script_sha256": digests["eval_script_sha256"],
            "examples_digest": digests["examples"], "guest_programs": guest_digests(),
            "python": sys.version.split()[0], "platform": platform.platform(),
            "note": "the batch executes the snapshot only; edits to the source tree during the batch cannot reach it and are reported"}


def revision_of(bundle: dict | None) -> str | None:
    return (((bundle or {}).get("provenance") or {}).get("attest_revision") or {}).get("digest")


def comparison_validity(rows: list[dict], registered: str | None, snapshot_intact: bool) -> dict:
    """Per task: valid only when every completed cell carries the registered revision and the snapshot was intact."""
    by_task: dict[str, dict] = {}
    for row in rows:
        entry = by_task.setdefault(row["task"], {"valid": True, "reasons": []})
        if row.get("status") != "completed":
            continue
        rev = row.get("revision_digest")
        if rev is None:
            entry["valid"] = False
            entry["reasons"].append(f"{row['system']} a{row['attempt']}: bundle records no revision")
        elif registered and rev != registered:
            entry["valid"] = False
            entry["reasons"].append(f"{row['system']} a{row['attempt']}: revision {rev[:12]} differs from the registered {registered[:12]}")
    if not snapshot_intact:
        for entry in by_task.values():
            entry["valid"] = False
            entry["reasons"].append("the source snapshot changed during the batch")
    return by_task


# ----------------------------------------------------------------------------- providers and pacing
def build_provider(name, ledger, usd_cap, max_calls, notify=None):
    if name == "codex":
        from attest.models.codex_gateway import CodexGateway
        return CodexGateway(load_secret("CODEX_API_KEY"), ledger, notify=notify)
    from attest.models.nebius_tokenfactory import NebiusTokenFactory
    return NebiusTokenFactory(load_secret("NEBIUS_API_KEY"), ledger, usd_cap=usd_cap, max_calls=max_calls)


def executor_for(ledger):
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
    return TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)


def codex_governor():
    """The process-wide governor for the Codex key, configured from the gateway's declared policy before the batch starts."""
    from attest.models.codex_gateway import CodexGateway
    client = CodexGateway(load_secret("CODEX_API_KEY"), Ledger())
    client.adopt_gateway_policy(force=True)
    log(f"codex pacing policy: {client.governor.policy_source}")
    return client.governor


class Budget:
    """Batch-level control shared by the workers: USD reservation against the approved total, consecutive
    infrastructure errors, and a stop flag set by any uncertain operation."""

    def __init__(self, approve_usd: float | None, per_run_cap: float, committed: float = 0.0):
        self.approve_usd = approve_usd
        self.per_run_cap = per_run_cap
        self.reserved = 0.0
        self.committed = committed
        self.peak_projected = committed
        self.consecutive_infra = 0
        self.stopped: str | None = None
        self.lock = threading.Lock()

    def try_reserve(self) -> str | None:
        """Return None when a run may start (reservation taken), otherwise the reason it may not."""
        with self.lock:
            if self.stopped:
                return self.stopped
            if self.approve_usd is not None:
                projected = self.committed + self.reserved + self.per_run_cap
                if projected > self.approve_usd + 1e-9:
                    self.stopped = (f"batch USD cap ${self.approve_usd:.2f} would be exceeded: ${self.committed:.4f} committed + "
                                    f"${self.reserved:.2f} reserved + ${self.per_run_cap:.2f} for this run = ${projected:.4f}")
                    return self.stopped
                self.reserved += self.per_run_cap
                self.peak_projected = max(self.peak_projected, projected)
            return None

    def settle(self, row: dict) -> None:
        with self.lock:
            if self.approve_usd is not None:
                self.reserved = max(0.0, self.reserved - self.per_run_cap)
                self.committed += float(row.get("cost_committed_usd") or row.get("cost_usd") or 0.0)
            if row.get("infra_error"):
                self.consecutive_infra += 1
                if self.consecutive_infra >= MAX_CONSECUTIVE_INFRA and not self.stopped:
                    self.stopped = f"stopped after {MAX_CONSECUTIVE_INFRA} consecutive infrastructure errors"
            else:
                self.consecutive_infra = 0
            if row.get("uncertain") and not self.stopped:
                self.stopped = "a transport-uncertain operation occurred; the batch stopped without replaying anything"

    def snapshot(self) -> dict:
        with self.lock:
            return {"approve_usd": self.approve_usd, "per_run_cap_usd": self.per_run_cap, "committed_usd": round(self.committed, 4),
                    "peak_projected_usd": round(self.peak_projected, 4), "stopped": self.stopped}


# ----------------------------------------------------------------------------- one cell
def one_system(cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root: Path) -> dict:
    task = TaskSpec.load(task_root / cell["task_path"])
    stripped = sorted(task.heldout_tests)
    task.heldout_tests = {}  # the system under test never sees the judge's suite
    heldout_src = (task_root / cell["heldout"]).read_text(encoding="utf-8")
    ledger = Ledger()
    provider = build_provider(provider_name, ledger, usd_cap, max_calls, notify=lambda m: log(f"[{cell['task']} {cell['system']}] {m}"))
    executor = executor_for(ledger)
    system = cell["system"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=out_dir, max_turns=max_turns,
                        tavily=None, profile_label=f"eval-{system}-a{cell['attempt']}", arbitrate=(system == "attest"),
                        run_id=f"{task.id}-{system}-a{cell['attempt']}-{stamp}")  # unique per cell even when cells start together
    t0 = time.monotonic()
    try:
        bundle = pipeline.run() if system == "attest" else pipeline.run_baseline()
    except Exception as error:  # noqa: BLE001 - the pipeline wrote its bundle (ERROR) before re-raising; the paid calls stay accounted for
        totals = ledger.totals()
        message = f"{type(error).__name__}: {str(error)[:200]}"
        return {**cell, "status": "completed", "verdict": "ERROR", "accepted": False, "held_out_correct": None, "judge_passed": None,
                "held_out_summary": "not judged: the run crashed", "cost_usd": totals.get("cost_usd"), "cost_committed_usd": totals.get("cost_usd_committed"),
                "uncertain_calls": totals.get("uncertain_unpriced_calls"), "model_calls": totals.get("model_calls"),
                "model_calls_failed": totals.get("model_calls_failed"), "sandbox_ops": totals.get("sandbox_operations"),
                "wall_s": round(time.monotonic() - t0, 1), "reasons": [message], "warnings": [], "gates": {}, "out_dir": str(pipeline.out_dir),
                "run_id": pipeline.run_id, "revision_digest": revision_of(pipeline.bundle), "arbitration": None, "error": message,
                "infra_error": True, "uncertain": "uncertain" in message.lower() or bool(totals.get("uncertain_unpriced_calls"))}
    wall = round(time.monotonic() - t0, 1)
    judge_error = None
    try:
        judge = pipeline.judge_heldout(heldout_src) if pipeline.checkpoint_uuid else {"correct": None, "summary_line": "no checkpoint; not judged"}
    except Exception as error:  # noqa: BLE001 - the verdict stands; the judge result is simply missing and the costs stay accounted for
        judge_error = f"{type(error).__name__}: {str(error)[:200]}"
        judge = {"correct": None, "summary_line": f"judge failed: {judge_error}"}
    totals = ledger.totals()  # after judging, so the judge's sandbox operation is included
    verdict = bundle["verdict"]["verdict"]
    accepted = (verdict in ACCEPTED_VERDICTS) if system == "attest" else bool(bundle["verdict"].get("finished"))
    judge_passed = judge.get("correct")
    if cell.get("ground_truth") == "unsatisfiable":
        # the contract cannot be met by any implementation (see CORRECTIONS.md of the 16 Oct evaluation): the judge suite
        # cannot establish correctness, so a shipped patch is never "correct" and holding (INFEASIBLE or NEEDS HUMAN) is right
        correct = False
    else:
        correct = judge_passed
    arb = bundle.get("arbitration")
    reasons = bundle["verdict"].get("reasons", [])
    uncertain = any("uncertain" in r for r in reasons) or bool(totals.get("uncertain_unpriced_calls")) or bool(judge_error and "uncertain" in judge_error.lower())
    roles = ((bundle.get("profile") or {}).get("provider") or {}).get("roles")
    return {**cell, "status": "completed", "verdict": verdict, "accepted": accepted, "held_out_correct": correct, "judge_passed": judge_passed,
            "held_out_summary": judge.get("summary_line"), "judge_evidence_class": judge.get("evidence_class"), "judge_error": judge_error,
            "judge_operation_uuid": judge.get("operation_uuid"), "heldout_stripped_from_task": stripped,
            "cost_usd": totals.get("cost_usd"), "cost_committed_usd": totals.get("cost_usd_committed"),
            "uncertain_calls": totals.get("uncertain_unpriced_calls"), "model_calls": totals.get("model_calls"),
            "model_calls_failed": totals.get("model_calls_failed"),  # provider refusals (for example an hourly limit) that shaped the verdict
            "rate_limited_calls": totals.get("rate_limited_calls"), "pacing_wait_ms": totals.get("pacing_wait_ms"),
            "sandbox_ops": totals.get("sandbox_operations"), "wall_s": wall, "turns": bundle["trajectory"]["turns"],
            "finished": bundle["trajectory"]["finished"], "reasons": reasons[:4], "warnings": bundle["verdict"].get("warnings", [])[:4],
            "gates": {k: {"ok": g.get("ok"), "evidence_class": g.get("evidence_class")} for k, g in (bundle.get("gates") or {}).items()},
            "out_dir": str(pipeline.out_dir), "run_id": bundle["run_id"], "roles": roles,
            "revision_digest": revision_of(bundle), "supervisor": ((bundle.get("provenance") or {}).get("supervisor") or {}).get("version"),
            "arbitration": ({"counts": arb["counts"], "cleared": arb["cleared"], "headline": arb["headline"]} if arb else None),
            "infra_error": verdict in INFRA_VERDICTS, "uncertain": uncertain}


def run_cell(cell, budget: Budget, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root: Path, governor=None) -> dict:
    blocked = budget.try_reserve()
    if blocked:
        return {**cell, "status": "not_run", "reason": blocked, "verdict": None, "accepted": False, "held_out_correct": None,
                "cost_usd": None, "cost_committed_usd": None, "wall_s": None, "infra_error": False, "uncertain": False}
    paced = 0.0
    try:
        if governor is not None:
            paced = governor.wait_for_headroom(CALLS_PER_CELL.get(cell["system"], 15), notify=lambda m: log(f"[{cell['task']} {cell['system']}] {m}"))
        row = one_system(cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root)
    except Exception as error:  # noqa: BLE001 - retain the failure as an attempt
        message = f"{type(error).__name__}: {str(error)[:200]}"
        row = {**cell, "status": "completed", "verdict": "HARNESS_ERROR", "accepted": False, "held_out_correct": None,
               "cost_usd": None, "cost_committed_usd": None, "wall_s": None, "infra_error": True,
               "uncertain": "uncertain" in message.lower(), "reasons": [message], "arbitration": None, "revision_digest": None}
    row["paced_wait_before_start_s"] = round(paced, 1)
    row["started_at_utc"] = row.get("started_at_utc") or utcnow()
    budget.settle(row)
    return row


def classify(row):
    """Confusion label against ground truth (held-out correctness)."""
    if row.get("status") == "not_run":
        return "not_run"
    correct = row.get("held_out_correct")
    if row.get("infra_error") or row.get("verdict") in INFRA_VERDICTS:
        return "infra_error"
    if correct is None:
        return "unknown"
    if row["accepted"] and correct:
        return "true_accept"
    if row["accepted"] and not correct:
        return "false_accept"
    if not row["accepted"] and correct:
        return "false_reject"
    return "true_reject"


def summarize(rows, systems, validity: dict | None = None):
    summary = {}
    invalid = {task for task, v in (validity or {}).items() if not v["valid"]}
    for system in systems:
        srows = [r for r in rows if r["system"] == system]
        done = [r for r in srows if r.get("status") == "completed"]
        conf = {k: sum(1 for r in srows if r["confusion"] == k)
                for k in ("true_accept", "false_accept", "false_reject", "true_reject", "infra_error", "unknown", "not_run")}
        costs = [r.get("cost_committed_usd") if r.get("cost_committed_usd") is not None else r.get("cost_usd") for r in done]
        costs = [c for c in costs if c is not None]
        walls = [r["wall_s"] for r in done if r.get("wall_s") is not None]
        needs_human = sum(1 for r in done if r.get("verdict") not in ("VERIFIED", "BASELINE") and not r.get("infra_error"))
        summary[system] = {"scheduled": len(srows), "completed": len(done), "not_run": conf["not_run"], "confusion": conf,
                           "shipped_broken_code": conf["false_accept"], "needs_human": needs_human,
                           "rate_limited_calls": sum(r.get("rate_limited_calls") or 0 for r in done),
                           "pacing_wait_s": round(sum((r.get("pacing_wait_ms") or 0) for r in done) / 1000 + sum(r.get("paced_wait_before_start_s") or 0 for r in srows), 1),
                           "cells_in_invalid_comparisons": sum(1 for r in srows if r["task"] in invalid),
                           "total_cost_committed_usd": round(sum(costs), 4), "mean_wall_s": round(sum(walls) / len(walls), 1) if walls else None}
    return summary


# ----------------------------------------------------------------------------- launcher (working tree) and batch (snapshot)
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="codex", choices=["codex", "nebius"])
    ap.add_argument("--tasks", default="", help="comma-separated task ids (default: all in the suite)")
    ap.add_argument("--systems", default="baseline,attest")
    ap.add_argument("--attempts", type=int, default=1, help="scheduled attempts per (task, system) cell; every one is reported")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--usd-cap", type=float, default=0.5, help="per-run USD cap (Nebius profile)")
    ap.add_argument("--approve-usd", type=float, default=None, help="REQUIRED for nebius: hard cap on the whole batch's committed USD")
    ap.add_argument("--max-calls", type=int, default=None, help="per-run model-call cap (required for nebius; default 20 there)")
    ap.add_argument("--max-turns", type=int, default=14)
    ap.add_argument("--out", default="", help="report directory (default: reports/attest-evaluation-<date>-<provider>[-label])")
    ap.add_argument("--label", default="", help="short label for the report directory and schedule")
    ap.add_argument("--suite", default="examples/eval/SUITE.json", help="suite file, relative to the project root")
    ap.add_argument("--resume", default="", help="continue the batch in this report directory: only cells never executed are run")
    ap.add_argument("--register-only", action="store_true", help="snapshot, pre-register the schedule and exit before any cell runs (proves the command)")
    ap.add_argument("--snapshot-root", default="", help=argparse.SUPPRESS)  # set by the launcher when re-executing from the snapshot
    ap.add_argument("--source-root", default="", help=argparse.SUPPRESS)
    return ap.parse_args(argv)


def launch(args, argv: list[str]) -> int:
    """Working-tree entry: make (or verify) the snapshot and re-execute this script from it in a fresh process."""
    if args.provider == "nebius" and not args.register_only:
        if args.approve_usd is None or args.max_calls is None and args.approve_usd is None:
            print("refusing: --provider nebius needs an explicit batch approval: --approve-usd TOTAL and --max-calls N", file=sys.stderr)
            return 2
    if args.resume:
        out_root = Path(args.resume).resolve()
        snapshot_root = out_root / SNAPSHOT_DIRNAME
        if not (out_root / "schedule.json").is_file() or not (snapshot_root / "SNAPSHOT.json").is_file():
            print(f"refusing: {out_root} has no schedule.json or no snapshot to resume from", file=sys.stderr)
            return 2
        registered = json.loads((snapshot_root / "SNAPSHOT.json").read_text(encoding="utf-8"))
        now = snapshot_digests(snapshot_root)
        if now["attest_revision"]["digest"] != registered["attest_revision"]["digest"] or now["eval_script_sha256"] != registered["eval_script_sha256"] \
                or now["examples"]["digest"] != registered["examples"]["digest"]:
            print("refusing: the snapshot in this report directory no longer matches the digests registered at launch; a resumed batch must run the same code", file=sys.stderr)
            return 2
        log(f"resuming {out_root} from its snapshot (revision {registered['attest_revision']['digest'][:12]})")
    else:
        day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        out_root = (ROOT / (args.out or f"reports/attest-evaluation-{day}-{args.provider}" + (f"-{args.label}" if args.label else ""))).resolve()
        if (out_root / "schedule.json").exists():
            print(f"refusing: {out_root / 'schedule.json'} already exists; a pre-registered schedule is never overwritten. Use --label, --out or --resume.",
                  file=sys.stderr)
            return 2
        out_root.mkdir(parents=True, exist_ok=True)
        snapshot_root = out_root / SNAPSHOT_DIRNAME
        record = make_snapshot(ROOT, snapshot_root)
        log(f"snapshot {snapshot_root}: attest revision {record['attest_revision']['digest'][:12]} ({record['attest_revision']['files']} sources), "
            f"eval script {record['eval_script_sha256'][:12]}, examples {record['examples']['digest'][:12]} ({record['examples']['files']} files)")
    forwarded = [a for a in argv if a not in ("--resume",) and not a.startswith("--resume=")]
    # drop the value of a separated --resume
    if "--resume" in argv:
        index = argv.index("--resume")
        forwarded = argv[:index] + argv[index + 2:]
    cmd = [sys.executable, str(snapshot_root / "scripts" / "run_evaluation.py"), *forwarded, "--out", str(out_root),
           "--snapshot-root", str(snapshot_root), "--source-root", str(ROOT)]
    if args.resume:
        cmd += ["--resume", str(out_root)]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)  # the snapshot process must import only its own copy
    log("fresh process from the snapshot: " + " ".join(cmd[1:3]) + " ...")
    return subprocess.call(cmd, cwd=str(snapshot_root), env=env)


def run_batch(args) -> int:
    snapshot_root = Path(args.snapshot_root).resolve()
    source_root = Path(args.source_root).resolve() if args.source_root else None
    provenance = runtime_provenance(snapshot_root, source_root)
    out_root = Path(args.out).resolve()
    if args.provider == "nebius" and args.max_calls is None:
        args.max_calls = 20
    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    runs_dir = out_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    governor = codex_governor() if args.provider == "codex" else None
    resumed_at = None
    previous_rows: list[dict] = []

    if args.resume:
        schedule = json.loads((out_root / "schedule.json").read_text(encoding="utf-8"))
        existing = json.loads((out_root / "evaluation.json").read_text(encoding="utf-8")) if (out_root / "evaluation.json").is_file() else {"rows": []}
        previous_rows = [r for r in existing.get("rows", []) if r.get("status") == "completed"]
        done_indices = {r["scheduled_index"] for r in previous_rows}
        cells = [c for c in schedule["cells"] if c["scheduled_index"] not in done_indices]
        resumed_at = utcnow()
        schedule.setdefault("resumptions", []).append({"at_utc": resumed_at, "cells": [c["scheduled_index"] for c in cells],
                                                       "provenance_check": "snapshot digests verified by the launcher"})
        (out_root / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
        committed = sum(float(r.get("cost_committed_usd") or r.get("cost_usd") or 0.0) for r in previous_rows)
        log(f"resuming: {len(previous_rows)} completed cells kept, {len(cells)} cells to run")
    else:
        committed = 0.0
        suite = json.loads((snapshot_root / args.suite).read_text(encoding="utf-8"))["tasks"]
        if args.tasks:
            wanted = set(args.tasks.split(","))
            suite = [t for t in suite if t["id"] in wanted]
        cells = []
        for entry in suite:
            for system in systems:
                for attempt in range(1, args.attempts + 1):
                    cells.append({"scheduled_index": len(cells), "task": entry["id"], "task_path": entry["path"], "heldout": entry["heldout"],
                                  "ground_truth": entry.get("ground_truth", "held_out_suite"), "kind": entry.get("kind"),
                                  "heldout_sha256": sha256_text((snapshot_root / entry["heldout"]).read_text(encoding="utf-8")),
                                  "task_spec_sha256": TaskSpec.load(snapshot_root / entry["path"]).frozen(
                                      __import__("attest.core.workspace", fromlist=["snapshot_repo"]).snapshot_repo(TaskSpec.load(snapshot_root / entry["path"]).repo_dir))["spec_sha256"],
                                  "system": system, "attempt": attempt})
        probe_ledger = Ledger()
        try:
            provider_desc = build_provider(args.provider, probe_ledger, args.usd_cap, args.max_calls).describe()
        except Exception as error:  # noqa: BLE001 - registering a schedule must work without credentials; a real run needs them
            if not getattr(args, "register_only", False):
                raise
            provider_desc = {"provider": args.provider, "note": f"provider not constructed while registering only ({type(error).__name__})"}
        schedule = {"label": args.label, "registered_at_utc": utcnow(), "attest_version": __version__, "provider": args.provider,
                    "provider_detail": provider_desc, "per_run_usd_cap": args.usd_cap, "approve_usd": args.approve_usd,
                    "max_calls_per_run": args.max_calls, "max_turns": args.max_turns, "workers": args.workers, "attempts_per_cell": args.attempts,
                    "systems": systems, "tasks": [t["id"] for t in suite], "suite": args.suite, "heldout_stripped_from_system_under_test": True,
                    "provenance": provenance,
                    "pacing": ({"calls_per_cell_reserved": CALLS_PER_CELL, **governor.snapshot()} if governor else None),
                    "stop_conditions": ["batch USD cap reached (reservation of the per-run cap before each run)",
                                        f"{MAX_CONSECUTIVE_INFRA} consecutive infrastructure errors", "any transport-uncertain operation (never replayed)",
                                        "Codex pacing: a cell whose bounded wait for the hourly budget is exceeded ends as ERROR (reported); no fallback"],
                    "definitions": {"accepted": "attest: verdict VERIFIED; baseline: implementer finished",
                                    "correct": "existing suite and held-out suite pass on the final patch in a fresh branch (judge); for a task whose ground_truth is "
                                               "'unsatisfiable' no patch counts as correct and a hold (INFEASIBLE or NEEDS HUMAN) is the right outcome",
                                    "infra_error": "verdict ERROR or a harness exception", "not_run": "scheduled but never executed; reason recorded",
                                    "comparison_invalid": "a task whose cells did not all run the registered revision, or whose snapshot changed during the batch"},
                    "cells": cells}
        schedule["register_only"] = bool(getattr(args, "register_only", False))
        (out_root / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
        log(f"pre-registered {len(cells)} cells ({len(suite)} tasks x {systems} x {args.attempts} attempt(s)) on provider={args.provider}; "
            f"per-run cap ${args.usd_cap}, batch approval {args.approve_usd}, max calls {args.max_calls}; schedule -> {out_root / 'schedule.json'}")
        if getattr(args, "register_only", False):
            log("register-only: no cell was started; the schedule and the snapshot digests are the record of this invocation")
            return 0

    registered_revision = ((schedule.get("provenance") or {}).get("attest_revision") or {}).get("digest")
    if registered_revision and registered_revision != provenance["attest_revision"]["digest"]:
        print(f"refusing: this process runs revision {provenance['attest_revision']['digest'][:12]} but the schedule registered {registered_revision[:12]}", file=sys.stderr)
        return 2

    budget = Budget(args.approve_usd if args.provider == "nebius" else None, args.usd_cap, committed=committed)
    rows: list[dict] = list(previous_rows)

    def persist(complete: bool, finished: str | None = None):
        snapshot_now = snapshot_digests(snapshot_root)
        snapshot_intact = snapshot_now["attest_revision"]["digest"] == provenance["attest_revision"]["digest"] and \
            snapshot_now["eval_script_sha256"] == provenance["eval_script_sha256"] and snapshot_now["examples"]["digest"] == provenance["examples_digest"]["digest"]
        working_tree = attest_revision(source_root / "attest")["digest"] if source_root and (source_root / "attest").is_dir() else None
        ordered = sorted(rows, key=lambda r: r["scheduled_index"])
        validity = comparison_validity(ordered, registered_revision, snapshot_intact)
        report = {"schedule": schedule, "finished_at_utc": finished, "complete": complete, "budget": budget.snapshot(),
                  "note": "every scheduled cell is reported once; there is no merge or best-of selection",
                  "provenance_check": {"registered_revision": registered_revision, "snapshot_intact_at_end": snapshot_intact,
                                       "working_tree_revision_now": working_tree,
                                       "working_tree_changed_since_launch": (working_tree != provenance["attest_revision"]["digest"]) if working_tree else None,
                                       "comparisons": validity, "invalid_tasks": sorted(t for t, v in validity.items() if not v["valid"])},
                  "pacing": governor.snapshot() if governor else None, "resumed_at_utc": resumed_at,
                  "rows": ordered, "summary": summarize(ordered, systems, validity)}
        (out_root / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_cell, cell, budget, args.provider, args.usd_cap, args.max_calls, runs_dir, args.max_turns, snapshot_root, governor)
                   for cell in cells]
        for fut in futures:
            row = fut.result()
            row["confusion"] = classify(row)
            rows.append(row)
            print(f"  [{row['scheduled_index']:>2}] {row['task']:<28} {row['system']:<9} a{row['attempt']} {row.get('status'):<9} verdict={str(row.get('verdict')):<12} "
                  f"correct={row.get('held_out_correct')!s:<5} -> {row['confusion']:<12} ${row.get('cost_committed_usd')} {row.get('wall_s')}s "
                  f"rev={(row.get('revision_digest') or '-')[:8]} paced={row.get('paced_wait_before_start_s')}s"
                  + (f"  ({row.get('reason')})" if row.get("status") == "not_run" else ""), flush=True)
            persist(complete=False)  # an interrupted batch still reports what it scheduled and ran

    report = persist(complete=True, finished=utcnow())
    print("\n=== SUMMARY (all scheduled cells) ===")
    print(json.dumps(report["summary"], indent=2))
    print("budget:", json.dumps(report["budget"]))
    print("provenance:", json.dumps({k: v for k, v in report["provenance_check"].items() if k != "comparisons"}))
    if governor:
        print("pacing:", json.dumps({k: v for k, v in report["pacing"].items() if k != "waits"}), f"waits={len(report['pacing']['waits'])}")
    print("\nwrote", out_root / "evaluation.json")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(argv)
    if args.provider == "nebius" and args.approve_usd is None and not args.snapshot_root and not args.register_only:
        print("refusing: --provider nebius needs an explicit batch approval: --approve-usd TOTAL (hard cap for the whole batch) and --max-calls N. "
              "Nothing was run.", file=sys.stderr)
        return 2
    if args.snapshot_root:
        return run_batch(args)
    return launch(args, argv)


if __name__ == "__main__":
    sys.exit(main())
