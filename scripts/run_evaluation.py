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
batch, reserved per run before it starts) and `--max-calls N` (per-run call cap; default 22 for nebius, recorded in the
schedule). A per-run USD cap alone does not control a batch. Stop conditions: batch cap reached; three consecutive
infrastructure errors; any transport-uncertain operation (never replayed). Remaining cells are reported as not run.

Accounting repairs (audit of 19 Oct 2026): a resumed batch restores provider, caps, workers, attempts, systems and the approved
total from schedule.json and refuses a conflicting command line (AC-07); every row records the profile it executed and a task
whose cells ran different profiles is an invalid comparison. On every process start the batch's starting committed total is
rebuilt from disk: every completed row once plus every run directory no row owns once, whether interrupted mid-run (journal)
or finished without a persisted row (ledger totals) (AC-01, AC-02).

Effective provider profile (review finding R5-06, 19 Oct 2026): the provider name and the harness-level limits do not pin the
comparison; the models answering each role, the reasoning effort, the sampling parameters and the per-run caps do, and several of
them come from the environment (ATTEST_NEBIUS_ROLES, ATTEST_NEBIUS_REASONING_EFFORT, ATTEST_NEBIUS_THINKING_FLAG, ATTEST_CODEX_ROLES).
`provider_profile` selects the stable keys of `provider.describe()`; the profile is registered in schedule.json, every completed row
carries the profile its bundle recorded, a row whose profile differs from the registration invalidates its task's comparison, and a
process that would build a different provider (on resume, or at the start of a cell) refuses before any paid call.

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


def _same_setting(given, registered) -> bool:
    """Equality for registered settings: numbers compare with a tolerance (floats re-parsed from a command line), the rest exactly."""
    numbers = (int, float)
    if isinstance(given, numbers) and not isinstance(given, bool) and isinstance(registered, numbers) and not isinstance(registered, bool):
        return abs(float(given) - float(registered)) <= 1e-9
    return given == registered


# row field -> (schedule key, label): the execution profile every completed row records (audit finding AC-07, 19 Oct 2026), so a
# cell that ran another provider or other limits than the registered ones invalidates its task's comparison
EXECUTION_PROFILE = {"executed_provider": ("provider", "provider"), "usd_cap": ("per_run_usd_cap", "per-run USD cap"),
                     "max_calls": ("max_calls_per_run", "per-run call cap"), "max_turns": ("max_turns", "turn cap")}

# The keys of a provider description that define the comparison a batch makes (review finding R5-06): which model answers each role,
# how it reasons and samples, and the per-run limits. Everything else in describe() is state (halted, journal counters) or policy prose.
PROFILE_KEYS = {"nebius_tokenfactory": ("provider", "roles", "reasoning_effort", "temperature", "max_tokens", "usd_cap", "max_calls",
                                        "thinking_roles", "send_thinking_flag"),
                "codex_gateway": ("provider", "roles", "base_url_sha256")}
PROFILE_ENVIRONMENT = ("ATTEST_NEBIUS_ROLES", "ATTEST_NEBIUS_REASONING_EFFORT", "ATTEST_NEBIUS_THINKING_FLAG", "ATTEST_CODEX_ROLES")


def _role_text(selection) -> str | None:
    """One spelling for a role's selection: the Token Factory maps a role to a model id, the gateway to (model, effort)."""
    if isinstance(selection, (list, tuple)):
        model = selection[0] if selection else None
        effort = selection[1] if len(selection) > 1 else None
        if model is None:
            return None
        return f"{model}:{effort}" if effort else str(model)
    return None if selection is None else str(selection)


def provider_profile(description: dict | None) -> dict:
    """The effective provider configuration a batch compares: the stable keys of `provider.describe()` for the provider named in it
    (an unknown provider contributes its name only). Per-role maps are spelled `role -> model` (Token Factory) or `role ->
    model:effort` (gateway); lists are plain lists, so the profile survives the schedule's JSON round trip unchanged."""
    desc = description or {}
    name = desc.get("provider")
    profile = {}
    for key in PROFILE_KEYS.get(name, ("provider",)):
        value = desc.get(key)
        if key == "roles" and isinstance(value, dict):
            value = {role: _role_text(selection) for role, selection in sorted(value.items())}
        elif isinstance(value, tuple):
            value = list(value)
        profile[key] = value
    return profile


def profile_differences(registered: dict | None, actual: dict | None) -> list[str]:
    """Every key (and, inside a per-role map, every role) whose actual value differs from the registered one, named."""
    registered, actual = registered or {}, actual or {}
    differences = []
    for key in sorted(set(registered) | set(actual)):
        before, now = registered.get(key), actual.get(key)
        if isinstance(before, dict) or isinstance(now, dict):
            before, now = before or {}, now or {}
            for sub in sorted(set(before) | set(now)):
                if not _same_setting(before.get(sub), now.get(sub)):
                    differences.append(f"{key}.{sub} {now.get(sub)!r} differs from the registered {before.get(sub)!r}")
        elif not _same_setting(before, now):
            differences.append(f"{key} {now!r} differs from the registered {before!r}")
    return differences


def profile_refusal(out_root: Path, differences: list[str]) -> str:
    return (f"refusing: the provider this process builds differs from the profile registered in {out_root / 'schedule.json'}: " + "; ".join(differences) +
            ". A resumed batch runs the registered models, reasoning effort, sampling and per-run limits or not at all; remove the environment "
            f"override ({', '.join(PROFILE_ENVIRONMENT)}) or register a new evaluation. No cell was constructed or run.")


def comparison_validity(rows: list[dict], registered: str | None, snapshot_intact: bool, schedule: dict | None = None) -> dict:
    """Per task: valid only when every completed cell carries the registered revision, ran the registered provider and limits and the
    registered provider profile (when `schedule` is given; rows written before 19 Oct 2026 recorded no execution profile, rows of
    schedules registered before the profile freeze no provider profile, and neither is judged on it) and the snapshot was intact."""
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
        for field, (key, label) in EXECUTION_PROFILE.items():
            if not schedule or field not in row or key not in schedule:
                continue
            if not _same_setting(row[field], schedule[key]):
                entry["valid"] = False
                entry["reasons"].append(f"{row['system']} a{row['attempt']}: {label} {row[field]!r} differs from the registered {schedule[key]!r}")
        if schedule and schedule.get("provider_profile") is not None and "provider_profile" in row:
            drift = profile_differences(schedule["provider_profile"], row["provider_profile"])
            if drift:
                entry["valid"] = False
                entry["reasons"].append(f"{row['system']} a{row['attempt']}: provider profile differs from the registered one: " + "; ".join(drift))
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
def one_system(cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root: Path, registered_profile: dict | None = None) -> dict:
    task = TaskSpec.load(task_root / cell["task_path"])
    stripped = sorted(task.heldout_tests)
    task.heldout_tests = {}  # the system under test never sees the judge's suite
    heldout_src = (task_root / cell["heldout"]).read_text(encoding="utf-8")
    ledger = Ledger()
    provider = build_provider(provider_name, ledger, usd_cap, max_calls, notify=lambda m: log(f"[{cell['task']} {cell['system']}] {m}"))
    actual_profile = provider_profile(provider.describe())
    if registered_profile is not None:
        # the provider actually built for this cell (code, command line and environment) must be the registered one (R5-06): a
        # drifted cell is reported as never run, before any executor, run directory or paid call exists
        drift = profile_differences(registered_profile, actual_profile)
        if drift:
            return {**cell, "status": "not_run", "verdict": None, "accepted": False, "held_out_correct": None, "cost_usd": None, "cost_committed_usd": None,
                    "wall_s": None, "infra_error": False, "uncertain": False, "provider_profile": actual_profile,
                    "reason": "the provider built for this cell differs from the registered profile (an environment override such as "
                              + " or ".join(PROFILE_ENVIRONMENT[:2]) + "?): " + "; ".join(drift)}
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
                "provider_profile": provider_profile(((pipeline.bundle or {}).get("profile") or {}).get("provider")),
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
    recorded_profile = provider_profile((bundle.get("profile") or {}).get("provider"))  # what the bundle says ran, not what we built
    candidate = bundle.get("candidate") or {}
    return {**cell, "status": "completed", "verdict": verdict, "accepted": accepted, "held_out_correct": correct, "judge_passed": judge_passed,
            "changed_paths": len(candidate.get("changed_paths") or []) + len(candidate.get("deleted_paths") or []),
            "held_out_summary": judge.get("summary_line"), "judge_evidence_class": judge.get("evidence_class"), "judge_error": judge_error,
            "judge_operation_uuid": judge.get("operation_uuid"), "heldout_stripped_from_task": stripped,
            "cost_usd": totals.get("cost_usd"), "cost_committed_usd": totals.get("cost_usd_committed"),
            "uncertain_calls": totals.get("uncertain_unpriced_calls"), "model_calls": totals.get("model_calls"),
            "model_calls_failed": totals.get("model_calls_failed"),  # provider refusals (for example an hourly limit) that shaped the verdict
            "rate_limited_calls": totals.get("rate_limited_calls"), "pacing_wait_ms": totals.get("pacing_wait_ms"),
            "sandbox_ops": totals.get("sandbox_operations"), "wall_s": wall, "turns": bundle["trajectory"]["turns"],
            "finished": bundle["trajectory"]["finished"], "reasons": reasons[:4], "warnings": bundle["verdict"].get("warnings", [])[:4],
            "gates": {k: {"ok": g.get("ok"), "evidence_class": g.get("evidence_class")} for k, g in (bundle.get("gates") or {}).items()},
            "out_dir": str(pipeline.out_dir), "run_id": bundle["run_id"], "roles": roles, "provider_profile": recorded_profile,
            "revision_digest": revision_of(bundle), "supervisor": ((bundle.get("provenance") or {}).get("supervisor") or {}).get("version"),
            "arbitration": ({"counts": arb["counts"], "cleared": arb["cleared"], "headline": arb["headline"]} if arb else None),
            "infra_error": verdict in INFRA_VERDICTS, "uncertain": uncertain}


def run_cell(cell, budget: Budget, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root: Path, governor=None,
             registered_profile: dict | None = None) -> dict:
    # An operator stops a batch cleanly by creating <report dir>/STOP: cells not yet started are reported as not run with that
    # reason, cells in flight finish and write their ledgers, and the batch can be resumed later with --resume.
    stop_file = Path(out_dir).parent / "STOP"
    if stop_file.exists():
        return {**cell, "status": "not_run", "reason": f"stopped by the operator ({stop_file.name} file present)", "verdict": None, "accepted": False,
                "held_out_correct": None, "cost_usd": None, "cost_committed_usd": None, "wall_s": None, "infra_error": False, "uncertain": False}
    blocked = budget.try_reserve()
    if blocked:
        return {**cell, "status": "not_run", "reason": blocked, "verdict": None, "accepted": False, "held_out_correct": None,
                "cost_usd": None, "cost_committed_usd": None, "wall_s": None, "infra_error": False, "uncertain": False}
    paced = 0.0
    try:
        if governor is not None:
            paced = governor.wait_for_headroom(CALLS_PER_CELL.get(cell["system"], 15), notify=lambda m: log(f"[{cell['task']} {cell['system']}] {m}"))
        row = one_system(cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root, registered_profile=registered_profile)
    except Exception as error:  # noqa: BLE001 - retain the failure as an attempt
        message = f"{type(error).__name__}: {str(error)[:200]}"
        row = {**cell, "status": "completed", "verdict": "HARNESS_ERROR", "accepted": False, "held_out_correct": None,
               "cost_usd": None, "cost_committed_usd": None, "wall_s": None, "infra_error": True,
               "uncertain": "uncertain" in message.lower(), "reasons": [message], "arbitration": None, "revision_digest": None}
    row["paced_wait_before_start_s"] = round(paced, 1)
    row["started_at_utc"] = row.get("started_at_utc") or utcnow()
    # the execution profile of this attempt, compared with the registered schedule by comparison_validity (AC-07)
    row["executed_provider"] = provider_name if row.get("status") == "completed" else None
    row["usd_cap"], row["max_calls"], row["max_turns"] = usd_cap, max_calls, max_turns
    budget.settle(row)
    return row


# ----------------------------------------------------------------------------- run directories no persisted row owns
SPEND_FIELDS = ("cost_usd", "cost_usd_committed", "model_calls", "open_reservations", "open_reserved_usd", "uncertain_unpriced_calls")


def run_identity(path) -> str:
    """One spelling for a run directory, so a row and a directory listing agree whatever path form each used."""
    return str(Path(path).resolve())


def _totals_in(path: Path, *keys: str) -> dict:
    """The ledger totals object stored in a JSON file (`ledger.json` holds it under "totals", a bundle under "ledger"/"totals")."""
    try:
        node = json.loads(path.read_text(encoding="utf-8"))
        for key in keys:
            node = (node or {}).get(key)
        return node if isinstance(node, dict) else {}
    except (OSError, json.JSONDecodeError, AttributeError):
        return {}


def recover_spend(run_dir: Path) -> dict | None:
    """The spend recorded in a run directory nobody reported, from the most complete record it holds: `ledger.json` (the totals
    Pipeline.finish wrote), else the journal `ledger.jsonl` (reservations before each request, call records after), else the
    bundle's own ledger totals. When both the totals and the journal are readable the higher committed figure is kept, so a
    difference between them can only raise the bound. None when the directory holds no record at all."""
    from attest.ledger import JOURNAL_FILE, read_journal
    candidates = []
    totals = _totals_in(run_dir / "ledger.json", "totals")
    if totals.get("cost_usd_committed") is not None:
        candidates.append(("ledger.json", totals))
    journal = read_journal(run_dir / JOURNAL_FILE)
    if journal is not None and journal.get("cost_usd_committed") is not None:
        candidates.append((JOURNAL_FILE, journal))
    if not candidates:
        totals = _totals_in(run_dir / "proof_bundle.json", "ledger", "totals")
        if totals.get("cost_usd_committed") is not None:
            candidates.append(("proof_bundle.json", totals))
    if not candidates:
        return None
    source, record = max(candidates, key=lambda item: float(item[1].get("cost_usd_committed") or 0.0))
    return {"source": source, **{key: record.get(key) for key in SPEND_FIELDS}}


def interrupted_cells(runs_dir: Path, rows: list[dict], already: list[dict], per_run_cap: float | None = None) -> list[dict]:
    """Every run directory under `runs_dir` that no persisted row owns (by run id or by normalised path), each listed once with the
    committed USD recovered from its own records. A directory without a bundle was interrupted mid-run and its journal is read
    back; a directory WITH a bundle that no row owns is finished but unreported (the process died between Pipeline.finish and the
    report write, or a later future finished while the main thread still waited on an earlier one) and its ledger totals are read
    back. The caller adds every entry to the batch's starting total on EVERY process start (audit findings AC-01 and AC-02);
    `already` (the entries an earlier resumption listed) only supplies the time an entry was first seen, never a reason to leave
    its cost out. A finished bundle with no readable record counts at `per_run_cap` when one is given (the console's policy for
    an unreadable run), otherwise it is listed with no figure and marked as not included."""
    owned_ids = {r.get("run_id") for r in rows if r.get("run_id")}
    owned_paths = {run_identity(r["out_dir"]) for r in rows if r.get("out_dir")}
    seen_before: dict[str, dict] = {}
    for item in already or []:
        for key in (item.get("run_id"), run_identity(item["out_dir"]) if item.get("out_dir") else None):
            if key:
                seen_before[key] = item
    found, listed = [], set()
    for run_dir in sorted(p for p in Path(runs_dir).iterdir() if p.is_dir()) if Path(runs_dir).is_dir() else []:
        identity = run_identity(run_dir)
        if run_dir.name in owned_ids or identity in owned_paths or identity in listed:
            continue
        finished = (run_dir / "proof_bundle.json").is_file()
        record = recover_spend(run_dir)
        if record is None and not finished:
            continue  # neither journal nor bundle: the process died before the first reservation, nothing was spent here
        earlier = seen_before.get(run_dir.name) or seen_before.get(identity) or {}
        if record is not None:
            committed, source = record["cost_usd_committed"], record["source"]
        elif per_run_cap is not None:
            committed, source = per_run_cap, "per_run_cap (no ledger record readable; the cap is the conservative bound)"
        else:
            committed, source = None, None
        entry = {"out_dir": str(run_dir), "run_id": run_dir.name, "kind": "finished_unreported" if finished else "interrupted",
                 "source": source, "cost_usd_committed": committed, "included_in_batch_total": committed is not None,
                 **{key: (record or {}).get(key) for key in SPEND_FIELDS if key != "cost_usd_committed"},
                 "first_listed_at_utc": earlier.get("first_listed_at_utc") or utcnow(), "listed_by_earlier_resumption": bool(earlier),
                 # kept for readers of earlier reports: it meant "left out of this process's total because an earlier process counted
                 # it", which no longer happens (every process rebuilds the total from disk), so it is always False
                 "counted_before": False}
        if earlier.get("cost_usd_committed") is not None and committed is not None and abs(float(earlier["cost_usd_committed"]) - float(committed)) > 1e-9:
            entry["previously_reported_usd"] = earlier["cost_usd_committed"]
        listed.add(identity)
        found.append(entry)
    return found


def classify(row):
    """Confusion label against ground truth (held-out correctness). A cell that produced no patch at all (Attest's NO CHANGE,
    or a baseline that neither finished nor changed a file) is `no_patch`: an unfinished task, never a correct rejection. A hold
    without a patch (INFEASIBLE, or NEEDS HUMAN with no patch and an unfinished implementer) is a refusal of the task: right on an
    unsatisfiable task, a `false_refusal` on one whose held-out suite is satisfiable."""
    if row.get("status") == "not_run":
        return "not_run"
    correct = row.get("held_out_correct")
    if row.get("infra_error") or row.get("verdict") in INFRA_VERDICTS:
        return "infra_error"
    if row.get("verdict") == "NO CHANGE" or (row.get("system") == "baseline" and not row.get("finished") and row.get("changed_paths") == 0):
        return "no_patch"
    if row.get("verdict") == "INFEASIBLE" or (row.get("verdict") == "NEEDS HUMAN" and row.get("changed_paths") == 0 and not row.get("finished")):
        # no patch exists, so the judge's result describes the unmodified repository, not a rejection: the refusal (INFEASIBLE, or a
        # NEEDS HUMAN hold that produced no patch) is right only when the task itself is unsatisfiable; holding a task whose held-out
        # suite can be satisfied is a wrong refusal. A NEEDS HUMAN hold WITH a patch is judged on that patch below.
        return "true_reject" if row.get("ground_truth") == "unsatisfiable" else "false_refusal"
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
                for k in ("true_accept", "false_accept", "false_reject", "true_reject", "false_refusal", "no_patch", "infra_error", "unknown", "not_run")}
        costs = [r.get("cost_committed_usd") if r.get("cost_committed_usd") is not None else r.get("cost_usd") for r in done]
        costs = [c for c in costs if c is not None]
        walls = [r["wall_s"] for r in done if r.get("wall_s") is not None]
        needs_human = sum(1 for r in done if r.get("verdict") not in ("VERIFIED", "BASELINE", "NO CHANGE") and not r.get("infra_error"))
        summary[system] = {"scheduled": len(srows), "completed": len(done), "not_run": conf["not_run"], "confusion": conf,
                           "shipped_broken_code": conf["false_accept"], "needs_human": needs_human, "no_patch": conf["no_patch"],
                           "rate_limited_calls": sum(r.get("rate_limited_calls") or 0 for r in done),
                           "pacing_wait_s": round(sum((r.get("pacing_wait_ms") or 0) for r in done) / 1000 + sum(r.get("paced_wait_before_start_s") or 0 for r in srows), 1),
                           "cells_in_invalid_comparisons": sum(1 for r in srows if r["task"] in invalid),
                           "total_cost_committed_usd": round(sum(costs), 4), "mean_wall_s": round(sum(walls) / len(walls), 1) if walls else None}
    return summary


# ----------------------------------------------------------------------------- launcher (working tree) and batch (snapshot)
# The parser leaves the registered settings unset (None) so that "not given" is distinguishable from "given": a resumed batch
# restores them from its schedule.json and refuses a conflicting command-line value (audit finding AC-07, 19 Oct 2026); the
# harness's own defaults are applied afterwards by apply_defaults.
DEFAULTS = {"provider": "codex", "workers": 2, "usd_cap": 0.5, "max_turns": 14, "attempts": 1, "systems": "baseline,attest"}
NEBIUS_DEFAULT_MAX_CALLS = 22  # per-run call cap of the Nebius profile when --max-calls is not given (recorded in schedule.json)
# command-line flag, argparse attribute, schedule.json key of every setting a batch is registered with
REGISTERED = (("--provider", "provider", "provider"), ("--usd-cap", "usd_cap", "per_run_usd_cap"), ("--approve-usd", "approve_usd", "approve_usd"),
              ("--max-calls", "max_calls", "max_calls_per_run"), ("--max-turns", "max_turns", "max_turns"), ("--workers", "workers", "workers"),
              ("--attempts", "attempts", "attempts_per_cell"), ("--systems", "systems", "systems"))


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default=None, choices=["codex", "nebius"], help="default codex; a resumed batch restores its registered provider")
    ap.add_argument("--tasks", default="", help="comma-separated task ids (default: all in the suite)")
    ap.add_argument("--systems", default=None, help="default baseline,attest")
    ap.add_argument("--attempts", type=int, default=None, help="scheduled attempts per (task, system) cell (default 1); every one is reported")
    ap.add_argument("--workers", type=int, default=None, help="default 2")
    ap.add_argument("--usd-cap", type=float, default=None, help="per-run USD cap (Nebius profile; default 0.5)")
    ap.add_argument("--approve-usd", type=float, default=None, help="REQUIRED for nebius: hard cap on the whole batch's committed USD")
    ap.add_argument("--max-calls", type=int, default=None, help=f"per-run model-call cap (nebius: default {NEBIUS_DEFAULT_MAX_CALLS}, recorded in the schedule)")
    ap.add_argument("--max-turns", type=int, default=None, help="default 14")
    ap.add_argument("--out", default="", help="report directory (default: reports/attest-evaluation-<date>-<provider>[-label])")
    ap.add_argument("--label", default="", help="short label for the report directory and schedule")
    ap.add_argument("--suite", default="examples/eval/SUITE.json", help="suite file, relative to the project root")
    ap.add_argument("--resume", default="", help="continue the batch in this report directory: only cells never executed are run")
    ap.add_argument("--register-only", action="store_true", help="snapshot, pre-register the schedule and exit before any cell runs (proves the command)")
    ap.add_argument("--snapshot-root", default="", help=argparse.SUPPRESS)  # set by the launcher when re-executing from the snapshot
    ap.add_argument("--source-root", default="", help=argparse.SUPPRESS)
    return ap.parse_args(argv)


def _systems_text(value) -> str:
    items = value if isinstance(value, list) else str(value).split(",")
    return ",".join(s.strip() for s in items if s and s.strip())


def restore_registered(args, schedule: dict) -> list[str]:
    """Fill every registered setting the command line left unset from the schedule, and return the conflicts: settings the command
    line gave explicitly with a value that differs from the registration. A resumed batch runs exactly the configuration it
    registered or not at all; a different configuration is a new evaluation, registered under its own schedule."""
    conflicts = []
    for flag, attr, key in REGISTERED:
        if key not in schedule:
            continue  # a schedule written before this setting was recorded: the command line (or the default) applies
        registered = schedule[key]
        given = getattr(args, attr, None)
        if attr == "systems":
            registered = _systems_text(registered)
            given = _systems_text(given) if given is not None else None
        if given is None:
            setattr(args, attr, registered)
        elif not _same_setting(given, registered):
            conflicts.append(f"{flag} {given} (registered: {registered})")
    return conflicts


def registered_profile_conflicts(schedule: dict, args) -> list[str]:
    """The differences between the provider this process builds for the registered configuration and the profile the schedule
    registered; empty when they agree or when the schedule registered no profile (written before the profile freeze)."""
    registered = schedule.get("provider_profile")
    if registered is None:
        log("the schedule registered no provider profile (written before the profile freeze); the provider built now is not compared with it")
        return []
    actual = provider_profile(build_provider(args.provider, Ledger(), args.usd_cap, args.max_calls).describe())
    return profile_differences(registered, actual)


def conflict_refusal(out_root: Path, conflicts: list[str]) -> str:
    return (f"refusing: the batch in {out_root} is registered with a different configuration than the command line gives: " + "; ".join(conflicts) +
            ". A resumed batch runs the registered provider, caps, workers, attempts and systems; omit these flags to resume it, or register a new "
            "evaluation. Nothing was constructed or run.")


def apply_defaults(args):
    """The harness's own defaults, applied only after a resumed batch had its chance to restore the registered values."""
    for attr, value in DEFAULTS.items():
        if getattr(args, attr, None) is None:
            setattr(args, attr, value)
    if args.provider == "nebius" and getattr(args, "max_calls", None) is None:
        args.max_calls = NEBIUS_DEFAULT_MAX_CALLS
    return args


def registered_argv(args) -> list[str]:
    """The registered configuration as explicit command-line flags. The launcher forwards them to the snapshot process on resume so
    that the frozen harness copy (which may predate the restore logic) runs the registered provider and limits, never its parser
    defaults."""
    out: list[str] = []
    for flag, attr, _ in REGISTERED:
        value = getattr(args, attr, None)
        if value is not None:
            out += [flag, _systems_text(value) if attr == "systems" else str(value)]
    return out


def strip_flags(argv: list[str], flags: set[str]) -> list[str]:
    """argv without the given value-taking flags, in both the `--flag value` and the `--flag=value` spelling."""
    kept, skip_value = [], False
    for token in argv:
        if skip_value:
            skip_value = False
            continue
        if token.split("=", 1)[0] in flags:
            skip_value = "=" not in token
            continue
        kept.append(token)
    return kept


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
    if args.resume:
        # the snapshot process receives the REGISTERED configuration explicitly (main() restored it from schedule.json and refused
        # any conflicting flag): the frozen harness copy in the snapshot may predate the restore logic, and must never fall back to
        # its parser defaults (the audit's AC-07: a Nebius batch resumed as Codex)
        forwarded = strip_flags(argv, {"--resume", *(flag for flag, _, _ in REGISTERED)}) + registered_argv(args)
    else:
        forwarded = strip_flags(argv, {"--resume"})
    cmd = [sys.executable, str(snapshot_root / "scripts" / "run_evaluation.py"), *forwarded, "--out", str(out_root),
           "--snapshot-root", str(snapshot_root), "--source-root", str(ROOT)]
    if args.resume:
        cmd += ["--resume", str(out_root)]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("PYTHONPATH", None)  # the snapshot process must import only its own copy
    log("fresh process from the snapshot: " + " ".join(cmd[1:3]) + " ...")
    return subprocess.call(cmd, cwd=str(snapshot_root), env=env)


def run_batch(args) -> int:
    out_root = Path(args.out or args.resume).resolve()
    schedule: dict | None = None
    if args.resume:
        # the registered configuration is restored and conflicts are refused BEFORE anything is constructed (AC-07); main() did the
        # same in the launcher, and a direct caller of run_batch gets the same guarantee
        if not (out_root / "schedule.json").is_file():
            print(f"refusing: {out_root} has no schedule.json to resume from", file=sys.stderr)
            return 2
        schedule = json.loads((out_root / "schedule.json").read_text(encoding="utf-8"))
        conflicts = restore_registered(args, schedule)
        if conflicts:
            print(conflict_refusal(out_root, conflicts), file=sys.stderr)
            return 2
    apply_defaults(args)
    if args.resume:
        # the provider this process would build (its code, the restored command line and ITS environment) must carry the registered
        # profile (R5-06): an environment override such as ATTEST_NEBIUS_ROLES is refused here, before any cell runtime exists
        drift = registered_profile_conflicts(schedule, args)
        if drift:
            print(profile_refusal(out_root, drift), file=sys.stderr)
            return 2
    snapshot_root = Path(args.snapshot_root).resolve()
    source_root = Path(args.source_root).resolve() if args.source_root else None
    provenance = runtime_provenance(snapshot_root, source_root)
    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    runs_dir = out_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    governor = codex_governor() if args.provider == "codex" else None
    resumed_at = None
    previous_rows: list[dict] = []
    existing: dict = {"rows": []}

    if args.resume:
        existing = json.loads((out_root / "evaluation.json").read_text(encoding="utf-8")) if (out_root / "evaluation.json").is_file() else {"rows": []}
        previous_rows = [r for r in existing.get("rows", []) if r.get("status") == "completed"]
        done_indices = {r["scheduled_index"] for r in previous_rows}
        cells = [c for c in schedule["cells"] if c["scheduled_index"] not in done_indices]
        resumed_at = utcnow()
        schedule.setdefault("resumptions", []).append({"at_utc": resumed_at, "cells": [c["scheduled_index"] for c in cells],
                                                       "provenance_check": "snapshot digests verified by the launcher",
                                                       "configuration": "restored from this schedule (provider, per-run USD cap, call cap, turn cap, workers, "
                                                                        "attempts, systems, approved total); a conflicting command line is refused",
                                                       "provider_profile_check": ("the provider built by this process carries the registered profile"
                                                                                  if schedule.get("provider_profile") is not None else
                                                                                  "no profile registered (schedule written before the profile freeze)")})
        (out_root / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
    else:
        suite = json.loads((snapshot_root / args.suite).read_text(encoding="utf-8"))["tasks"]
        if args.tasks:
            wanted = set(args.tasks.split(","))
            suite = [t for t in suite if t["id"] in wanted]
        from attest.core.workspace import snapshot_repo
        cells = []
        for entry in suite:
            # every task is loaded and frozen once at registration (with its own per-file bound), so a task that cannot load
            # fails the registration, before any cell and before any paid call
            task = TaskSpec.load(snapshot_root / entry["path"])
            spec_sha = task.frozen(snapshot_repo(task.repo_dir, task.max_file_bytes))["spec_sha256"]
            heldout_sha = sha256_text((snapshot_root / entry["heldout"]).read_text(encoding="utf-8"))
            for system in systems:
                for attempt in range(1, args.attempts + 1):
                    cells.append({"scheduled_index": len(cells), "task": entry["id"], "task_path": entry["path"], "heldout": entry["heldout"],
                                  "ground_truth": entry.get("ground_truth", "held_out_suite"), "kind": entry.get("kind"),
                                  "heldout_sha256": heldout_sha, "task_spec_sha256": spec_sha, "system": system, "attempt": attempt})
        probe_ledger = Ledger()
        registered_profile = None  # stays None only when the provider could not be constructed while registering without credentials
        try:
            provider_desc = build_provider(args.provider, probe_ledger, args.usd_cap, args.max_calls).describe()
            registered_profile = provider_profile(provider_desc)  # the effective models, effort, sampling and caps this process would run (R5-06)
        except Exception as error:  # noqa: BLE001 - registering a schedule must work without credentials; a real run needs them
            if not getattr(args, "register_only", False):
                raise
            provider_desc = {"provider": args.provider, "note": f"provider not constructed while registering only ({type(error).__name__})"}
        schedule = {"label": args.label, "registered_at_utc": utcnow(), "attest_version": __version__, "provider": args.provider,
                    "provider_detail": provider_desc, "provider_profile": registered_profile, "per_run_usd_cap": args.usd_cap, "approve_usd": args.approve_usd,
                    "max_calls_per_run": args.max_calls, "max_turns": args.max_turns, "workers": args.workers, "attempts_per_cell": args.attempts,
                    "systems": systems, "tasks": [t["id"] for t in suite], "suite": args.suite, "heldout_stripped_from_system_under_test": True,
                    "provenance": provenance,
                    "pacing": ({"calls_per_cell_reserved": CALLS_PER_CELL, **governor.snapshot()} if governor else None),
                    "stop_conditions": ["batch USD cap reached (reservation of the per-run cap before each run)",
                                        f"{MAX_CONSECUTIVE_INFRA} consecutive infrastructure errors", "any transport-uncertain operation (never replayed)",
                                        "Codex pacing: a cell whose bounded wait for the hourly budget is exceeded ends as ERROR (reported); no fallback",
                                        "operator STOP file in the report directory: cells not yet started are reported as not run; in-flight cells finish and keep their ledgers"],
                    "definitions": {"accepted": "attest: verdict VERIFIED; baseline: implementer finished",
                                    "correct": "existing suite and held-out suite pass on the final patch in a fresh branch (judge); for a task whose ground_truth is "
                                               "'unsatisfiable' no patch counts as correct and a hold (INFEASIBLE or NEEDS HUMAN) is the right outcome",
                                    "infra_error": "verdict ERROR or a harness exception",
                                    "not_run": "scheduled but never executed; reason recorded (a batch stop condition, the operator's STOP file, or a provider "
                                               "built for the cell whose profile differs from the registered one)",
                                    "no_patch": "no patch was produced (Attest NO CHANGE, or a baseline that neither finished nor edited): an unfinished "
                                                "task, counted neither as a rejection nor as an acceptance",
                                    "true_reject": "a patch was produced and not accepted, and the judge found it not correct; or the task is marked "
                                                   "unsatisfiable and Attest held it without a patch (INFEASIBLE, or NEEDS HUMAN with no patch)",
                                    "false_refusal": "Attest held the task without producing a patch (INFEASIBLE on an executed witness, or NEEDS HUMAN with no "
                                                     "patch and an unfinished implementer) although the task's ground truth is a satisfiable held-out suite: a wrong "
                                                     "refusal, counted neither as a rejection of a patch nor as an unfinished task; a NEEDS HUMAN hold with a patch "
                                                     "is judged on that patch",
                                    "provider_profile": "the effective provider configuration registered at launch (models per role, reasoning effort, sampling, "
                                                        "per-run caps; for the gateway the roles with their effort and the URL digest), selected from "
                                                        "provider.describe(); every completed row carries the profile its bundle recorded, a resumed process "
                                                        "whose provider differs is refused before any cell, a cell whose provider differs is reported as not run",
                                    "comparison_invalid": "a task whose cells did not all run the registered revision, provider, limits and provider profile, or "
                                                          "whose snapshot changed during the batch"},
                    "resume_policy": "a resumed batch restores provider, per-run USD cap, call cap, turn cap, workers, attempts, systems and the approved "
                                     "total from this file and refuses a conflicting command line; it refuses a process whose provider (code, command line "
                                     "and environment) differs from provider_profile; its starting committed total is rebuilt on every process start from "
                                     "every completed row and every run directory no row owns, each counted once",
                    "cells": cells}
        schedule["register_only"] = bool(getattr(args, "register_only", False))
        (out_root / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
        log(f"pre-registered {len(cells)} cells ({len(suite)} tasks x {systems} x {args.attempts} attempt(s)) on provider={args.provider}; "
            f"per-run cap ${args.usd_cap}, batch approval {args.approve_usd}, max calls {args.max_calls}; schedule -> {out_root / 'schedule.json'}")
        log(f"provider profile registered: {json.dumps(registered_profile, sort_keys=True)}"
            + (f" (overrides in the environment: {', '.join(k for k in PROFILE_ENVIRONMENT if os.environ.get(k))})" if any(os.environ.get(k) for k in PROFILE_ENVIRONMENT) else ""))
        if getattr(args, "register_only", False):
            log("register-only: no cell was started; the schedule and the snapshot digests are the record of this invocation")
            return 0

    registered_revision = ((schedule.get("provenance") or {}).get("attest_revision") or {}).get("digest")
    if registered_revision and registered_revision != provenance["attest_revision"]["digest"]:
        print(f"refusing: this process runs revision {provenance['attest_revision']['digest'][:12]} but the schedule registered {registered_revision[:12]}", file=sys.stderr)
        return 2

    # The batch's starting committed total is rebuilt from disk on EVERY process start (audit findings AC-01 and AC-02): every
    # distinct completed row once, plus every distinct run directory no row owns once, whether it was interrupted mid-run (journal)
    # or finished without a persisted row (ledger totals). No figure from an earlier process's report is trusted or suppressed.
    interrupted = interrupted_cells(runs_dir, previous_rows, existing.get("interrupted") or [], per_run_cap=args.usd_cap)
    rows_usd = sum(float(r.get("cost_committed_usd") or r.get("cost_usd") or 0.0) for r in previous_rows)
    unowned_usd = sum(float(i.get("cost_usd_committed") or 0.0) for i in interrupted)
    committed = rows_usd + unowned_usd
    starting_total = {"rebuilt_at_utc": utcnow(), "completed_rows": len(previous_rows), "completed_rows_usd": round(rows_usd, 6),
                      "unowned_run_directories": len(interrupted), "unowned_run_directories_usd": round(unowned_usd, 6),
                      "committed_usd": round(committed, 6),
                      "rule": "every completed row once plus every run directory no row owns once (interrupted: journal; finished but unreported: "
                              "ledger totals), recomputed from disk at every process start"}
    if args.resume:
        log(f"resuming: {len(previous_rows)} completed cells kept (${rows_usd:.4f}), {len(cells)} cells to run, {len(interrupted)} run director(ies) no row "
            f"owns (${unowned_usd:.4f} from their ledger records); starting committed total ${committed:.4f}")

    budget = Budget(args.approve_usd if args.provider == "nebius" else None, args.usd_cap, committed=committed)
    rows: list[dict] = list(previous_rows)

    def persist(complete: bool, finished: str | None = None):
        snapshot_now = snapshot_digests(snapshot_root)
        snapshot_intact = snapshot_now["attest_revision"]["digest"] == provenance["attest_revision"]["digest"] and \
            snapshot_now["eval_script_sha256"] == provenance["eval_script_sha256"] and snapshot_now["examples"]["digest"] == provenance["examples_digest"]["digest"]
        working_tree = attest_revision(source_root / "attest")["digest"] if source_root and (source_root / "attest").is_dir() else None
        ordered = sorted(rows, key=lambda r: r["scheduled_index"])
        validity = comparison_validity(ordered, registered_revision, snapshot_intact, schedule)
        report = {"schedule": schedule, "finished_at_utc": finished, "complete": complete, "budget": budget.snapshot(), "starting_total": starting_total,
                  "note": "every scheduled cell is reported once; there is no merge or best-of selection",
                  "provenance_check": {"registered_revision": registered_revision, "snapshot_intact_at_end": snapshot_intact,
                                       "working_tree_revision_now": working_tree,
                                       "working_tree_changed_since_launch": (working_tree != provenance["attest_revision"]["digest"]) if working_tree else None,
                                       "comparisons": validity, "invalid_tasks": sorted(t for t, v in validity.items() if not v["valid"])},
                  "pacing": governor.snapshot() if governor else None, "resumed_at_utc": resumed_at,
                  "interrupted": interrupted,
                  "interrupted_note": ("run directories that no persisted row owns, each listed once: kind 'interrupted' (the process died mid-run; the "
                                       "ledger journal is read back) or 'finished_unreported' (the pipeline finished but its row was never persisted; the "
                                       "ledger totals are read back). Every entry with included_in_batch_total is part of this batch's committed total, "
                                       "rebuilt from disk at every process start; the cell itself ran again as a fresh attempt"),
                  "rows": ordered, "summary": summarize(ordered, systems, validity)}
        (out_root / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_cell, cell, budget, args.provider, args.usd_cap, args.max_calls, runs_dir, args.max_turns, snapshot_root, governor,
                               registered_profile=schedule.get("provider_profile"))
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
    if args.resume:
        # before anything is constructed: the registered configuration is restored from the schedule and a conflicting flag refused
        out_root = Path(args.resume).resolve()
        if not (out_root / "schedule.json").is_file():
            print(f"refusing: {out_root} has no schedule.json or no snapshot to resume from", file=sys.stderr)
            return 2
        conflicts = restore_registered(args, json.loads((out_root / "schedule.json").read_text(encoding="utf-8")))
        if conflicts:
            print(conflict_refusal(out_root, conflicts), file=sys.stderr)
            return 2
    apply_defaults(args)
    if args.provider == "nebius" and args.approve_usd is None and not args.snapshot_root and not args.register_only:
        print("refusing: --provider nebius needs an explicit batch approval: --approve-usd TOTAL (hard cap for the whole batch) and --max-calls N. "
              "Nothing was run.", file=sys.stderr)
        return 2
    if args.snapshot_root:
        return run_batch(args)
    return launch(args, argv)


if __name__ == "__main__":
    sys.exit(main())
