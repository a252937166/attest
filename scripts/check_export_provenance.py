#!/usr/bin/env python3
"""Check every Proof Bundle of an export against its recorded provenance (revision 8, 19 Oct 2026).

For each run directory that holds a proof_bundle.json in the export (default dist/public):
1. `attest check` on the exported copy: ok, its evidence protocol, whether it is fully verified, whether it is a redacted copy.
2. Its source: the same run directory in the private project tree. Every exported file equals the source byte for byte, except
   the files a REDACTION.json lists, whose original digest must equal the source file and whose redacted digest the exported
   file; a derived manifest is listed there too. (Skipped with --no-source, for a reviewer who has only the export.)
3. Its batch, when the run sits in a batch folder (`<batch>/runs/<run>` next to schedule.json and evaluation.json): the package
   digest the bundle records equals the digest the batch registered and the one its row in evaluation.json recorded, and the
   provider profile the bundle records equals the registered profile (the stable keys the harness compares).
Bundles recorded before a field existed are reported as such ("not recorded"), never as a match.

Usage: check_export_provenance.py [--export dist/public] [--source .] [--no-source] [--json out.json]
Exit code 0 when no bundle fails a check that applies to it."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from attest.core.check import check_bundle  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def batch_of(run_dir: Path) -> Path | None:
    parent = run_dir.parent
    if parent.name == "runs" and (parent.parent / "schedule.json").is_file():
        return parent.parent
    return None


def recorded_digest(bundle: dict) -> str | None:
    revision = ((bundle.get("provenance") or {}).get("attest_revision") or {})
    return revision.get("digest") if isinstance(revision, dict) else None


def check_source(export_run: Path, export_root: Path, source_root: Path) -> list[str]:
    problems = []
    source_run = source_root / export_run.relative_to(export_root)
    if not source_run.is_dir():
        return [f"no source run directory at {source_run.relative_to(source_root)}"]
    redaction = {}
    if (export_run / "REDACTION.json").is_file():
        record = json.loads((export_run / "REDACTION.json").read_text(encoding="utf-8"))
        redaction = {f["path"]: f for f in record.get("files", [])}
    for path in sorted(p for p in export_run.rglob("*") if p.is_file()):
        rel = path.relative_to(export_run).as_posix()
        if rel == "REDACTION.json":
            continue
        source_file = source_run / rel
        if rel in redaction:
            entry = redaction[rel]
            if not source_file.is_file() or sha(source_file) != entry.get("original_sha256"):
                problems.append(f"{rel}: the source differs from the original digest REDACTION.json records")
            if sha(path) != entry.get("redacted_sha256"):
                problems.append(f"{rel}: the exported file differs from the redacted digest REDACTION.json records")
        elif rel == "manifest.json" and redaction:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if not manifest.get("derived_from"):
                problems.append("manifest.json of a redacted copy is not marked as derived")
        elif not source_file.is_file():
            problems.append(f"{rel}: exported but absent from the source")
        elif sha(source_file) != sha(path):
            problems.append(f"{rel}: differs from the source and is not listed in REDACTION.json")
    return problems


def check_batch(run_dir: Path, bundle: dict, batch: Path, cache: dict) -> tuple[list[str], dict]:
    from run_evaluation import provider_profile  # the harness's own definition of the compared profile
    if batch not in cache:
        schedule = json.loads((batch / "schedule.json").read_text(encoding="utf-8"))
        rows = []
        if (batch / "evaluation.json").is_file():
            rows = json.loads((batch / "evaluation.json").read_text(encoding="utf-8")).get("rows") or []
        cache[batch] = (schedule, {r.get("run_id"): r for r in rows if r.get("run_id")})
    schedule, rows = cache[batch]
    problems, facts = [], {}
    digest = recorded_digest(bundle)
    registered = (((schedule.get("provenance") or {}).get("attest_revision")) or {}).get("digest")
    facts["registered_digest"], facts["bundle_digest"] = registered, digest
    if digest is None:
        facts["digest"] = "not recorded in the bundle"
    elif registered and digest != registered:
        problems.append(f"package digest {digest[:12]} differs from the batch's registered {registered[:12]}")
    row = rows.get(bundle.get("run_id"))
    if row is None:
        facts["row"] = "no row names this run"
    else:
        if row.get("revision_digest") and digest and row["revision_digest"] != digest:
            problems.append(f"the row records digest {row['revision_digest'][:12]}, the bundle {digest[:12]}")
        facts["row_verdict"] = row.get("verdict")
        if row.get("verdict") and (bundle.get("verdict") or {}).get("verdict") != row.get("verdict"):
            problems.append(f"the row records verdict {row.get('verdict')}, the bundle {(bundle.get('verdict') or {}).get('verdict')}")
    registered_profile = schedule.get("provider_profile")
    if registered_profile:
        actual = provider_profile(((bundle.get("profile") or {}).get("provider")))
        if actual != registered_profile:
            problems.append(f"provider profile differs from the registered one: {sorted(k for k in set(actual) | set(registered_profile) if actual.get(k) != registered_profile.get(k))}")
        facts["profile"] = "matches the registered profile" if actual == registered_profile else "differs"
    else:
        facts["profile"] = "not registered (batch predates profile registration)"
    return problems, facts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=str(ROOT / "dist" / "public"))
    ap.add_argument("--source", default=str(ROOT))
    ap.add_argument("--no-source", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()
    export_root, source_root = Path(args.export).resolve(), Path(args.source).resolve()
    results, cache = [], {}
    for bundle_path in sorted(export_root.rglob("proof_bundle.json")):
        if ".git" in bundle_path.parts or "snapshot" in bundle_path.parts:
            continue
        run_dir = bundle_path.parent
        rel = run_dir.relative_to(export_root).as_posix()
        entry = {"run_dir": rel, "problems": []}
        report = check_bundle(run_dir)
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        entry.update({"check_ok": report["ok"], "protocol": report.get("protocol"), "fully_verified": report.get("fully_verified"),
                      "redacted_copy": report.get("redacted_export"), "verdict": report.get("verdict")})
        if not report["ok"]:
            entry["problems"].append("attest check failed: " + "; ".join(c["name"] for c in report["checks"] if c["ok"] is False and c["severity"] == "error"))
        if not args.no_source:
            entry["problems"] += check_source(run_dir, export_root, source_root)
        batch = batch_of(run_dir)
        if batch is not None:
            problems, facts = check_batch(run_dir, bundle, batch, cache)
            entry["problems"] += problems
            entry["batch"] = batch.relative_to(export_root).as_posix()
            entry.update(facts)
        results.append(entry)
    failed = [r for r in results if r["problems"]]
    summary = {"export": str(export_root), "bundles": len(results), "check_ok": sum(1 for r in results if r["check_ok"]),
               "fully_verified": sum(1 for r in results if r["fully_verified"]), "historical": sum(1 for r in results if r["protocol"] is None),
               "by_protocol": {str(p): sum(1 for r in results if r["protocol"] == p) for p in sorted({r["protocol"] for r in results}, key=lambda x: (x is None, x or 0))},
               "redacted_copies": sum(1 for r in results if r["redacted_copy"]),
               "in_batches": sum(1 for r in results if r.get("batch")),
               "batch_digest_matches": sum(1 for r in results if r.get("batch") and r.get("bundle_digest") and r.get("bundle_digest") == r.get("registered_digest")),
               "batch_digest_not_recorded": sum(1 for r in results if r.get("batch") and not r.get("bundle_digest")),
               "batch_digest_not_registered": sum(1 for r in results if r.get("batch") and r.get("bundle_digest") and not r.get("registered_digest")),
               "profile_matches": sum(1 for r in results if r.get("profile") == "matches the registered profile"),
               "source_compared": not args.no_source, "failed": [{"run_dir": r["run_dir"], "problems": r["problems"]} for r in failed]}
    if args.json:
        Path(args.json).write_text(json.dumps({"summary": summary, "bundles": results}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
