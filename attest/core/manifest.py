"""Artifact manifest: one sha256 and size per file of a run directory, written last so the bundle can be checked offline.

`manifest.json` lists every file in the run directory except itself. `attest check` recomputes each digest; the console
shows the purpose and size of each artifact from the same table. Old run directories without a manifest get one computed
on the fly (`build_manifest`) and are reported by `attest check` as `no manifest` (integrity not checkable).

A SHA-256 manifest is an integrity and internal-consistency check, not a digital signature and not independent proof of
execution: whoever can edit the files can regenerate it. The bindings and the verdict rule are therefore recomputed too.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path

MANIFEST_FILE = "manifest.json"
MANIFEST_VERSION = 2  # v2 (19 Oct 2026, CORE-07): a complete listing is required; symlinks are never listed and are reported
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9._\-]+$")

PURPOSES: tuple[tuple[str, str], ...] = (
    (r"^PROOF\.md$", "Human-readable rendering of the Proof Bundle"),
    (r"^proof_bundle\.json$", "The Proof Bundle: every stage record, gate and the verdict"),
    (r"^manifest\.json$", "sha256 and size of every artifact (this file)"),
    (r"^task\.frozen\.json$", "Frozen task: statement, policy and repository digests"),
    (r"^baseline\.json$", "Repository's own suite on the unmodified checkpoint"),
    (r"^spec\.json$", "Specification and contract written before any code"),
    (r"^grounding\.json$", "External references consulted for the specification"),
    (r"^sealed/test_sealed\.py$", "Sealed acceptance tests (E1), written before the patch"),
    (r"^sealed/test_sealed\.attempt\d+\.py$", "Rejected sealing attempt, kept for the record"),
    (r"^red\.attempt\d+\.json$", "Red check of a sealing attempt on the unmodified base"),
    (r"^trajectory\.jsonl$", "Implementer action trail, one JSON object per turn"),
    (r"^candidate\.patch$", "Unified diff of the candidate patch"),
    (r"^tamper_scan\.json$", "Static scan of the added lines for tampering constructs"),
    (r"^verify\.json$", "Fresh-branch verification: sealed, existing and held-out suites with binding"),
    (r"^verify_raw\.json$", "Raw supervisor results used to recompute the binding offline"),
    (r"^breaker\.json$", "Breaker pass: mutants (E2) and tests written after the patch (E3)"),
    (r"^breaker_tests\.py$", "Tests written after the patch (E3)"),
    (r"^breaker_tests\.attempt\d+\.py$", "Rejected breaker attempt, kept for the record"),
    (r"^breaker_response\.attempt\d+\.json$", "Raw breaker model answer"),
    (r"^mutants_.*\.py$", "Source of one mutant used in E2"),
    (r"^drift\.json$", "Drift audit (E5)"),
    (r"^arbitration\.json$", "Arbitration of generated-test failures (E6)"),
    (r"^arbitration/.*\.py$", "Corrected test module produced by the arbiter (E6)"),
    (r"^contract_audit\.json$", "Contract audit: claimed conflicts and the result of executing their witness programs"),
    (r"^contract_audit/witness_\d+\.py$", "Witness program written by the contract auditor and executed on the unmodified repository"),
    (r"^ledger\.json$", "Model calls and sandbox operations with usage and cost"),
    (r"^ledger\.jsonl$", "Append-only ledger journal: reservations before each request, call records as they complete"),
    (r"^judge\.json$", "Independent judge result (evaluation harness only)"),
)


def purpose_of(rel_path: str) -> str:
    for pattern, purpose in PURPOSES:
        if re.match(pattern, rel_path):
            return purpose
    return "Run artifact"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_files(run_dir: Path, exclude: tuple[str, ...] = (MANIFEST_FILE,)) -> list[Path]:
    """Regular files of the run directory (symlinks are never part of a bundle: they are reported by `list_symlinks`)."""
    run_dir = Path(run_dir)
    return sorted(p for p in run_dir.rglob("*") if not p.is_symlink() and p.is_file() and p.relative_to(run_dir).as_posix() not in exclude)


def list_symlinks(run_dir: Path) -> list[str]:
    run_dir = Path(run_dir)
    return sorted(p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_symlink())


def unsafe_path(rel: str) -> bool:
    """A listed path must be relative, contained and made of plain segments (no `..`, no absolute path, no backslash)."""
    parts = rel.split("/")
    return (not rel or rel.startswith("/") or "\\" in rel or any(part in ("", ".", "..") for part in parts)
            or not all(SAFE_SEGMENT.match(part) for part in parts))


def build_manifest(run_dir: Path, run_id: str | None = None, exclude: tuple[str, ...] = (MANIFEST_FILE,)) -> dict:
    run_dir = Path(run_dir)
    files = []
    for path in list_files(run_dir, exclude):
        rel = path.relative_to(run_dir).as_posix()
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path), "purpose": purpose_of(rel)})
    return {"version": MANIFEST_VERSION, "run_id": run_id or run_dir.name, "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "algorithm": "sha256", "excluded": list(exclude), "file_count": len(files), "total_bytes": sum(f["bytes"] for f in files),
            "files": files}


def verify_manifest(run_dir: Path, manifest: dict) -> dict:
    """Recompute every listed digest and check the listing itself. `ok` covers the digests (mismatched or missing entries);
    `complete` says every regular file of the run directory is listed; `entries_ok` says the listing is well formed (no
    duplicate or unsafe path, correct count and total, sha256, only the manifest itself excluded); `symlinks` names links in
    the run directory, which a bundle must not contain. `attest check` decides which of these are errors for the bundle's
    evidence protocol; a fully verified manifest needs all three."""
    run_dir = Path(run_dir)
    entries = list(manifest.get("files") or [])
    listed: dict[str, dict] = {}
    duplicates, unsafe = [], []
    for entry in entries:
        rel = str(entry.get("path") or "")
        if rel in listed:
            duplicates.append(rel)
        listed[rel] = entry
        if unsafe_path(rel):
            unsafe.append(rel)
    mismatched, missing, symlinked = [], [], []
    for rel, entry in listed.items():
        path = run_dir / rel
        if rel in unsafe:
            continue
        if path.is_symlink():
            symlinked.append(rel)  # a listed entry must be a regular file; a link is never opened
            continue
        if not path.is_file():
            missing.append(rel)
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256") or path.stat().st_size != entry.get("bytes"):
            mismatched.append({"path": rel, "expected": entry.get("sha256"), "actual": actual,
                               "expected_bytes": entry.get("bytes"), "actual_bytes": path.stat().st_size})
    excluded = list(manifest.get("excluded") or (MANIFEST_FILE,))
    present = {p.relative_to(run_dir).as_posix() for p in list_files(run_dir, tuple(excluded))}
    unlisted = sorted(present - set(listed))
    symlinks = sorted(set(list_symlinks(run_dir)) | set(symlinked))
    count_ok = manifest.get("file_count") == len(entries)
    total_ok = manifest.get("total_bytes") == sum(int(e.get("bytes") or 0) for e in entries)
    excluded_ok = excluded == [MANIFEST_FILE]
    algorithm_ok = manifest.get("algorithm") == "sha256"
    entry_problems = []
    if duplicates:
        entry_problems.append("duplicate path(s): " + ", ".join(duplicates)[:200])
    if unsafe:
        entry_problems.append("unsafe path(s): " + ", ".join(unsafe)[:200])
    if not count_ok:
        entry_problems.append(f"file_count {manifest.get('file_count')} vs {len(entries)} entries")
    if not total_ok:
        entry_problems.append(f"total_bytes {manifest.get('total_bytes')} vs the sum of the entries")
    if not excluded_ok:
        entry_problems.append(f"exclusions {excluded} (only {MANIFEST_FILE} may be excluded)")
    if not algorithm_ok:
        entry_problems.append(f"algorithm {manifest.get('algorithm')!r} (sha256 required)")
    return {"ok": not mismatched and not missing and not symlinked, "checked": len(listed), "mismatched": mismatched, "missing": missing,
            "unlisted": unlisted, "complete": not unlisted, "duplicates": duplicates, "unsafe": unsafe, "symlinks": symlinks,
            "count_ok": count_ok, "total_ok": total_ok, "excluded_ok": excluded_ok, "algorithm_ok": algorithm_ok,
            "entries_ok": not entry_problems, "entry_problems": entry_problems, "version": manifest.get("version")}
