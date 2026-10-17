#!/usr/bin/env python3
"""Build the public-release tree for review: an allowlisted copy of the project with internal details redacted.

Run directories whose files were redacted get a REDACTION.json (source run id and path, the original manifest's digest, the
rules, and each rewritten file's original and redacted digest) and a regenerated manifest marked as derived from the
original; every exported bundle is then verified with `attest check`, and the privacy scan runs last over everything written.

What goes in: the package, tests, scripts, examples (tasks and held-out suites), deployment files, the documentation
meant for users (README, PILOT, METHOD, console notes), the license, and the evidence reports named in ALLOW_REPORTS.
What stays out: competitor and planning proposals, internal provider notes, the server plan, run data, screenshots larger
than the size cap, virtual environments and caches.

Redaction (public copies only; the originals under reports/ are never modified): the development gateway's host name and
API key prefix, the key label, the local home directory of the author, and the project-local absolute paths in bundles
and logs. The export ends with a scan of the result for the redacted strings and for secret-like tokens; any hit fails.

Usage: export_public.py --out dist/public [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the export verifies bundles with the package's own checker
ALLOW_TOP = ["attest", "tests", "examples", "deploy", "scripts", ".github", "README.md", "LICENSE", "PILOT.md", "PILOT_FEEDBACK.md",
             "METHOD.md", "attest-console.md", "attest-first-slice.md", "attest-product-design.md", "pyproject.toml", ".gitignore"]
ALLOW_REPORTS = ["attest-first-slice-2026-10-15", "attest-verification-2026-10-15", "attest-deployment-2026-10-15", "attest-hardening-2026-10-16",
                 "attest-evaluation-2026-10-16", "attest-deployment-2026-10-16", "attest-competitive-review-2026-10-16", "attest-m1-2026-10-16",
                 "attest-m2-2026-10-17", "attest-m3-2026-10-17", "attest-reliability-2026-10-17", "attest-m4-2026-10-17",
                 "attest-deployment-2026-10-17"]  # the gateway operations report stays private (internal infrastructure)
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "snapshot", "screens", "refresh-sequence", "runs-private",
                # two partial copies of run directories kept in the 16 Oct hardening report (sealed and breaker modules were not
                # copied at the time); they fail `attest check` by construction, so the originals stay private
                "semver-v2-codex-verified", "smoke-run-durationkit-codex"}
EXCLUDE_SUFFIXES = {".pyc", ".db", ".db-shm", ".db-wal"}
MAX_FILE_BYTES = 2_000_000
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".py", ".txt", ".log", ".patch", ".sh", ".conf", ".service", ".toml", ".cfg", ".ini", ".html", ".css", ".js", ".example", ".rst", ".yml", ".yaml", ".diff"}

# (pattern, replacement): the gateway host and key shapes are never allowed to appear in public copies
REDACTIONS = [
    (re.compile(r"https?://development-gateway\.invalid(/v1)?"), "https://development-gateway.invalid"),
    (re.compile(r"development-gateway\.invalid"), "development-gateway.invalid"),
    (re.compile(r"cxk_[A-Za-z0-9_\-]{6,}"), "[REDACTED-KEY]"),
    (re.compile(r"tvly-[A-Za-z0-9_\-]{6,}"), "[REDACTED-KEY]"),
    (re.compile(r"/Users/[A-Za-z0-9_.\-]+/Documents/project/interesting/devpost/nebiusAi"), "/work/attest"),
    (re.compile(r"/Users/[A-Za-z0-9_.\-]+/"), "/home/author/"),
    (re.compile(r"private vault"), "private vault"),
]
SCAN_PATTERNS = [re.compile(p) for p in (r"codex\.axiqo", r"cxk_[A-Za-z0-9_\-]{6,}", r"tvly-[A-Za-z0-9_\-]{6,}", r"/Users/[A-Za-z0-9_.\-]+/",
                                          r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}")]


def redact_text(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in REDACTIONS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_tree(source: Path, dest: Path, stats: dict) -> None:
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if any(part in EXCLUDE_DIRS for part in rel.parts) or path.suffix in EXCLUDE_SUFFIXES:
            continue
        if path.is_symlink() or not path.is_file():
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            stats["skipped_large"].append(str(source.relative_to(ROOT) / rel))
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in TEXT_SUFFIXES or path.name in ("Makefile", "LICENSE"):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copyfile(path, target)
                continue
            text, n = redact_text(text)
            if n:
                stats["redactions"] += n
                stats["redacted_files"].append(str(source.relative_to(ROOT) / rel))
                stats["redacted_pairs"].append((path, target))
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copyfile(path, target)
        stats["files"] += 1


def _run_dir_of(path: Path, stop: Path) -> Path | None:
    """The run directory (holding proof_bundle.json) that contains `path`, if any, searching upwards to `stop`."""
    current = path.parent
    while current != stop and current != current.parent:
        if (current / "proof_bundle.json").is_file():
            return current
        current = current.parent
    return None


def trace_redacted_runs(stats: dict, dest: Path) -> list[dict]:
    """For every exported run directory with a rewritten file: write REDACTION.json (source run, original manifest digest,
    rules, per-file original and redacted digests) and regenerate manifest.json as an explicitly derived manifest. The
    original run directory is never touched; `attest check` on the copy verifies the derived manifest and reports the
    redaction. Run directories without an original manifest (recorded before milestone M2) get REDACTION.json only."""
    from attest.core.manifest import MANIFEST_FILE, build_manifest
    by_run: dict[Path, list[tuple[Path, Path]]] = {}
    for original, copy in stats["redacted_pairs"]:
        run_copy = _run_dir_of(copy, dest)
        if run_copy is not None:
            by_run.setdefault(run_copy, []).append((original, copy))
    records = []
    for run_copy, pairs in sorted(by_run.items()):
        run_original = pairs[0][0].parent
        while not (run_original / "proof_bundle.json").is_file() and run_original != run_original.parent:
            run_original = run_original.parent
        try:
            run_id = json.loads((run_copy / "proof_bundle.json").read_text(encoding="utf-8")).get("run_id") or run_copy.name
        except (json.JSONDecodeError, OSError):
            run_id = run_copy.name
        original_manifest = run_original / MANIFEST_FILE
        record = {"note": "redacted public copy; the original run directory is kept privately and was not modified",
                  "source_run_id": run_id, "source_relative_path": run_original.relative_to(ROOT).as_posix(),
                  "source_manifest_sha256": _sha256(original_manifest) if original_manifest.is_file() else None,
                  "rules": [pattern.pattern for pattern, _ in REDACTIONS],
                  "files": [{"path": copy.relative_to(run_copy).as_posix(), "original_sha256": _sha256(original), "original_bytes": original.stat().st_size,
                             "redacted_sha256": _sha256(copy), "redacted_bytes": copy.stat().st_size} for original, copy in sorted(pairs, key=lambda x: x[1])]}
        (run_copy / "REDACTION.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        if original_manifest.is_file():
            manifest = build_manifest(run_copy, run_id)
            manifest["derived_from"] = {"original_manifest_sha256": record["source_manifest_sha256"], "redaction_record": "REDACTION.json",
                                        "note": "manifest of the redacted public copy; the original manifest covers the private original"}
            (run_copy / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        records.append({"run_copy": str(run_copy.relative_to(dest)), "run_id": run_id, "files": len(pairs), "manifest_regenerated": original_manifest.is_file()})
    return records


def verify_exported_bundles(dest: Path) -> dict:
    """`attest check` on every exported run directory; the export fails if any has an error."""
    from attest.core.check import CheckError, check_bundle
    results = {"checked": 0, "ok": 0, "failed": [], "warnings": 0}
    for bundle_path in sorted(dest.rglob("proof_bundle.json")):
        run_dir = bundle_path.parent
        results["checked"] += 1
        try:
            report = check_bundle(run_dir)
        except CheckError as error:
            results["failed"].append({"run": str(run_dir.relative_to(dest)), "error": str(error)})
            continue
        results["warnings"] += report["warnings"]
        if report["ok"]:
            results["ok"] += 1
        else:
            results["failed"].append({"run": str(run_dir.relative_to(dest)), "errors": [c["detail"] for c in report["checks"] if c["ok"] is False and c["severity"] == "error"]})
    return results


def scan(dest: Path) -> list[str]:
    hits = []
    for path in sorted(dest.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES and path.name not in ("LICENSE",):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SCAN_PATTERNS:
            match = pattern.search(text)
            if match:
                hits.append(f"{path.relative_to(dest)}: {pattern.pattern} -> {match.group(0)[:40]!r}")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist/public")
    ap.add_argument("--force", action="store_true", help="replace an existing export directory")
    args = ap.parse_args()
    dest = (ROOT / args.out).resolve()
    if dest.exists():
        if not args.force:
            print(f"refusing: {dest} exists (use --force)", file=sys.stderr)
            return 2
        # replace the exported files but keep the review repository's history (.git) when one was initialised there
        for child in dest.iterdir():
            if child.name == ".git":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    dest.mkdir(parents=True, exist_ok=True)
    stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": [], "redacted_pairs": []}
    for name in ALLOW_TOP:
        source = ROOT / name
        if source.is_dir():
            copy_tree(source, dest / name, stats)
        elif source.is_file():
            (dest / name).parent.mkdir(parents=True, exist_ok=True)
            text, n = redact_text(source.read_text(encoding="utf-8"))
            stats["redactions"] += n
            (dest / name).write_text(text, encoding="utf-8")
            stats["files"] += 1
    for name in ALLOW_REPORTS:
        source = ROOT / "reports" / name
        if source.is_dir():
            copy_tree(source, dest / "reports" / name, stats)
    traced = trace_redacted_runs(stats, dest)          # REDACTION.json and derived manifests, written after the copies
    verification = verify_exported_bundles(dest)        # every exported bundle must pass `attest check`
    record = {"out": str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else dest.name, "files": stats["files"], "redactions": stats["redactions"], "redacted_files": sorted(set(stats["redacted_files"])),
              "redacted_runs": traced, "bundle_verification": verification, "skipped_large": stats["skipped_large"],
              "allow_top": ALLOW_TOP, "allow_reports": ALLOW_REPORTS}
    # the privacy scan is the last step and covers every output file, including the record written below
    hits = scan(dest)
    record_text = json.dumps(record, indent=2) + "\n"
    for pattern in SCAN_PATTERNS:
        match = pattern.search(record_text)
        if match:
            hits.append(f"EXPORT.json: {pattern.pattern} -> {match.group(0)[:40]!r}")
    record["scan_hits"] = hits
    (dest / "EXPORT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in ("redacted_files", "redacted_runs")}
                     | {"redacted_file_count": len(record["redacted_files"]), "redacted_run_count": len(traced)}, indent=2))
    if verification["failed"]:
        print(f"VERIFICATION FAILED: {len(verification['failed'])} exported bundle(s) do not pass `attest check`", file=sys.stderr)
        return 1
    if hits:
        print("SCAN FAILED: redacted strings or secret-like tokens remain", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
