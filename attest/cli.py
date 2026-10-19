"""Command-line entry points: preflight checks and running one task end to end."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
from pathlib import Path

from .ledger import Ledger
from .secrets import SecretError, load_secret, project_id

EXIT_CODES = "exit codes: 0 success (run: VERIFIED); 1 check found a mismatch; 2 refused or misconfigured (credentials, limits, bad input); 3 import skeleton has policy problems to fix"


def build_provider(name: str, ledger: Ledger, usd_cap: float):
    if name == "codex":
        from .models.codex_gateway import CodexGateway
        return CodexGateway(load_secret("CODEX_API_KEY"), ledger, notify=lambda m: print(f"[codex] {m}", flush=True))
    if name == "nebius":
        from .models.nebius_tokenfactory import NebiusTokenFactory
        return NebiusTokenFactory(load_secret("NEBIUS_API_KEY"), ledger, usd_cap=usd_cap)
    raise SystemExit(f"unknown provider {name}")


def build_executor(ledger: Ledger):
    from .sandbox.tf_sandboxes import TokenFactorySandboxes
    return TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)


def build_tavily():
    from .core.grounding import Tavily
    from .secrets import SecretError
    try:
        return Tavily(load_secret("TAVILY_API_KEY"))
    except SecretError:
        return None


def cmd_preflight(args) -> int:
    ledger = Ledger()
    report = {}
    executor = build_executor(ledger)
    who = executor.whoami()
    report["sandboxes"] = {"permissions": who.get("permissions"), "limits": who.get("limits"),
                           "base_image_uuid": executor.resolve_image(args.base_image)}
    provider = build_provider(args.provider, ledger, args.usd_cap)
    if args.provider == "codex":
        status = provider.status()
        report["codex_gateway"] = {"running": status.get("running"), "waiting": status.get("waiting"),
                                   "defaults": status.get("defaults"), "catalog": provider.catalog(),
                                   "roles": {r: provider.resolve(r) for r in provider.roles}}
    else:
        report["nebius"] = provider.describe()
    if args.adapter_smoke:
        from .sandbox.tf_sandboxes import TokenFactorySandboxes  # noqa: F401
        run = executor.run_branch(report["sandboxes"]["base_image_uuid"],
                                  {"/tmp/attest-smoke/hello.txt": b"hello from attest\n"},
                                  [{"name": "cat", "cmd": ["/bin/cat", "/tmp/attest-smoke/hello.txt"], "cwd": "/tmp", "timeout": 10},
                                   {"name": "python", "cmd": ["/usr/local/bin/python", "-c", "import sys; print(sys.version.split()[0])"], "cwd": "/tmp", "timeout": 10}],
                                  stage="adapter_smoke", timeout=30)
        report["adapter_smoke"] = {"operation_uuid": run.operation_uuid, "status": run.status, "exit_code": run.exit_code,
                                   "runner_error": run.runner_error,
                                   "steps": [{"name": s.name, "exit_code": s.exit_code, "stdout": s.stdout.strip()[:200]} for s in run.steps]}
    report["ledger"] = ledger.to_dict()
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def cmd_run(args) -> int:
    from .core.pipeline import Pipeline
    from .core.task import TaskSpec
    ledger = Ledger()
    task = TaskSpec.load(Path(args.task))
    provider = build_provider(args.provider, ledger, args.usd_cap)
    executor = build_executor(ledger)
    pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=Path(args.out),
                        max_turns=args.max_turns, max_mutants=args.max_mutants, mutation_threshold=args.mutation_threshold,
                        mutant_workers=args.mutant_workers, drift_threshold=args.drift_threshold,
                        tavily=None if args.no_grounding else build_tavily(), profile_label=args.profile_label or
                        ("development" if args.provider == "codex" else "submission-pilot"),
                        arbitrate=not args.no_arbitration, arbitration_apply=not args.arbitration_advisory)
    bundle = pipeline.run()
    print(json.dumps({"verdict": bundle["verdict"]["verdict"], "reasons": bundle["verdict"]["reasons"],
                      "out_dir": str(pipeline.out_dir), "totals": bundle["ledger"]["totals"]}, indent=2))
    return 0 if bundle["verdict"]["verdict"] == "VERIFIED" else 2


def cmd_import(args) -> int:
    """Import an external repository (GitHub at a pinned commit, or a local directory) as a bounded task skeleton."""
    from .core.external import ImportRefused, fetch_github, import_local, task_skeleton
    dest = Path(args.out) / args.id
    if dest.exists() and any(dest.iterdir()):
        print(f"refusing: {dest} exists and is not empty", file=sys.stderr)
        return 2
    dest.mkdir(parents=True, exist_ok=True)
    try:
        if args.github:
            source = fetch_github(args.github, args.commit or "", dest, max_file_bytes=args.max_file_bytes)
        else:
            source = import_local(Path(args.local), dest, max_file_bytes=args.max_file_bytes)
    except ImportRefused as error:
        print(f"refused: {error}", file=sys.stderr)
        shutil.rmtree(dest, ignore_errors=True)
        return 2
    except (OSError, urllib.error.URLError) as error:
        print(f"import failed: {type(error).__name__}: {error}", file=sys.stderr)
        shutil.rmtree(dest, ignore_errors=True)
        return 2
    statement = Path(args.statement_file).read_text(encoding="utf-8").strip() if args.statement_file else "TODO: describe the change the implementer must make."
    criteria = [line.strip() for line in Path(args.criteria_file).read_text(encoding="utf-8").splitlines() if line.strip()] if args.criteria_file else []
    heldout = {}
    for item in args.heldout or []:
        guest_rel, _, local = item.partition("=")
        source_file = Path(local)
        if source_file.is_file() and source_file.resolve().parent != dest.resolve():
            shutil.copyfile(source_file, dest / source_file.name)  # the held-out module lives next to task.json, never in repo/
            local = source_file.name
        heldout[guest_rel] = local
    install = None
    lock = None
    if args.pin:
        install = ["/usr/local/bin/python", "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check", "--target", "/tmp/deps", *args.pin]
        lock = " ".join(args.pin)
    body = task_skeleton(args.id, args.title or args.id, source, args.runner, args.write_glob or [], args.protect or None, heldout or None,
                         statement, criteria, args.python_path or [], install, lock, None, args.test_timeout, args.reference,
                         max_file_bytes=min(args.max_file_bytes, 1_000_000))
    body["import_hint"] = args.import_hint
    (dest / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    (dest / "task.json").write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # validate the skeleton the way `attest run` will, so a requester sees refusals before any sandbox operation
    from .core.external import external_policy_problems, repository_problems
    from .core.task import TaskSpec
    from .core.workspace import snapshot_repo
    task = TaskSpec.load(dest / "task.json")
    problems = repository_problems(snapshot_repo(task.repo_dir, task.max_file_bytes), task.max_file_bytes) + (external_policy_problems(task) if task.upstream else [])
    missing = [name for name, value in (("statement", not args.statement_file), ("acceptance_criteria", not criteria), ("import_hint", not args.import_hint),
                                        ("allowed_write_globs", not args.write_glob)) if value]
    next_step = (f"fill in {', '.join(missing)} in {dest / 'task.json'}, then " if missing else "") + \
        f"`python -m attest run --task {dest / 'task.json'} --out runs --provider nebius --usd-cap 0.5` (log timestamps are UTC)"
    print(json.dumps({"task": str(dest / "task.json"), "source": {k: source.get(k) for k in ("url", "commit", "files", "total_bytes", "tree_sha256", "tarball_sha256")},
                      "skipped": source.get("skipped"), "materialized_links": source.get("materialized_links"),
                      "write_scope": body["allowed_write_globs"], "protected": body["protected_globs"], "test_command": body["test_command"],
                      "install": body.get("install_command"), "heldout": sorted(body.get("heldout_tests") or {}), "policy_problems": problems,
                      "still_empty": missing, "next": next_step,
                      "note": "to import again after editing the statement, delete the task directory first (the tarball is downloaded again)"},
                     indent=2))
    return 0 if not problems else 3


def cmd_check(args) -> int:
    """Offline integrity and consistency check of a Proof Bundle (run directory or zip); exit 1 on any mismatch."""
    from .core.check import CheckError, check_bundle, format_report
    reports = []
    worst = 0
    for path in args.paths:
        try:
            report = check_bundle(path)
        except CheckError as error:
            report = {"path": path, "ok": False, "errors": 1, "warnings": 0, "checks": [{"name": "input", "ok": False, "severity": "error", "detail": str(error)}],
                      "run_id": None, "verdict": None, "manifest_verified": False, "manifest_present": False}
        reports.append(report)
        if not report["ok"]:
            worst = 1
        if not args.json:
            print(format_report(report))
            if len(args.paths) > 1:
                print()
    if args.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
    return worst


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="attest", description="Attest: evidence-gated coding agent", epilog=EXIT_CODES)
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight", help="check credentials, gateway queue, catalog and sandbox access")
    pre.add_argument("--provider", choices=["codex", "nebius"], default="codex")
    pre.add_argument("--base-image", default="python:3.12-slim")
    pre.add_argument("--adapter-smoke", action="store_true", help="run one disposable sandbox op through the adapter")
    pre.add_argument("--usd-cap", type=float, default=0.5)
    pre.add_argument("--output")
    pre.set_defaults(func=cmd_preflight)
    run = sub.add_parser("run", help="run one task end to end and write a Proof Bundle")
    run.add_argument("--task", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--provider", choices=["codex", "nebius"], default="codex")
    run.add_argument("--max-turns", type=int, default=12)
    run.add_argument("--usd-cap", type=float, default=0.5)
    run.add_argument("--profile-label")
    run.add_argument("--max-mutants", type=int, default=12)
    run.add_argument("--mutation-threshold", type=float, default=0.5)
    run.add_argument("--mutant-workers", type=int, default=8)
    run.add_argument("--drift-threshold", type=float, default=0.6)
    run.add_argument("--no-grounding", action="store_true", help="skip Tavily grounding even if the key is available")
    run.add_argument("--no-arbitration", action="store_true", help="skip the arbitration of generated-test failures")
    run.add_argument("--arbitration-advisory", action="store_true",
                     help="record the arbiter's classifications and validated corrections but never re-run a gate on them (the default "
                          "re-runs the affected gate when a correction passes the mechanical validation; a sealed assertion failure is never overridden)")
    run.set_defaults(func=cmd_run)
    imp = sub.add_parser("import", help="import an external repository (GitHub at a pinned commit, or a local directory) as a bounded task")
    src = imp.add_mutually_exclusive_group(required=True)
    src.add_argument("--github", help="https://github.com/<owner>/<repo>; requires --commit")
    src.add_argument("--local", help="local directory to copy")
    imp.add_argument("--commit", help="full 40-character commit sha (required with --github)")
    imp.add_argument("--id", required=True, help="task id (also the directory name under --out)")
    imp.add_argument("--out", required=True, help="parent directory for the task (for example examples/)")
    imp.add_argument("--title")
    imp.add_argument("--import-hint", default="", help="free text shown to the test authors and the implementer, for example "
                     "\"from pkg import f   (package lives in src/pkg)\"")
    imp.add_argument("--runner", choices=["unittest", "pytest"], default="unittest")
    imp.add_argument("--write-glob", action="append", help="allowed write scope, repeatable (required before running)")
    imp.add_argument("--protect", action="append", help="protected globs (default: tests, packaging files, CI)")
    imp.add_argument("--python-path", action="append", help="extra import roots relative to the repository (for example src)")
    imp.add_argument("--pin", action="append", help="pinned requirement name==version installed at checkpoint (repeatable)")
    imp.add_argument("--heldout", action="append", help="guest/path.py=local/file.py held-out test module, repeatable")
    imp.add_argument("--statement-file", help="file with the task statement")
    imp.add_argument("--criteria-file", help="file with one acceptance criterion per line")
    imp.add_argument("--reference", help="free-text reference (issue or pull request) recorded under upstream.reference")
    imp.add_argument("--test-timeout", type=int, default=180)
    imp.add_argument("--max-file-bytes", type=int, default=200_000, help="per-file size limit (hard cap 1,000,000)")
    imp.set_defaults(func=cmd_import)
    check = sub.add_parser("check", help="verify a Proof Bundle offline: manifest digests, bindings, ledger totals, gate-to-verdict rule, PROOF.md")
    check.add_argument("paths", nargs="+", help="run directories or downloaded bundle zips")
    check.add_argument("--json", action="store_true", help="print the report as JSON")
    check.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SecretError as error:
        print(f"attest {args.command}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
