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

Release boundary (REL-01 and REL-02 of the audit of 19 Oct 2026): environment and credential files, keys, archives, databases
and compiled binaries are excluded at every depth (`attest.env.example`, whose values are empty, is the documented exception);
every exported file is scanned whatever its name, by decoding it as UTF-8 (only a file that fails to decode AND holds NUL bytes
is binary and skipped); a ZIP archive is inspected member by member with bounded decompression if the archive policy ever
admits one (the default excludes every archive), any other archive in the staged tree is a hit; the scan runs on the exact
staged tree and fails closed. The export is built in a sibling temporary directory and only then replaces the previous
export's contents (keeping the review repository's `.git`). A destination that is the project root, an ancestor of it, inside
the project anywhere but under dist/, a non-empty directory this tool did not produce, or a Git checkout without an export
record is refused before anything is created or deleted.

Usage: export_public.py --out dist/public [--force]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the export verifies bundles with the package's own checker
ALLOW_TOP = ["attest", "tests", "examples", "deploy", "scripts", ".github", "README.md", "LICENSE", "PILOT.md", "PILOT_FEEDBACK.md",
             "METHOD.md", "FREEZE.md", "TESTING.md", "attest-console.md", "attest-first-slice.md", "attest-product-design.md", "pyproject.toml", ".gitignore"]
ALLOW_REPORTS = ["attest-first-slice-2026-10-15", "attest-verification-2026-10-15", "attest-deployment-2026-10-15", "attest-hardening-2026-10-16",
                 "attest-evaluation-2026-10-16", "attest-deployment-2026-10-16", "attest-competitive-review-2026-10-16", "attest-m1-2026-10-16",
                 "attest-m2-2026-10-17", "attest-m3-2026-10-17", "attest-reliability-2026-10-17", "attest-m4-2026-10-17",
                 "attest-deployment-2026-10-17", "attest-freeze-2026-10-17", "attest-evaluation-2026-10-17-nebius-m5",
                 "attest-ui-2026-10-18", "attest-deployment-2026-10-18", "attest-revision-2026-10-19",
                 "attest-deployment-2026-10-19", "attest-audit-2026-10-19", "attest-audit-repairs-2026-10-19", "attest-revision5-review-2026-10-19", "attest-revision5-repairs-2026-10-19",
                 "attest-deployment-2026-10-19b", "attest-deployment-2026-10-19c",
                 "attest-revision6-review-2026-10-19", "attest-revision6-repairs-2026-10-19", "attest-deployment-2026-10-19d"]  # the gateway operations report stays private (internal infrastructure)
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "snapshot", "screens", "refresh-sequence", "runs-private",
                # the 19 Oct audit's synthetic bundles are deliberately defective (they fail `attest check` by design) and its
                # synthetic work directory is scratch; the audit report describes both
                "synthetic-bundles", "synthetic-work",
                # private diagnostics sidecars (full exception text behind the correlation references that bundles and events carry; R5-04)
                "diagnostics",
                # two partial copies of run directories kept in the 16 Oct hardening report (sealed and breaker modules were not
                # copied at the time); they fail `attest check` by construction, so the originals stay private
                "semver-v2-codex-verified", "smoke-run-durationkit-codex"}
# Specific directories (relative to the project root) that stay private although same-named directories elsewhere are exported:
# the first (stopped) development batch of 19 Oct 2026 ran the revision before the ledger journal was sealed under the
# manifest, so its three bundles fail the digest check by construction (the defect it exposed).
EXCLUDE_PATHS = {"reports/attest-revision-2026-10-19/evaluation-codex"}
MAX_FILE_BYTES = 2_000_000
EXPORT_RECORD = "EXPORT.json"  # written at the root of every export; its presence marks a tree this tool produced

# Never published, at any depth (REL-01): environment files and credentials by name, keys, archives, databases and compiled or
# binary files by suffix. `attest.env.example` documents the variable names with empty values and is the only exception.
ALLOW_NAMES = {"attest.env.example"}
EXCLUDE_NAME_GLOBS = (".env", ".env.*", "*.env", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore", "*.ppk", "id_*")
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z", ".bz2", ".tbz", ".xz", ".txz", ".zst", ".rar", ".jar", ".war", ".whl", ".egg"}
DATABASE_SUFFIXES = {".db", ".db-shm", ".db-wal", ".sqlite", ".sqlite3", ".sqlitedb"}
BINARY_SUFFIXES = {".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe", ".o", ".a", ".class", ".bin", ".img", ".iso", ".dmg", ".deb", ".rpm"}
# "exclude": no archive enters the export (the default). "inspect": a .zip is copied and the final scan inspects it member by
# member with bounded decompression (scan_zip); every other archive type stays excluded.
ARCHIVE_POLICY = "exclude"
ZIP_MAX_MEMBERS = 2_000
ZIP_MEMBER_BYTES = MAX_FILE_BYTES
ZIP_TOTAL_BYTES = 20_000_000

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
SCAN_PATTERNS = [re.compile(p) for p in (
    r"codex\.axiqo", r"cxk_[A-Za-z0-9_\-]{6,}", r"tvly-[A-Za-z0-9_\-]{6,}", r"/Users/[A-Za-z0-9_.\-]+/",
    r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",                                   # PEM private keys of any kind
    r"(?i)authorization['\"]?[ \t]*:[ \t]*['\"]?bearer[ \t]+[A-Za-z0-9._\-]{16,}",       # a bearer token written out, not the header name alone
    r"(?i)\b(?:[a-z_]*token|[a-z_]*secret(?:[_-]?key)?|passwd|password)['\"]?[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9_\-]{16,}",  # token=/secret= values of 16+ chars on the same line
)]


def redact_text(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in REDACTIONS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusion_reason(path: Path) -> str | None:
    """Why a file never enters the export (REL-01), or None when it may; applied at every depth and inside archives."""
    name = path.name
    if name in ALLOW_NAMES:
        return None
    for glob in EXCLUDE_NAME_GLOBS:
        if fnmatch.fnmatchcase(name, glob):
            return f"environment or credential file ({glob})"
    suffix = Path(name.lower()).suffix
    if suffix in ARCHIVE_SUFFIXES:
        if ARCHIVE_POLICY == "inspect" and suffix == ".zip":
            return None
        return f"archive ({suffix}); archive policy {ARCHIVE_POLICY!r}"
    if suffix in DATABASE_SUFFIXES:
        return f"database ({suffix})"
    if suffix in BINARY_SUFFIXES:
        return f"compiled or binary file ({suffix})"
    return None


def decode_for_scan(data: bytes) -> str | None:
    """The UTF-8 text of a file, or None only when it fails to decode AND holds NUL bytes (binary). Text that fails to decode
    but has no NUL byte comes back with replacement characters, so it is still scanned."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        if b"\0" in data:
            return None
        return data.decode("utf-8", "replace")


def _label(source: Path, rel: Path) -> str:
    return (source.relative_to(ROOT) / rel).as_posix() if source.is_relative_to(ROOT) else rel.as_posix()


def copy_tree(source: Path, dest: Path, stats: dict) -> None:
    """Copy the publishable regular files under `source` into `dest`: excluded names and suffixes are recorded in
    stats["excluded"], every file that decodes as UTF-8 is redacted whatever its suffix (a redacted file is rewritten, an
    unchanged one is copied byte for byte), and anything else is copied byte for byte for the final scan to judge."""
    excluded = stats.setdefault("excluded", [])
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if any(_label(source, rel).startswith(prefix + "/") for prefix in EXCLUDE_PATHS):
            continue  # a specific directory stays private; same-named directories elsewhere are exported
        if path.is_symlink() or not path.is_file():
            continue
        label = _label(source, rel)
        reason = exclusion_reason(path)
        if reason:
            excluded.append({"path": label, "reason": reason})
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            stats["skipped_large"].append(label)
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        try:
            text, n = redact_text(data.decode("utf-8"))
        except UnicodeDecodeError:
            text, n = None, 0
        if n:
            stats["redactions"] += n
            stats["redacted_files"].append(label)
            stats["redacted_pairs"].append((path, target))
            target.write_bytes(text.encode("utf-8"))
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


# The 19 Oct 2026 audit's reproduction scripts (published unmodified) plant two synthetic values that are never credentials: a
# key-shaped sentinel showing what the scanner used to miss, and the offline console's admin token. Exactly these values are
# allowed through the scan; nothing else is.
SCAN_SENTINELS = ("[REDACTED-KEY]", "synthetic-team-token")


def _pattern_hits(text: str) -> list[str]:
    hits = []
    for pattern in SCAN_PATTERNS:
        for match in pattern.finditer(text):
            if any(sentinel in match.group(0) for sentinel in SCAN_SENTINELS):
                continue
            hits.append(f"{pattern.pattern} -> {match.group(0)[:40]!r}")
            break
    return hits


def scan_zip(source: Path | io.BytesIO, label: str = "", depth: int = 0) -> list[tuple[str, str]]:
    """Inspect a ZIP archive member by member with bounded decompression: the member count, each member's declared size and
    the running total are checked before anything is read, every read is capped at the declaration plus one byte, members
    with excluded names or binary content are findings, text members are scanned, and one level of nested ZIP is inspected
    the same way. Returns (member, detail) findings; an empty list means the archive passed."""
    try:
        archive = zipfile.ZipFile(source)
    except (zipfile.BadZipFile, OSError, ValueError) as error:
        return [(label, f"unreadable archive ({error})")]
    findings: list[tuple[str, str]] = []
    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if len(infos) > ZIP_MAX_MEMBERS:
            return [(label, f"{len(infos)} members exceed the inspection bound of {ZIP_MAX_MEMBERS} members")]
        total = 0
        for info in infos:
            member = f"{label}!{info.filename}" if label else info.filename
            reason = exclusion_reason(Path(info.filename))
            if reason:
                findings.append((member, reason))
                continue
            if info.file_size > ZIP_MEMBER_BYTES:
                findings.append((member, f"declares {info.file_size} bytes; the inspection bound is {ZIP_MEMBER_BYTES} bytes"))
                continue
            total += info.file_size
            if total > ZIP_TOTAL_BYTES:
                findings.append((member, f"the archive exceeds the total inspection bound of {ZIP_TOTAL_BYTES} bytes"))
                break
            try:
                with archive.open(info) as handle:
                    data = handle.read(ZIP_MEMBER_BYTES + 1)
            except (zipfile.BadZipFile, OSError, ValueError) as error:
                findings.append((member, f"unreadable member ({error})"))
                continue
            if len(data) != info.file_size:
                findings.append((member, f"delivered {len(data)} bytes for a declared size of {info.file_size} bytes"))
                continue
            if info.filename.lower().endswith(".zip"):
                if depth >= 1:
                    findings.append((member, "nested archive deeper than one level"))
                else:
                    findings.extend(scan_zip(io.BytesIO(data), member, depth + 1))
                continue
            text = decode_for_scan(data)
            if text is None:
                findings.append((member, "binary member cannot be scanned"))
                continue
            findings.extend((member, hit) for hit in _pattern_hits(text))
    return findings


def scan(dest: Path) -> list[str]:
    """Every regular file of the tree, whatever its name (the review repository's own `.git` excepted): excluded names are
    hits, a ZIP is inspected member by member, any other archive is a hit, an unreadable file is a hit, text is matched
    against SCAN_PATTERNS, and only a file that fails to decode AND holds NUL bytes is skipped as binary. Fails closed."""
    hits: list[str] = []
    if not dest.exists():
        return hits
    for path in sorted(dest.rglob("*")):
        parts = path.relative_to(dest).parts
        if ".git" in parts or path.is_symlink() or not path.is_file():
            continue
        rel = "/".join(parts)
        suffix = Path(path.name.lower()).suffix
        if suffix in ARCHIVE_SUFFIXES:
            if suffix == ".zip" and ARCHIVE_POLICY == "inspect":
                hits.extend(f"{rel}!{member}: {detail}" if member else f"{rel}: {detail}" for member, detail in scan_zip(path))
            else:
                hits.append(f"{rel}: archive in the staged tree ({suffix}; archive policy {ARCHIVE_POLICY!r}); exclude it")
            continue
        reason = exclusion_reason(path)
        if reason:
            hits.append(f"{rel}: must not be published ({reason})")
            continue
        try:
            text = decode_for_scan(path.read_bytes())
        except OSError as error:
            hits.append(f"{rel}: unreadable ({error})")
            continue
        if text is None:
            continue
        hits.extend(f"{rel}: {hit}" for hit in _pattern_hits(text))
    return hits


def destination_problem(dest: Path) -> str | None:
    """Why `dest` (resolved) may not receive an export (REL-02), or None. Decided before anything is created or deleted."""
    root = ROOT.resolve()
    if dest == root:
        return f"{dest} is the project root"
    if root.is_relative_to(dest):
        return f"{dest} contains the project root"
    if dest.is_relative_to(root) and (dest == root / "dist" or not dest.is_relative_to(root / "dist")):
        return f"{dest} lies inside the project; inside the project only a directory under dist/ may receive an export"
    if dest.exists():
        if not dest.is_dir():
            return f"{dest} is not a directory"
        if (dest / ".git").exists() and not (dest / EXPORT_RECORD).is_file():
            return f"{dest} is a Git checkout this tool did not produce (no {EXPORT_RECORD} beside .git)"
        if any(dest.iterdir()) and not (dest / EXPORT_RECORD).is_file():
            return f"{dest} is not empty and is not a previous export (no {EXPORT_RECORD})"
    return None


def build_export(staging: Path, dest: Path) -> tuple[dict, int]:
    """Copy, trace, verify and scan into `staging`; the record is written there as EXPORT.json. Returns (record, status)."""
    stats = {"files": 0, "redactions": 0, "redacted_files": [], "skipped_large": [], "redacted_pairs": [], "excluded": []}
    for name in ALLOW_TOP:
        source = ROOT / name
        if source.is_symlink():
            continue
        if source.is_dir():
            copy_tree(source, staging / name, stats)
        elif source.is_file():
            reason = exclusion_reason(source)
            if reason:
                stats["excluded"].append({"path": name, "reason": reason})
                continue
            data = source.read_bytes()
            try:
                text, n = redact_text(data.decode("utf-8"))
            except UnicodeDecodeError:
                text, n = None, 0
            (staging / name).parent.mkdir(parents=True, exist_ok=True)
            if n:
                stats["redactions"] += n
                stats["redacted_files"].append(name)
                (staging / name).write_bytes(text.encode("utf-8"))
            else:
                shutil.copyfile(source, staging / name)
            stats["files"] += 1
    for name in ALLOW_REPORTS:
        source = ROOT / "reports" / name
        if source.is_dir() and not source.is_symlink():
            copy_tree(source, staging / "reports" / name, stats)
    traced = trace_redacted_runs(stats, staging)          # REDACTION.json and derived manifests, written after the copies
    verification = verify_exported_bundles(staging)        # every exported bundle must pass `attest check`
    root = ROOT.resolve()
    record = {"out": dest.relative_to(root).as_posix() if dest.is_relative_to(root) else dest.name, "files": stats["files"],
              "redactions": stats["redactions"], "redacted_files": sorted(set(stats["redacted_files"])), "redacted_runs": traced,
              "bundle_verification": verification, "skipped_large": stats["skipped_large"], "excluded": stats["excluded"],
              "archive_policy": ARCHIVE_POLICY, "allow_top": ALLOW_TOP, "allow_reports": ALLOW_REPORTS}
    # the privacy scan is the last step and covers every staged file, whatever its name, and the record written below
    hits = scan(staging)
    hits.extend(f"{EXPORT_RECORD}: {hit}" for hit in _pattern_hits(json.dumps(record, indent=2) + "\n"))
    record["scan_hits"] = hits
    (staging / EXPORT_RECORD).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k not in ("redacted_files", "redacted_runs", "excluded")}
                     | {"redacted_file_count": len(record["redacted_files"]), "redacted_run_count": len(traced),
                        "excluded_count": len(stats["excluded"])}, indent=2))
    if verification["failed"]:
        print(f"VERIFICATION FAILED: {len(verification['failed'])} exported bundle(s) do not pass `attest check`", file=sys.stderr)
        return record, 1
    if hits:
        print("SCAN FAILED: redacted strings, secret-like tokens or unpublishable files remain:\n  " + "\n  ".join(hits[:20]), file=sys.stderr)
        return record, 1
    return record, 0


def publish(staging: Path, dest: Path) -> None:
    """Replace the previous export's contents with the staged tree, keeping the review repository's `.git`."""
    dest.mkdir(parents=True, exist_ok=True)
    for child in dest.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in staging.iterdir():
        os.replace(child, dest / child.name)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="dist/public")
    ap.add_argument("--force", action="store_true", help="replace the contents of a previous export at --out")
    args = ap.parse_args()
    dest = (ROOT / args.out).resolve()   # relative to the project root; an absolute --out is taken as given
    problem = destination_problem(dest)
    if problem:
        print(f"refusing: {problem}", file=sys.stderr)
        return 2
    if dest.exists() and any(dest.iterdir()) and not args.force:
        print(f"refusing: {dest} holds a previous export (use --force to replace it)", file=sys.stderr)
        return 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=dest.name + ".staging-", dir=dest.parent))   # a sibling: the final move is a rename
    try:
        _, status = build_export(staging, dest)
        if status:
            print("the previous export, if any, was left untouched", file=sys.stderr)
            return status
        publish(staging, dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
