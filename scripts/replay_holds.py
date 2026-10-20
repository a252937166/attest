#!/usr/bin/env python3
"""Replay a recorded hold: run breaker test modules against the recorded candidate and against the unmodified base.

Purpose (17 Oct 2026): three Attest holds in the Codex dry run blocked candidates the held-out judge accepted. This tool
re-runs the original and the corrected adversarial modules on both sides, through the REAL sealed-suite supervisor, so the
record shows for every test whether it passes on the candidate and whether it still fails on the original implementation.

Two modes, both without model inference:
* local (default): the supervisor and children run with this interpreter, not as root (privilege separation off, recorded).
* --sandbox: one retained checkpoint of the task repository in Nebius Token Factory Sandboxes, then one disposable
  networking-off branch per module and side; the result is bound exactly like a pipeline run (operation UUIDs recorded).

The candidate is reconstructed from the run's candidate.patch and checked against the sha256 the bundle recorded; the base
repository is checked against the frozen task's file digests. Nothing in the recorded run directory is modified.

Usage:
  replay_holds.py --run RUN_DIR --task TASK_JSON --module LABEL=PATH [--module LABEL=PATH ...] --out REPORT.json
                  [--sandbox] [--per-test-timeout 60]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.core.sealed import (SUPERVISOR_VERSION, bind_verification, guest_files_for, new_nonce, read_sealed_result,  # noqa: E402
                                sealed_steps, sha256_text, static_test_ids, summarize)
from attest.core.task import GUEST_PYTHON, GUEST_REPO, TaskSpec  # noqa: E402
from attest.core.workspace import snapshot_repo  # noqa: E402
from attest.ledger import Ledger, utcnow  # noqa: E402

GUEST_MODULE_DIR = "/tmp/replay"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reconstruct_candidate(repo_dir: Path, patch_path: Path, recorded_sha: dict) -> tuple[dict[str, bytes], dict]:
    """Apply the recorded candidate.patch to a temporary copy of the base repository; return the changed files and a check."""
    if shutil.which("patch") is None:
        raise SystemExit("the `patch` program is required to reconstruct the candidate")
    tmp = Path(tempfile.mkdtemp(prefix="attest-replay-"))
    try:
        work = tmp / "repo"
        shutil.copytree(repo_dir, work, ignore=shutil.ignore_patterns("__pycache__"))
        proc = subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(patch_path.resolve())], cwd=work, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"candidate.patch did not apply cleanly: {proc.stdout[-400:]} {proc.stderr[-400:]}")
        base = snapshot_repo(repo_dir)
        after = snapshot_repo(work)
        changed = {rel: data for rel, data in after.items() if base.get(rel) != data}
        actual = {rel: sha256_bytes(data) for rel, data in changed.items()}
        check = {"changed_paths": sorted(changed), "recorded_sha256": recorded_sha, "reconstructed_sha256": actual,
                 "identical_to_recorded": actual == recorded_sha}
        return changed, check
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_local(repo_dir: Path, changed: dict[str, bytes] | None, module_src: str, module_name: str, extra_paths: list[str],
              per_test_timeout: int, test_timeout: int) -> dict:
    """One supervisor run with this interpreter: base when `changed` is None, candidate otherwise."""
    tmp = Path(tempfile.mkdtemp(prefix="attest-replay-local-"))
    try:
        repo = tmp / "w"
        shutil.copytree(repo_dir, repo, ignore=shutil.ignore_patterns("__pycache__"))
        for rel, data in (changed or {}).items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_bytes(data)
        suite_dir = tmp / "replay"
        paths = [str(repo / p.strip("/")) for p in extra_paths] + [str(repo)]
        files = guest_files_for(str(suite_dir), module_name, module_src, repo_dir=str(repo), extra_paths=paths[:-1], canary=True)
        for path, data in files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(data)
        nonce = new_nonce()
        env = {**os.environ, "PYTHONPATH": ":".join(paths), "PYTHONDONTWRITEBYTECODE": "1"}
        steps = sealed_steps(sys.executable, str(repo), str(suite_dir), nonce, paths[:-1], {"PYTHONPATH": ":".join(paths)},
                             timeout=test_timeout, module_name=module_name, per_test_timeout=per_test_timeout, step_prefix="replay")
        started = time.monotonic()
        outputs = {}
        for step in steps:
            proc = subprocess.run(step["cmd"], cwd=step["cwd"], env=env, capture_output=True, timeout=test_timeout + 60)
            outputs[step["name"]] = proc.stdout.decode("utf-8", "replace")
        raw = json.loads(outputs["replay_result"]) if outputs.get("replay_result", "").strip().startswith("{") else None
        return _describe(raw, module_src, module_name, nonce, round(time.monotonic() - started, 2), None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _describe(raw: dict | None, module_src: str, module_name: str, nonce: str, wall_s: float, operation_uuid: str | None) -> dict:
    summary = summarize(raw)
    ids = static_test_ids(module_src, module_name)
    binding = bind_verification(raw, ids, sha256_text(module_src), nonce) if raw else {"ok": False, "checks": {}, "reasons": ["no result"]}
    tests = [{"id": t["id"].split(".")[-1], "outcome": t["outcome"], "duration_s": t.get("duration_s"), "timed_out": t.get("timed_out"),
              "exit_code": t.get("exit_code"), "signal": t.get("signal"), "result_bytes": next((r.get("result_bytes") for r in (raw or {}).get("tests", []) if r.get("id") == t["id"]), None),
              "failure_tail": (t.get("failure_tail") or "")[-300:]} for t in summary["tests"]]
    return {"supervisor": (raw or {}).get("supervisor"), "privilege_separation": (raw or {}).get("privilege_separation"),
            "summary_line": summary["summary_line"], "ran": summary["ran"], "passed": summary["passed"], "failing": summary["failing"],
            "all_passed": summary["all_passed"], "canary_ok": summary.get("canary_ok"), "wall_s": wall_s, "operation_uuid": operation_uuid,
            "binding_failed_checks": [k for k, v in binding.get("checks", {}).items() if not v], "tests": tests}


def run_sandbox(task: TaskSpec, snapshot: dict[str, bytes], changed_by_module: list[tuple[str, str, str, dict | None]],
                per_test_timeout: int, log) -> tuple[dict, list[dict]]:
    """One checkpoint, then one disposable branch per (module, side). Returns (checkpoint record, branch records)."""
    from attest.sandbox.tf_sandboxes import TokenFactorySandboxes
    from attest.secrets import load_secret, project_id
    ledger = Ledger()
    ledger.attach_sink(Path(tempfile.mkdtemp(prefix="attest-replay-ledger-")) / "ledger.jsonl")  # operations are journaled before dispatch (revision 9)
    executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)
    image = executor.resolve_image(task.base_image)
    steps = []
    if task.install_command:
        steps.append({"name": "install", "cmd": task.install_command, "cwd": GUEST_REPO, "timeout": max(60, task.checkpoint_timeout - 60),
                      "env": task.guest_env(), "stop_on_failure": True})
    steps.append({"name": "existing", "cmd": task.test_command, "cwd": GUEST_REPO, "timeout": task.test_timeout, "env": task.guest_env()})
    log(f"sandbox: checkpoint from {task.base_image} ({image}), networking={'on' if task.checkpoint_networking else 'off'}")
    checkpoint = executor.create_checkpoint(image, {f"{GUEST_REPO}/{rel}": data for rel, data in snapshot.items()}, steps, stage="replay-checkpoint",
                                            timeout=task.checkpoint_timeout, networking=task.checkpoint_networking)
    record = {"operation_uuid": checkpoint.operation_uuid, "status": checkpoint.status, "image_uuid": checkpoint.result_image_uuid,
              "runner_error": checkpoint.runner_error, "existing_exit_code": (checkpoint.step("existing") or {}).exit_code if checkpoint.step("existing") else None}
    if not checkpoint.ok or not checkpoint.result_image_uuid:
        raise SystemExit(f"checkpoint failed: {record}")
    branches = []
    for label, side, module_src, changed in changed_by_module:
        module_name = "test_breaker"
        files = {f"{GUEST_REPO}/{rel}": data for rel, data in (changed or {}).items()}
        files.update(guest_files_for(GUEST_MODULE_DIR, module_name, module_src, repo_dir=GUEST_REPO, extra_paths=task.sealed_extra_paths(), canary=True))
        nonce = new_nonce()
        steps = sealed_steps(GUEST_PYTHON, GUEST_REPO, GUEST_MODULE_DIR, nonce, task.sealed_extra_paths(), task.guest_env(),
                             timeout=task.test_timeout, module_name=module_name, per_test_timeout=per_test_timeout, step_prefix="replay")
        log(f"sandbox: {label} on {side}")
        started = time.monotonic()
        run = executor.run_branch(checkpoint.result_image_uuid, files, steps, stage=f"replay-{label}-{side}", timeout=task.test_timeout + 60)
        raw = read_sealed_result(run, "replay")
        desc = _describe(raw, module_src, module_name, nonce, round(time.monotonic() - started, 2), run.operation_uuid)
        desc.update({"label": label, "side": side, "runner_error": run.runner_error, "status": run.status})
        branches.append(desc)
        log(f"  -> {desc['summary_line']} (op {run.operation_uuid})")
    record["sandbox_operations"] = ledger.totals()["sandbox_operations"]
    return record, branches


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="recorded run directory (read only)")
    ap.add_argument("--task", required=True, help="task.json of the same task (its repo is the base)")
    ap.add_argument("--module", action="append", required=True, help="LABEL=PATH of a test module to replay (importable as test_breaker)")
    ap.add_argument("--out", required=True, help="JSON report to write")
    ap.add_argument("--sandbox", action="store_true", help="also replay in Nebius Sandboxes through the supervisor (no inference)")
    ap.add_argument("--per-test-timeout", type=int, default=60)
    args = ap.parse_args()

    run_dir = Path(args.run)
    bundle = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8"))
    task = TaskSpec.load(Path(args.task))
    snapshot = snapshot_repo(task.repo_dir)
    frozen_files = (bundle.get("task") or {}).get("repo_files_sha256") or {}
    base_identical = {rel: sha256_bytes(data) for rel, data in snapshot.items()} == frozen_files
    changed, candidate_check = reconstruct_candidate(task.repo_dir, run_dir / "candidate.patch", (bundle.get("candidate") or {}).get("sha256") or {})
    modules = []
    for item in args.module:
        label, _, path = item.partition("=")
        src = Path(path).read_text(encoding="utf-8")
        modules.append((label, path, src))

    def log(message: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

    report = {"generated_at_utc": utcnow(), "run_id": bundle.get("run_id"), "run_dir": str(run_dir), "verdict": (bundle.get("verdict") or {}).get("verdict"),
              "task": task.id, "task_json": args.task, "supervisor_now": SUPERVISOR_VERSION,
              "supervisor_recorded": ((bundle.get("provenance") or {}).get("supervisor") or {}).get("version"),
              "base_repo_identical_to_frozen_task": base_identical, "candidate": candidate_check, "per_test_timeout_s": args.per_test_timeout,
              "modules": {}}
    for label, path, src in modules:
        log(f"local: {label} ({path})")
        entry = {"path": path, "sha256": sha256_text(src), "tests": len(static_test_ids(src, "test_breaker")), "local": {}}
        for side, files in (("base", None), ("candidate", changed)):
            entry["local"][side] = run_local(task.repo_dir, files, src, "test_breaker", task.python_paths, args.per_test_timeout, task.test_timeout)
            log(f"  {side}: {entry['local'][side]['summary_line']} in {entry['local'][side]['wall_s']} s")
        report["modules"][label] = entry
    if args.sandbox:
        plan = [(label, side, src, (changed if side == "candidate" else None)) for label, _, src in modules for side in ("base", "candidate")]
        checkpoint, branches = run_sandbox(task, snapshot, plan, args.per_test_timeout, log)
        report["sandbox"] = {"checkpoint": checkpoint}
        for branch in branches:
            report["modules"][branch["label"]].setdefault("sandbox", {})[branch["side"]] = branch
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nrun {report['run_id']} ({report['verdict']}); base identical to frozen task: {base_identical}; candidate reconstructed: {candidate_check['identical_to_recorded']}")
    print(f"{'module':<28} {'mode':<8} {'side':<10} {'result':<48} {'wall s':>7}")
    for label, entry in report["modules"].items():
        for mode in ("local", "sandbox"):
            for side, desc in (entry.get(mode) or {}).items():
                print(f"{label:<28} {mode:<8} {side:<10} {desc['summary_line'][:48]:<48} {desc['wall_s']:>7}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
