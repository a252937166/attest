#!/usr/bin/env python3
"""Build the public-release tree for review: an allowlisted copy of the project with internal details redacted.

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
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOW_TOP = ["attest", "tests", "examples", "deploy", "scripts", ".github", "README.md", "LICENSE", "PILOT.md", "PILOT_FEEDBACK.md",
             "METHOD.md", "attest-console.md", "attest-first-slice.md", "attest-product-design.md", "pyproject.toml", ".gitignore"]
ALLOW_REPORTS = ["attest-first-slice-2026-10-15", "attest-verification-2026-10-15", "attest-deployment-2026-10-15", "attest-hardening-2026-10-16",
                 "attest-evaluation-2026-10-16", "attest-deployment-2026-10-16", "attest-competitive-review-2026-10-16", "attest-m1-2026-10-16",
                 "attest-m2-2026-10-17", "attest-m3-2026-10-17", "attest-reliability-2026-10-17", "attest-m4-2026-10-17",
                 "attest-deployment-2026-10-17"]  # the gateway operations report stays private (internal infrastructure)
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "snapshot", "screens", "refresh-sequence", "runs-private"}
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
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copyfile(path, target)
        stats["files"] += 1


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
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": []}
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
    hits = scan(dest)
    record = {"out": str(dest), "files": stats["files"], "redactions": stats["redactions"], "redacted_files": sorted(set(stats["redacted_files"])),
              "skipped_large": stats["skipped_large"], "scan_hits": hits, "allow_top": ALLOW_TOP, "allow_reports": ALLOW_REPORTS}
    (dest / "EXPORT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in ("redacted_files",)} | {"redacted_file_count": len(record["redacted_files"])}, indent=2))
    if hits:
        print("SCAN FAILED: redacted strings or secret-like tokens remain", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
