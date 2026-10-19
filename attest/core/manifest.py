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
MANIFEST_VERSION = 1

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
    run_dir = Path(run_dir)
    return sorted(p for p in run_dir.rglob("*") if p.is_file() and p.relative_to(run_dir).as_posix() not in exclude)


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
    """Recompute every listed digest. Reports mismatched and missing entries and files present but unlisted."""
    run_dir = Path(run_dir)
    listed = {f["path"]: f for f in manifest.get("files") or []}
    mismatched, missing = [], []
    for rel, entry in listed.items():
        path = run_dir / rel
        if not path.is_file():
            missing.append(rel)
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256") or path.stat().st_size != entry.get("bytes"):
            mismatched.append({"path": rel, "expected": entry.get("sha256"), "actual": actual,
                               "expected_bytes": entry.get("bytes"), "actual_bytes": path.stat().st_size})
    present = {p.relative_to(run_dir).as_posix() for p in list_files(run_dir, tuple(manifest.get("excluded") or (MANIFEST_FILE,)))}
    unlisted = sorted(present - set(listed))
    return {"ok": not mismatched and not missing, "checked": len(listed), "mismatched": mismatched, "missing": missing, "unlisted": unlisted}
