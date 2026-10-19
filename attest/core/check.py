"""`attest check`: offline verification of a Proof Bundle (run directory or downloaded zip).

What it recomputes, without any network or sandbox access:
1. every artifact digest and size against manifest.json, and the manifest's own completeness and well-formedness (a bundle
   without a manifest is reported as `no manifest`: its integrity cannot be checked, which is different from a mismatch);
2. the frozen task digest, the sealed and adversarial module digests and their statically discovered test ids;
3. the sealed, adversarial, existing and held-out bindings from the raw supervisor results in verify_raw.json, the per-test
   outcomes the bundle summarises from them, every evaluated mutant's classification, and the base and mutant evidence of
   every validated correction;
4. the ledger totals from the individual model calls;
5. the gate records against the stage records they summarise, and the gate-to-verdict rule;
6. PROOF.md, re-rendered from proof_bundle.json (compared byte for byte when the bundle was produced by this Attest revision).

Evidence protocol (19 Oct 2026, audit finding CORE-06): a bundle that declares `evidence_protocol.version` 2 or later is
CURRENT and must carry the complete evidence for its verdict (every gate with its raw results, every evaluated mutant's raw
result, the base and mutant evidence of any correction, the witness of an INFEASIBLE verdict, isolation recorded as active
and a complete manifest); any missing item is an error. A bundle without that field is HISTORICAL: its internal consistency
is checked as far as its records allow, checks that cannot run are warnings, and it never receives the fully-verified badge.

Any mismatch is an error and the exit code is 1. The tool never re-executes sandbox runs; it establishes that the bundle is
internally consistent and unchanged since its manifest was written.

Terminology: a SHA-256 manifest provides integrity and internal-consistency checks. It is not a digital signature (anyone
who can edit the files can regenerate it, which is why `attest check` also recomputes the bindings and the verdict rule)
and it is not independent proof that the recorded sandbox operations happened; that evidence lives in the operation UUIDs
and the per-test records bound to the nonce.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from .exhibits import decision, exhibits
from .manifest import MANIFEST_FILE, build_manifest, list_symlinks, verify_manifest
from .proof import render_markdown
from .provenance import attest_revision
from .pipeline import (base_discrimination, classification_problems, classify_mutant_run, correction_problems, mutant_rerun_discrimination,
                       requirement_provenance)
from .prompts import WITNESS_EXIT_CODE, WITNESS_MARKER
from .sealed import bind_modules, bind_verification, static_test_ids, summarize
from .verdict import EVIDENCE_PROTOCOL_VERSION, expected_verdict, legacy_clearing_allowed, protocol_version
from .witness import WITNESS_LANGUAGE, Repository, analyze_witness

RAW_FILE = "verify_raw.json"
REDACTION_FILE = "REDACTION.json"  # written by scripts/export_public.py next to a redacted copy of a run directory
GATE_INVENTORY = ("existing_suite", "sealed_binding", "mutation", "adversarial_tests", "drift_audit")


class CheckError(RuntimeError):
    """The input is not a Proof Bundle (missing or unreadable proof_bundle.json, unsafe zip)."""


class Report:
    def __init__(self, path: str):
        self.path = path
        self.checks: list[dict] = []

    def add(self, name: str, ok: bool | None, detail: str, severity: str = "error") -> None:
        """ok=None means the check could not run (recorded as a warning with its reason)."""
        if ok is None:
            self.checks.append({"name": name, "ok": None, "severity": "warning", "detail": detail})
        else:
            self.checks.append({"name": name, "ok": bool(ok), "severity": severity if not ok else "info", "detail": detail})

    @property
    def errors(self) -> list[dict]:
        return [c for c in self.checks if c["ok"] is False and c["severity"] == "error"]

    @property
    def warnings(self) -> list[dict]:
        return [c for c in self.checks if c["ok"] is None or (c["ok"] is False and c["severity"] == "warning")]

    def to_dict(self) -> dict:
        return {"path": self.path, "ok": not self.errors, "errors": len(self.errors), "warnings": len(self.warnings), "checks": self.checks}


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    for info in archive.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts or "\\" in name:
            raise CheckError(f"unsafe path in zip: {name!r}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise CheckError(f"symbolic link in zip: {name!r}")
    archive.extractall(target)


def locate_run_dir(path: Path) -> tuple[Path, Path | None]:
    """Return (run_dir, tempdir_to_remove). Accepts a run directory or a zip whose entries may share a top folder."""
    path = Path(path)
    if path.is_dir():
        if not (path / "proof_bundle.json").is_file():
            raise CheckError(f"{path} has no proof_bundle.json")
        return path, None
    if not path.is_file():
        raise CheckError(f"{path} does not exist")
    if not zipfile.is_zipfile(path):
        raise CheckError(f"{path} is neither a run directory nor a zip archive")
    temp = Path(tempfile.mkdtemp(prefix="attest-check-"))
    with zipfile.ZipFile(path) as archive:
        _safe_extract(archive, temp)
    candidates = sorted(temp.rglob("proof_bundle.json"), key=lambda p: len(p.parts))
    if not candidates:
        shutil.rmtree(temp, ignore_errors=True)
        raise CheckError(f"{path} contains no proof_bundle.json")
    return candidates[0].parent, temp


def _recompute_spec_digest(task: dict) -> str | None:
    if not task or "spec_sha256" not in task:
        return None
    body = {k: v for k, v in task.items() if k != "spec_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _outcomes(tests: list | None) -> dict:
    return {t.get("id"): t.get("outcome") for t in (tests or [])}


def _binding_matches(recomputed: dict, recorded: dict | None, strict: bool) -> tuple[bool, list[str]]:
    """A recorded binding agrees with its recomputation when `ok` is equal and every recorded check has the recomputed value.
    A current bundle must also carry exactly the checks this revision computes; a historical bundle may lack checks added
    since (they are recomputed from the same raw facts and would only ever add reasons to refuse VERIFIED)."""
    recorded = recorded or {}
    recorded_checks = recorded.get("checks") or {}
    diff = [k for k, v in recorded_checks.items() if recomputed["checks"].get(k) != v]
    if strict:
        diff += [k for k in recomputed["checks"] if k not in recorded_checks]
    same = not diff and recomputed["ok"] == recorded.get("ok")
    return same, sorted(set(diff))


def required_evidence_problems(bundle: dict, run_dir: Path, raw: dict | None, protocol: int = 2) -> list[str]:
    """What a CURRENT bundle must carry for its verdict (CORE-06). Every missing item is named. The mandatory stage records are
    derived from the protocol, the terminal verdict, the frozen task and the recorded execution mode, never from which records
    happen to be present (follow-up review R5-02); from protocol 3 an INFEASIBLE verdict needs a grounded conflict (R5-03)."""
    problems: list[str] = []
    verdict = (bundle.get("verdict") or {}).get("verdict")
    task = bundle.get("task") or {}
    if not task.get("spec_sha256"):
        problems.append("task record without spec_sha256")
    if not ((bundle.get("provenance") or {}).get("attest_revision") or {}).get("digest"):
        problems.append("provenance without the Attest revision")
    if not ((bundle.get("ledger") or {}).get("totals")):
        problems.append("ledger totals missing")
    if verdict == "INFEASIBLE":
        audit = bundle.get("contract_audit") or {}
        demonstrated = [c for c in audit.get("conflicts") or [] if c.get("demonstrated")]
        if not demonstrated:
            problems.append("INFEASIBLE without a demonstrated witness in contract_audit")
        if protocol >= 3:
            grounded = [c for c in demonstrated if c.get("grounded")]
            if not grounded:
                problems.append(f"INFEASIBLE without a grounded conflict (authoritative task criteria only, witness in {WITNESS_LANGUAGE})")
            task_ids = {f"TC{i}" for i in range(1, len(task.get("acceptance_criteria") or []) + 1)}
            derived_ids = {f"AC{i}" for i in range(1, len((bundle.get("spec") or {}).get("acceptance_criteria") or []) + 1)}
            for conflict in grounded:
                if requirement_provenance(conflict.get("requirement_ids") or [], task_ids, derived_ids) != "task":
                    problems.append("a grounded conflict names criteria that are not all the task's own")
                path = conflict.get("witness_path")
                if not path or not (run_dir / path).is_file():
                    problems.append("a grounded conflict without its witness program file")
                    continue
                # the recorded flag is never trusted: the language analysis is repeated from the witness file and the copies of the
                # repository files kept in the bundle (a copy counts only when its digest equals the frozen task's; review R6-1). A
                # protocol-3 bundle keeps no copies, so a protocol-3 witness that imports repository code cannot be re-established.
                analysis = analyze_witness((run_dir / path).read_text(encoding="utf-8"), Repository.from_bundle(run_dir, task))
                if not analysis["conforms"]:
                    problems.append(f"a grounded conflict's witness is outside the constrained witness language {WITNESS_LANGUAGE}: "
                                    + "; ".join(analysis["problems"][:2])[:300])
                if protocol >= 4:
                    recorded = conflict.get("witness_language") or {}
                    if recorded.get("version") != WITNESS_LANGUAGE or not recorded.get("conforms"):
                        problems.append(f"a grounded conflict without a conforming {WITNESS_LANGUAGE} analysis record")
                    elif (recorded.get("repository_files") or {}) != analysis["repository_files"]:
                        problems.append("a grounded conflict's recorded repository files differ from the files its origin resolution reads")
        for conflict in demonstrated:
            path = conflict.get("witness_path")
            if not path or not (run_dir / path).is_file():
                problems.append("demonstrated conflict without its witness program file")
            if not conflict.get("witness_sha256"):
                problems.append("demonstrated conflict without the witness digest")
            if not conflict.get("operation_uuid"):
                problems.append("demonstrated conflict without the sandbox operation that executed the witness")
            if conflict.get("exit_code") != WITNESS_EXIT_CODE or conflict.get("timed_out"):
                problems.append(f"demonstrated conflict without exit code {WITNESS_EXIT_CODE} (or it timed out)")
            if not any(line.startswith(WITNESS_MARKER) for line in (conflict.get("stdout_tail") or "").splitlines()):
                problems.append(f"demonstrated conflict without a {WITNESS_MARKER} line in the recorded output")
            if not conflict.get("requirement_ids"):
                problems.append("demonstrated conflict names no requirement")
        return problems
    gates = bundle.get("gates") or {}
    verification = bundle.get("verification") or {}
    raw = raw or {}
    if gates:
        # every recorded gate must have the stage record it summarises; a gate whose stage record vanished is not evidence (R5-02)
        stage_of = {"existing_suite": verification.get("existing"), "sealed_binding": verification.get("binding"), "heldout_suite": verification.get("heldout"),
                    "mutation": ((bundle.get("breaker") or {}).get("mutation")), "adversarial_tests": ((bundle.get("breaker") or {}).get("adversarial")),
                    "drift_audit": bundle.get("drift")}
        for name, gate in gates.items():
            if gate.get("skipped"):
                continue
            if name in stage_of and not stage_of[name]:
                problems.append(f"gate {name} has no stage record")
    if verdict != "VERIFIED":
        return problems
    missing_gates = [g for g in GATE_INVENTORY if g not in gates]
    task_heldout = bool(task.get("heldout_tests_sha256"))
    if task_heldout and "heldout_suite" not in gates:
        missing_gates.append("heldout_suite")
    if missing_gates:
        problems.append("gate inventory incomplete: " + ", ".join(missing_gates))
    # The repository's own suite always runs on the candidate; its record and, in bound mode, its raw result are mandatory, and
    # the mode comes from the execution record of the checkpoint, not from the surviving stage record (R5-02).
    mode = ((bundle.get("execution") or {}).get("suite_binding") or {}).get("mode")
    if mode not in ("bound", "stdout"):
        problems.append("execution record without the suite binding mode")
    existing = verification.get("existing")
    if not isinstance(existing, dict):
        problems.append("existing-suite stage record missing")
    else:
        if not existing.get("all_passed"):
            problems.append("existing-suite stage record does not say the suite passed")
        if mode and existing.get("evidence_class") != mode:
            problems.append(f"existing-suite evidence class {existing.get('evidence_class')!r} differs from the recorded binding mode {mode!r}")
        if mode == "bound":
            if raw.get("existing") is None:
                problems.append("raw existing-suite result missing for a bound suite")
            if not (existing.get("binding") or {}).get("ok"):
                problems.append("existing-suite binding missing or not ok for a bound suite")
            if not existing.get("modules"):
                problems.append("existing-suite record names no modules for a bound suite")
        elif mode == "stdout" and not existing.get("operation_uuid"):
            problems.append("existing-suite record without the sandbox operation that ran it")
    heldout = verification.get("heldout")
    if task_heldout:
        if not isinstance(heldout, dict):
            problems.append("held-out stage record missing although the frozen task declares held-out tests")
        else:
            if not heldout.get("all_passed"):
                problems.append("held-out stage record does not say the suite passed")
            if heldout.get("evidence_class") == "bound":
                if raw.get("heldout") is None:
                    problems.append("raw held-out result missing for a bound held-out suite")
                if not (heldout.get("binding") or {}).get("ok"):
                    problems.append("held-out binding missing or not ok for a bound held-out suite")
            elif not heldout.get("operation_uuid"):
                problems.append("held-out record without the sandbox operation that ran it")
    elif heldout is not None or "heldout_suite" in gates:
        problems.append("held-out evidence recorded although the frozen task declares no held-out tests")
    if not isinstance(verification.get("sealed"), dict):
        problems.append("sealed stage record missing")
    for name, gate in gates.items():
        if gate.get("skipped"):
            problems.append(f"gate {name} skipped in a VERIFIED bundle")
        elif not gate.get("ok"):
            problems.append(f"gate {name} failed in a VERIFIED bundle")
    candidate = bundle.get("candidate") or {}
    if candidate.get("scope_ok") is not True or candidate.get("implementer_finished") is not True:
        problems.append("candidate facts (scope_ok, implementer_finished) are not both true")
    if not (candidate.get("changed_paths") or candidate.get("deleted_paths")):
        problems.append("VERIFIED without any changed path")
    sealed = bundle.get("sealed_tests") or {}
    if not sealed.get("path") or not (run_dir / sealed["path"]).is_file() or not sealed.get("sha256") or not sealed.get("expected_ids"):
        problems.append("sealed module, digest or expected ids missing")
    if not (bundle.get("red_run") or {}).get("ran"):
        problems.append("red check record missing")
    if raw.get("red") is None:
        problems.append("raw red-check result missing")
    corrected_sealed = verification.get("corrected")
    if gates.get("sealed_binding", {}).get("corrected"):
        if not corrected_sealed:
            problems.append("sealed gate marked corrected without the correction record")
        else:
            if raw.get("sealed_corrected") is None:
                problems.append("raw result of the corrected sealed module missing")
            if raw.get("sealed_corrected_base") is None or not (corrected_sealed.get("base_rerun") or {}).get("binding"):
                problems.append("base evidence of the sealed correction missing (raw result or binding)")
    if raw.get("sealed") is None or verification.get("binding") is None:
        problems.append("raw sealed result or its binding missing")
    else:
        checks = (verification.get("binding") or {}).get("checks") or {}
        if checks.get("verifier_isolation_active") is not True:
            problems.append("sealed binding does not record isolation as active")
        if checks.get("supervisor_cleanup_complete") is False:
            problems.append("sealed binding records an incomplete supervisor cleanup")
        if not gates.get("sealed_binding", {}).get("corrected") and not (verification.get("binding") or {}).get("ok"):
            problems.append("sealed binding failed in a VERIFIED bundle")
    breaker = bundle.get("breaker") or {}
    adversarial = breaker.get("adversarial") or {}
    if not adversarial.get("sha256") or not (run_dir / "breaker_tests.py").is_file():
        problems.append("adversarial module or its digest missing")
    if raw.get("adversarial") is None:
        problems.append("raw adversarial result missing")
    if gates.get("adversarial_tests", {}).get("corrected"):
        corrected_adv = adversarial.get("corrected") or {}
        if not corrected_adv:
            problems.append("adversarial gate marked corrected without the correction record")
        else:
            if raw.get("adversarial_corrected") is None:
                problems.append("raw result of the corrected adversarial module missing")
            if raw.get("adversarial_corrected_base") is None or not (corrected_adv.get("base_rerun") or {}).get("binding"):
                problems.append("base evidence of the adversarial correction missing (raw result or binding)")
            mutant_reruns = [m for m in corrected_adv.get("mutant_reruns") or [] if m.get("corrected_tests_failing")]
            if mutant_reruns and any(m.get("mutant") not in (raw.get("adversarial_corrected_mutants") or {}) for m in mutant_reruns):
                problems.append("raw result of a discriminating mutant re-run missing")
    mutation = breaker.get("mutation") or {}
    evaluated = [m for m in mutation.get("mutants") or [] if m.get("status") in ("killed", "survived")]
    raw_mutants = raw.get("mutants") if isinstance(raw.get("mutants"), dict) else {}
    lost = [m["id"] for m in evaluated if m.get("id") not in raw_mutants]
    if lost:
        problems.append(f"raw results missing for {len(lost)} evaluated mutant(s)")
    for m in evaluated:
        if not (run_dir / f"mutants_{m.get('id')}.py").is_file():
            problems.append(f"mutant source mutants_{m.get('id')}.py missing")
            break
    audit = bundle.get("contract_audit") or {}
    if not audit or audit.get("outcome") in (None, "not run"):
        problems.append("contract audit record missing")
    elif audit.get("outcome") == "contradiction demonstrated":
        problems.append("VERIFIED although the contract audit demonstrated a contradiction")
    return problems


def check_run_dir(run_dir: Path, report: Report) -> dict:
    run_dir = Path(run_dir)
    bundle_path = run_dir / "proof_bundle.json"
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"proof_bundle.json unreadable: {error}") from None
    report.add("bundle_parses", True, f"run {bundle.get('run_id')} verdict {(bundle.get('verdict') or {}).get('verdict')}")
    protocol = protocol_version(bundle)
    current = protocol is not None and protocol >= 2
    if protocol is None:
        recorded_version = str((bundle.get("provenance") or {}).get("attest_version") or "")
        try:
            version_tuple = tuple(int(part) for part in recorded_version.split(".")[:3])
        except ValueError:
            version_tuple = ()
        if version_tuple >= (0, 5, 0):
            # the protocol exists since 0.5.0: a bundle of that version without the field is downgraded, not historical
            report.add("evidence_protocol", False, f"the bundle records Attest {recorded_version} but declares no evidence protocol; a downgraded protocol claim is not accepted as a current bundle")
        else:
            report.add("evidence_protocol", None, "no evidence protocol declared: a historical bundle (recorded before Attest 0.5.0), checked for internal consistency only "
                       "(checks that cannot run are warnings; it never receives the fully-verified badge)")
    elif protocol > EVIDENCE_PROTOCOL_VERSION:
        report.add("evidence_protocol", False, f"evidence protocol {protocol} is newer than this checker supports ({EVIDENCE_PROTOCOL_VERSION})")
    else:
        report.add("evidence_protocol", True, f"evidence protocol version {protocol}: the complete evidence for the verdict is required")
    redaction_path = run_dir / REDACTION_FILE
    if redaction_path.is_file():
        try:
            redaction = json.loads(redaction_path.read_text(encoding="utf-8"))
            files = redaction.get("files") or []
            report.add("redacted_export", True, f"this is a redacted public copy of run {redaction.get('source_run_id')}: {len(files)} file(s) rewritten "
                       f"({', '.join(f['path'] for f in files)[:160]}); the manifest checked below is the export's own, traced to the original manifest "
                       f"{(redaction.get('source_manifest_sha256') or 'none (the original had no manifest)')[:16]}; the original is kept privately")
        except (json.JSONDecodeError, OSError) as error:
            report.add("redacted_export", False, f"{REDACTION_FILE} unreadable: {error}")

    # 1. manifest: digests, completeness, well-formed listing, no links (CORE-07)
    manifest_path = run_dir / MANIFEST_FILE
    links = list_symlinks(run_dir)
    report.add("no_symlinks", not links, "no symbolic link in the run directory" if not links else "symbolic link(s) in the run directory are never part of a bundle: " + ", ".join(links)[:200])
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            manifest = None
            report.add("manifest_parses", False, f"manifest.json unreadable: {error}")
        if manifest:
            result = verify_manifest(run_dir, manifest)
            strict_manifest = current or (result.get("version") or 0) >= 2
            detail = f"{result['checked']} file(s) checked"
            if result["mismatched"]:
                detail += "; digest or size mismatch: " + ", ".join(m["path"] for m in result["mismatched"])
            if result["missing"]:
                detail += "; missing: " + ", ".join(result["missing"])
            if result["symlinks"]:
                detail += "; listed entries that are links: " + ", ".join(result["symlinks"])[:160]
            report.add("manifest_digests", result["ok"], detail)
            if result["unlisted"]:
                report.add("manifest_complete", False, "files not listed in the manifest: " + ", ".join(result["unlisted"])[:300],
                           severity="error" if strict_manifest else "warning")
            else:
                report.add("manifest_complete", True, "every file in the run directory is listed")
            report.add("manifest_entries", result["entries_ok"], "the listing is well formed (unique contained paths, correct count and total, sha256, only the manifest excluded)"
                       if result["entries_ok"] else "manifest listing problems: " + "; ".join(result["entry_problems"])[:300])
            report.add("manifest_run_id", manifest.get("run_id") == bundle.get("run_id"),
                       f"manifest run_id {manifest.get('run_id')} vs bundle {bundle.get('run_id')}")
    else:
        computed = build_manifest(run_dir, bundle.get("run_id"))
        report.add("manifest_present", False if current else None,
                   f"no manifest.json ({'required by the evidence protocol' if current else 'bundle predates milestone M2'}; integrity not checkable); "
                   f"{computed['file_count']} file(s) present, digests computed but nothing to compare against")

    # 2. digests inside the bundle
    task = bundle.get("task") or {}
    recomputed = _recompute_spec_digest(task)
    if recomputed:
        report.add("task_spec_digest", recomputed == task.get("spec_sha256"), f"recomputed {recomputed[:16]} vs recorded {str(task.get('spec_sha256'))[:16]}")
    sealed = bundle.get("sealed_tests") or {}
    verification = bundle.get("verification") or {}
    if sealed.get("path"):
        sealed_path = run_dir / sealed["path"]
        if sealed_path.is_file():
            src = sealed_path.read_text(encoding="utf-8")
            digest = _sha_text(src)
            report.add("sealed_file_digest", digest == sealed.get("sha256"), f"{sealed['path']} sha256 {digest[:16]} vs recorded {str(sealed.get('sha256'))[:16]}")
            if verification.get("sealed_sha256_injected"):
                report.add("sealed_digest_injected", verification["sealed_sha256_injected"] == sealed.get("sha256"),
                           "the digest injected into the verify branch equals the sealed module digest")
            try:
                ids = static_test_ids(src)
                if "expected_ids" in sealed:
                    report.add("sealed_static_ids", set(ids) == set(sealed.get("expected_ids") or []),
                               f"{len(ids)} statically discovered test ids vs {len(sealed.get('expected_ids') or [])} recorded")
                else:
                    report.add("sealed_static_ids", None, f"{len(ids)} statically discovered test ids; the bundle records none (schema predates expected_ids)")
            except SyntaxError as error:
                report.add("sealed_static_ids", False, f"sealed module does not parse: {error}")
        else:
            report.add("sealed_file_digest", False, f"{sealed['path']} missing from the run directory")
    adversarial = ((bundle.get("breaker") or {}).get("adversarial") or {})
    if adversarial.get("sha256"):
        adv_path = run_dir / "breaker_tests.py"
        if adv_path.is_file():
            src = adv_path.read_text(encoding="utf-8")
            digest = _sha_text(src)
            report.add("adversarial_file_digest", digest == adversarial["sha256"], f"breaker_tests.py sha256 {digest[:16]} vs recorded {adversarial['sha256'][:16]}")
            try:
                ids = static_test_ids(src, "test_breaker")
                report.add("adversarial_static_ids", set(ids) == set(adversarial.get("expected_ids") or []),
                           f"{len(ids)} statically discovered test ids vs {len(adversarial.get('expected_ids') or [])} recorded")
            except SyntaxError as error:
                report.add("adversarial_static_ids", False, f"breaker_tests.py does not parse: {error}")
        else:
            report.add("adversarial_file_digest", False, "breaker_tests.py missing from the run directory")
    candidate = bundle.get("candidate") or {}
    patch_path = run_dir / "candidate.patch"
    if patch_path.is_file() and candidate.get("diff") is not None:
        report.add("candidate_patch_matches", patch_path.read_text(encoding="utf-8") == candidate["diff"], "candidate.patch equals the diff recorded in the bundle")

    # 2b. corrected generated-test modules (arbitration): digest, scope rule and classification ids, recomputed (CORE-05)
    corrected_records = {}
    if verification.get("corrected"):
        corrected_records["sealed"] = (verification["corrected"], run_dir / (sealed.get("path") or "sealed/test_sealed.py"), "test_sealed")
    if adversarial.get("corrected"):
        corrected_records["adversarial"] = (adversarial["corrected"], run_dir / "breaker_tests.py", "test_breaker")
    arbitration_modules = {m.get("module"): m for m in ((bundle.get("arbitration") or {}).get("modules") or [])}
    for label, (record, original_path, module_name) in corrected_records.items():
        corrected_path = run_dir / (record.get("path") or f"arbitration/{label}_corrected.py")
        if not corrected_path.is_file() or not original_path.is_file():
            report.add(f"{label}_corrected_module", False, f"corrected or original module missing ({corrected_path.name}, {original_path.name})")
            continue
        corrected_src = corrected_path.read_text(encoding="utf-8")
        original_src = original_path.read_text(encoding="utf-8")
        report.add(f"{label}_corrected_digest", _sha_text(corrected_src) == record.get("sha256"),
                   f"{corrected_path.name} sha256 {_sha_text(corrected_src)[:16]} vs recorded {str(record.get('sha256'))[:16]}")
        failing_ids = set(record.get("original_failing") or [])
        try:
            problems, changed = correction_problems(original_src, corrected_src, module_name, failing_ids)
            same_changed = set(record.get("changed_tests") or []) == changed
            report.add(f"{label}_correction_scope", not problems and same_changed and bool(changed),
                       ("the correction keeps the test set, changes only the failing tests' bodies and nothing else "
                        f"({', '.join(sorted(changed))[:160]})" if not problems else "scope rule violated: " + "; ".join(problems)[:300])
                       + ("" if same_changed else f"; recorded changed tests {record.get('changed_tests')} differ from the recomputed {sorted(changed)}"))
        except SyntaxError as error:
            report.add(f"{label}_correction_scope", False, f"a module does not parse: {error}")
        module_record = arbitration_modules.get(label)
        if module_record is not None:
            id_problems, _ = classification_problems(module_record.get("classifications") or [], failing_ids)
            report.add(f"{label}_classification_ids", not id_problems,
                       "the arbiter classified exactly the failing tests" if not id_problems else "classification ids do not match the failing tests: " + "; ".join(id_problems)[:200])
    audit = bundle.get("contract_audit") or {}
    for conflict in audit.get("conflicts") or []:
        if conflict.get("witness_path"):
            witness_path = run_dir / conflict["witness_path"]
            if witness_path.is_file():
                digest = _sha_text(witness_path.read_text(encoding="utf-8"))
                report.add("witness_digest", digest == conflict.get("witness_sha256"), f"{conflict['witness_path']} sha256 {digest[:16]} vs recorded {str(conflict.get('witness_sha256'))[:16]}")
            else:
                report.add("witness_digest", False, f"{conflict['witness_path']} missing from the run directory")
            if protocol is not None and protocol >= 4 and witness_path.is_file():
                fresh = analyze_witness(witness_path.read_text(encoding="utf-8"), Repository.from_bundle(run_dir, bundle.get("task") or {}))
                recorded = conflict.get("witness_language") or {}
                agrees = (recorded.get("version") == WITNESS_LANGUAGE and bool(recorded.get("conforms")) == fresh["conforms"]
                          and bool(conflict.get("witness_constrained")) == fresh["conforms"]
                          and (recorded.get("repository_files") or {}) == fresh["repository_files"])
                report.add("witness_language_rederived", agrees,
                           f"{conflict['witness_path']}: {WITNESS_LANGUAGE} analysis repeated from the witness and {len(fresh['repository_files'])} "
                           f"repository cop{'y' if len(fresh['repository_files']) == 1 else 'ies'}: "
                           + ("conforms" if fresh["conforms"] else "outside the language (" + "; ".join(fresh["problems"][:1])[:160] + ")")
                           + ("" if agrees else f"; the recorded analysis says conforms={recorded.get('conforms')!r}, witness_constrained="
                                                f"{conflict.get('witness_constrained')!r}, files {sorted(recorded.get('repository_files') or {})}"))
            if conflict.get("demonstrated"):
                lines = [line for line in (conflict.get("stdout_tail") or "").splitlines() if line.startswith(WITNESS_MARKER)]
                names_claim = any(i in line for line in lines for i in (conflict.get("requirement_ids") or []))
                report.add("witness_demonstration_recorded", conflict.get("exit_code") == WITNESS_EXIT_CODE and bool(lines) and (names_claim or not current)
                           and bool(conflict.get("operation_uuid")) and not conflict.get("timed_out"),
                           f"a demonstrated conflict records exit code {WITNESS_EXIT_CODE}, a {WITNESS_MARKER} line naming a claimed requirement and its operation "
                           f"(recorded exit {conflict.get('exit_code')}, operation {str(conflict.get('operation_uuid'))[:12]})")
    if (bundle.get("verdict") or {}).get("verdict") == "INFEASIBLE":
        demonstrated = any(c.get("demonstrated") for c in audit.get("conflicts") or [])
        if demonstrated or current or audit:
            report.add("infeasible_has_demonstrated_witness", demonstrated,
                       "an INFEASIBLE verdict rests on at least one demonstrated witness" if demonstrated else
                       ("INFEASIBLE without a demonstrated witness" + ("" if audit else " or any contract audit record")))
        else:
            report.add("infeasible_has_demonstrated_witness", None,
                       "INFEASIBLE recorded before the contract audit existed (historical bundle, before 19 Oct 2026): the specification's "
                       "own judgement ended the run; no executed witness can be checked")

    # 3. bindings from raw supervisor results
    raw_path = run_dir / RAW_FILE
    raw = None
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            report.add("raw_results_parse", False, f"{RAW_FILE} unreadable: {error}")
    if raw is None:
        if not raw_path.is_file():
            report.add("raw_results_present", False if current else None,
                       f"no {RAW_FILE}: bindings cannot be recomputed ({'required by the evidence protocol' if current else 'bundle predates milestone M2'})")
    else:
        sealed_v = verification.get("sealed") or {}
        if raw.get("sealed") is not None and verification.get("binding") is not None:
            recomputed_binding = bind_verification(raw["sealed"], verification.get("expected_ids") or [], sealed.get("sha256"), sealed_v.get("nonce"))
            same, diff = _binding_matches(recomputed_binding, verification["binding"], current)
            report.add("sealed_binding_recomputed", same, "binding checks recomputed from the raw supervisor result " + ("match the record" if same else f"differ: {', '.join(diff)}"))
            report.add("sealed_outcomes_match_raw", _outcomes(summarize(raw["sealed"])["tests"]) == _outcomes(sealed_v.get("tests")),
                       "per-test outcomes in the bundle equal those in the raw result")
        elif "sealed" in raw and raw.get("sealed") is None and verification.get("binding") is not None:
            report.add("sealed_binding_recomputed", (verification["binding"].get("checks") or {}).get("result_file_present") is False,
                       "no raw sealed result; the recorded binding must say the result file was absent")
        for label, key, module_record in (("sealed", "sealed_corrected", verification.get("corrected")), ("adversarial", "adversarial_corrected", adversarial.get("corrected"))):
            if not module_record:
                continue
            if raw.get(key) is not None:
                recomputed_binding = bind_verification(raw[key], module_record.get("expected_ids") or [], module_record.get("sha256"), module_record.get("nonce"))
                same, diff = _binding_matches(recomputed_binding, module_record.get("binding") or {}, current)
                report.add(f"{label}_corrected_binding_recomputed", same, f"binding of the corrected {label} module recomputed from the raw result " + ("matches the record" if same else f"differs: {', '.join(diff)}"))
                report.add(f"{label}_corrected_outcomes_match_raw", _outcomes(summarize(raw[key])["tests"]) == _outcomes((module_record.get("summary") or {}).get("tests")),
                           f"per-test outcomes of the corrected {label} module equal those in the raw result")
                report.add(f"{label}_corrected_passes", bool((module_record.get("summary") or {}).get("all_passed")) and bool((module_record.get("binding") or {}).get("ok")),
                           f"the corrected {label} module passes on the candidate with the binding intact")
            # discrimination evidence (CORE-01): the base re-run and any mutant re-run are recomputed from their raw results
            base_record = module_record.get("base_rerun") or {}
            base_raw = raw.get(f"{key}_base")
            if base_raw is not None and base_record.get("binding") is not None:
                recomputed_base = base_discrimination(base_raw, {"summary_line": base_record.get("summary_line"), "failing": base_record.get("failing")},
                                                      base_record.get("expected_ids") or module_record.get("expected_ids") or [], module_record.get("sha256"),
                                                      base_record.get("nonce"), sorted(module_record.get("changed_tests") or []), label)
                same_b = (recomputed_base["outcomes"] == base_record.get("outcomes") and recomputed_base["structural_problems"] == base_record.get("structural_problems")
                          and recomputed_base["corrected_tests_failing_on_base"] == base_record.get("corrected_tests_failing_on_base"))
                report.add(f"{label}_base_evidence_recomputed", same_b, f"the base re-run of the corrected {label} module recomputed from its raw result "
                           + ("matches the record" if same_b else "differs from the record"))
                mutant_caught = any(m.get("corrected_tests_failing") for m in module_record.get("mutant_reruns") or [])
                discriminates = bool(recomputed_base["discrimination"]) or (label == "adversarial" and mutant_caught)
                report.add(f"{label}_discrimination_recomputed", discriminates == bool(module_record.get("discrimination")) and (discriminates or not module_record.get("discrimination")),
                           f"discrimination of the corrected {label} module recomputed from authentic results: {'holds' if discriminates else 'does not hold'}; "
                           f"recorded: {module_record.get('discrimination') or 'none'}")
            elif current:
                report.add(f"{label}_base_evidence_recomputed", False, f"the base re-run evidence of the corrected {label} module is missing (raw result or binding)")
            else:
                report.add(f"{label}_base_evidence_recomputed", None, f"the base re-run of the corrected {label} module carries no recomputable evidence (recorded before 19 Oct 2026)")
            reruns_raw = raw.get(f"{key}_mutants") if isinstance(raw.get(f"{key}_mutants"), dict) else {}
            for rerun in module_record.get("mutant_reruns") or []:
                mutant_id = rerun.get("mutant")
                if rerun.get("binding") is None or mutant_id not in reruns_raw:
                    if current and rerun.get("corrected_tests_failing"):
                        report.add(f"{label}_mutant_rerun_recomputed", False, f"mutant re-run {mutant_id} carries no recomputable evidence")
                    continue
                recomputed_m = mutant_rerun_discrimination(reruns_raw[mutant_id], {"summary_line": rerun.get("summary_line")}, rerun.get("expected_ids") or module_record.get("expected_ids") or [],
                                                           module_record.get("sha256"), rerun.get("nonce"), sorted(module_record.get("changed_tests") or []))
                same_m = recomputed_m["corrected_tests_failing"] == rerun.get("corrected_tests_failing") and recomputed_m["structural_problems"] == rerun.get("structural_problems")
                report.add(f"{label}_mutant_rerun_recomputed", same_m, f"mutant re-run {mutant_id} recomputed from its raw result " + ("matches the record" if same_m else "differs from the record"))
        if adversarial.get("sha256") and raw.get("adversarial") is not None:
            adv_summary = adversarial.get("summary") or {}
            recomputed_binding = bind_verification(raw["adversarial"], adversarial.get("expected_ids") or [], adversarial["sha256"], adv_summary.get("nonce"))
            same, diff = _binding_matches(recomputed_binding, adversarial.get("binding") or {}, current)
            report.add("adversarial_binding_recomputed", same, "adversarial binding recomputed from the raw result " + ("matches the record" if same else f"differs: {', '.join(diff)}"))
            report.add("adversarial_outcomes_match_raw", _outcomes(summarize(raw["adversarial"])["tests"]) == _outcomes(adv_summary.get("tests")),
                       "per-test adversarial outcomes in the bundle equal those in the raw result")
        for name in ("existing", "heldout"):
            record = verification.get(name) or {}
            if record.get("evidence_class") == "bound" and raw.get(name) is not None:
                modules = record.get("modules") or []
                if not all("ids" in m for m in modules):
                    report.add(f"{name}_binding_recomputed", None, f"{name} modules carry no test ids (bundle predates milestone M2); binding not recomputed")
                    continue
                recomputed_binding = bind_modules(raw[name], modules, record.get("nonce"))
                same, diff = _binding_matches(recomputed_binding, record.get("binding") or {}, current)
                report.add(f"{name}_binding_recomputed", same, f"{name} suite binding recomputed from the raw result " + ("matches the record" if same else f"differs: {', '.join(diff)}"))
                report.add(f"{name}_outcomes_match_raw", _outcomes(summarize(raw[name])["tests"]) == _outcomes(record.get("tests")),
                           f"per-test {name} outcomes in the bundle equal those in the raw result")
        red = bundle.get("red_run") or {}
        if raw.get("red") is not None and red:
            report.add("red_outcomes_match_raw", _outcomes(summarize(raw["red"])["tests"]) == _outcomes(red.get("tests")),
                       "red-check outcomes in the bundle equal those in the raw result")
            report.add("red_check_failed_on_base", (red.get("failing") or 0) > 0, f"{red.get('failing')} of {red.get('ran')} sealed tests failed on the unmodified base")
        # mutants (CORE-03): every evaluated mutant's status is recomputed from its raw result under the recorded policy
        mutation = (bundle.get("breaker") or {}).get("mutation") or {}
        raw_mutants = raw.get("mutants") if isinstance(raw.get("mutants"), dict) else None
        if mutation.get("mutants") and raw_mutants is not None:
            expected_ids = (verification.get("corrected") or {}).get("expected_ids") if (bundle.get("breaker") or {}).get("after_sealed_correction") else sealed.get("expected_ids")
            module_sha = (verification.get("corrected") or {}).get("sha256") if (bundle.get("breaker") or {}).get("after_sealed_correction") else sealed.get("sha256")
            mismatched = []
            counts = {"killed": 0, "survived": 0, "unknown": 0}
            for m in mutation["mutants"]:
                mid = m.get("id")
                if mid in raw_mutants:
                    result = raw_mutants[mid]
                    binding = bind_verification(result, expected_ids or [], module_sha, m.get("nonce"), canary=False)
                    status, _, _ = classify_mutant_run(result, binding, expected_ids or [])
                else:
                    status = "unknown" if m.get("status") == "unknown" else "missing"
                counts[status if status in counts else "unknown"] += 1
                if status != m.get("status"):
                    mismatched.append(f"{mid}: recorded {m.get('status')}, recomputed {status}")
            report.add("mutants_recomputed", not mismatched, f"{len(mutation['mutants'])} mutant(s) reclassified from their raw results "
                       + ("match the record" if not mismatched else "differ: " + "; ".join(mismatched)[:300]))
            evaluated = counts["killed"] + counts["survived"]
            score = round(counts["killed"] / evaluated, 3) if evaluated else None
            same_score = (mutation.get("killed"), mutation.get("survived"), mutation.get("unknown"), mutation.get("score")) == (counts["killed"], counts["survived"], counts["unknown"], score)
            report.add("mutation_score_recomputed", same_score, f"killed {counts['killed']}, survived {counts['survived']}, unknown {counts['unknown']}, score {score} "
                       + ("match the record" if same_score else f"vs recorded {mutation.get('killed')}/{mutation.get('survived')}/{mutation.get('unknown')} score {mutation.get('score')}"))
        elif mutation.get("mutants") and current:
            report.add("mutants_recomputed", False, "the evidence protocol requires the raw result of every evaluated mutant; none is recorded")

    # 4. ledger totals
    ledger = bundle.get("ledger") or {}
    calls = ledger.get("model_calls") or []
    totals = ledger.get("totals") or {}
    if totals:
        problems = []
        if totals.get("model_calls") != len(calls):
            problems.append(f"model_calls {totals.get('model_calls')} vs {len(calls)} records")
        if totals.get("model_calls_failed") is not None and totals["model_calls_failed"] != sum(1 for c in calls if not c.get("ok")):
            problems.append("model_calls_failed")
        for key in ("tokens_in", "tokens_out", "tokens_cached"):
            if totals.get(key) is not None and totals[key] != sum(c.get(key) or 0 for c in calls):
                problems.append(key)
        usd = [c["cost_usd"] for c in calls if c.get("cost_usd") is not None]
        recorded_usd = totals.get("cost_usd")
        if (recorded_usd is None) != (not usd) or (usd and abs(round(sum(usd), 6) - recorded_usd) > 1e-6):
            problems.append(f"cost_usd {recorded_usd} vs {round(sum(usd), 6) if usd else None}")
        if totals.get("cost_usd_committed") is not None:
            committed = sum(c["cost_usd"] if c.get("cost_usd") is not None else (c.get("reserved_usd") or 0.0) for c in calls)
            committed += sum(r.get("reserved_usd") or 0.0 for r in ledger.get("open_reservations") or [])
            if abs(round(committed, 6) - totals["cost_usd_committed"]) > 1e-6:
                problems.append(f"cost_usd_committed {totals['cost_usd_committed']} vs {round(committed, 6)}")
        if totals.get("sandbox_operations") is not None and totals["sandbox_operations"] != len(ledger.get("sandbox_ops") or []):
            problems.append("sandbox_operations")
        report.add("ledger_totals", not problems, "totals recomputed from the individual records " + ("match" if not problems else "differ: " + "; ".join(problems)))

    # 5. gates against stage records, then the verdict rule
    gates = bundle.get("gates") or {}
    mismatches = []
    existing = verification.get("existing") or {}
    if "existing_suite" in gates and existing:
        if bool(gates["existing_suite"].get("ok")) != bool(existing.get("all_passed")):
            mismatches.append("existing_suite")
    elif "existing_suite" in gates and current and not gates["existing_suite"].get("skipped"):
        mismatches.append("existing_suite (gate without a stage record)")
    if "sealed_binding" in gates and verification.get("binding") is not None:
        if gates["sealed_binding"].get("corrected"):
            corrected = verification.get("corrected") or {}
            expected_ok = bool((corrected.get("summary") or {}).get("all_passed")) and bool((corrected.get("binding") or {}).get("ok")) and bool(corrected.get("discrimination"))
            if bool(gates["sealed_binding"].get("ok")) != expected_ok:
                mismatches.append("sealed_binding (corrected)")
        elif bool(gates["sealed_binding"].get("ok")) != bool(verification["binding"].get("ok")):
            mismatches.append("sealed_binding")
    heldout = verification.get("heldout")
    if "heldout_suite" in gates and heldout:
        if bool(gates["heldout_suite"].get("ok")) != bool(heldout.get("all_passed")):
            mismatches.append("heldout_suite")
    elif "heldout_suite" in gates and current and not gates["heldout_suite"].get("skipped"):
        mismatches.append("heldout_suite (gate without a stage record)")
    if "adversarial_tests" in gates and adversarial and not gates["adversarial_tests"].get("skipped"):
        if gates["adversarial_tests"].get("corrected"):
            corrected = adversarial.get("corrected") or {}
            expected_ok = bool((corrected.get("summary") or {}).get("all_passed")) and bool((corrected.get("binding") or {}).get("ok")) and bool(corrected.get("discrimination"))
            if bool(gates["adversarial_tests"].get("ok")) != expected_ok:
                mismatches.append("adversarial_tests (corrected)")
        elif "summary" in adversarial or adversarial.get("unusable"):
            expected_ok = (not adversarial.get("unusable")) and bool((adversarial.get("summary") or {}).get("all_passed")) and bool((adversarial.get("binding") or {}).get("ok"))
            if bool(gates["adversarial_tests"].get("ok")) != expected_ok:
                mismatches.append("adversarial_tests")
        elif adversarial.get("skipped"):
            report.add("adversarial_gate_fail_open", False, f"the adversarial gate was recorded as {'passed' if gates['adversarial_tests'].get('ok') else 'failed'} although no adversarial "
                       f"test ran ({str(adversarial['skipped'])[:100]}); this fail-open path existed before milestone M1 and the verdict of this bundle rests on the other gates",
                       severity="warning")
        else:
            report.add("adversarial_gate_schema", None, "the adversarial record predates the summary/binding schema; its gate is not compared")
    drift = bundle.get("drift") or {}
    if "drift_audit" in gates and "drift_score" in drift and drift.get("threshold") is not None:
        expected_ok = float(drift.get("drift_score") or 0.0) < float(drift["threshold"])
        if bool(gates["drift_audit"].get("ok")) != expected_ok:
            mismatches.append("drift_audit")
    mutation = (bundle.get("breaker") or {}).get("mutation") or {}
    if "mutation" in gates and mutation and not gates["mutation"].get("skipped") and mutation.get("evaluated"):
        if mutation.get("score") is not None and mutation.get("threshold") is not None:
            below = float(mutation["score"]) < float(mutation["threshold"])
            if below and gates["mutation"].get("ok"):
                mismatches.append("mutation")
    if gates:
        report.add("gates_match_stage_records", not mismatches, "every gate agrees with the stage record it summarises" if not mismatches else "gates disagree with their stage records: " + ", ".join(mismatches))
    if "gates" not in bundle:
        report.add("verdict_derivation", None, "the bundle records no gates at all (schema predates gate records); the verdict rule cannot be re-derived")
    else:
        derived = expected_verdict(bundle)
        report.add("verdict_derivation", derived["consistent"], derived["detail"] + (f" (blocking: {', '.join(derived.get('blocking') or []) or 'nothing'})" if derived.get("applicable") else ""))
        legacy_flags = bool((bundle.get("verdict") or {}).get("cleared_by_arbitration")) or bool((bundle.get("arbitration") or {}).get("applied") and not (bundle.get("arbitration") or {}).get("applied_to_gates") and (bundle.get("arbitration") or {}).get("cleared"))
        if legacy_flags:
            report.add("legacy_clearing_scope", legacy_clearing_allowed(bundle),
                       "the former explicit apply mode (cleared_by_arbitration) is honoured only for a historical bundle started before 19 Oct 2026"
                       + ("" if legacy_clearing_allowed(bundle) else "; this bundle is current or undated, so the flag has no effect on the derivation"),
                       severity="warning")
    recorded_verdict = (bundle.get("verdict") or {}).get("verdict")
    reasons = (bundle.get("verdict") or {}).get("reasons") or []
    if recorded_verdict == "VERIFIED":
        report.add("verified_has_no_reasons", not reasons, "a VERIFIED verdict carries no blocking reasons" if not reasons else f"VERIFIED with reasons recorded: {reasons[0][:120]}")
    elif recorded_verdict == "NEEDS HUMAN":
        report.add("hold_has_reasons", bool(reasons), "a NEEDS HUMAN verdict names at least one reason" if reasons else "NEEDS HUMAN without any recorded reason")
    if current:
        problems = required_evidence_problems(bundle, run_dir, raw, protocol)
        report.add("required_evidence", not problems, f"the complete evidence for a {recorded_verdict} verdict under evidence protocol {protocol} is present"
                   if not problems else "required evidence missing: " + "; ".join(problems)[:600])
    try:
        exhibits(bundle)
        decision(bundle)
        report.add("exhibits_render", True, "exhibits E1 to E7 and the decision render from the gates")
    except Exception as error:  # noqa: BLE001 - a rendering failure is itself a finding
        report.add("exhibits_render", False, f"{type(error).__name__}: {str(error)[:160]}")

    # 6. PROOF.md
    proof_path = run_dir / "PROOF.md"
    if proof_path.is_file():
        try:
            rendered = render_markdown(bundle)
            same = rendered == proof_path.read_text(encoding="utf-8")
            prov = bundle.get("provenance") or {}
            same_revision = (prov.get("attest_revision") or {}).get("digest") == attest_revision()["digest"]
            if same:
                report.add("proof_md_matches", True, "PROOF.md equals a fresh rendering of proof_bundle.json")
            elif same_revision:
                report.add("proof_md_matches", False, "PROOF.md differs from a fresh rendering although the bundle was produced by this Attest revision")
            else:
                report.add("proof_md_matches", None, "PROOF.md differs from a fresh rendering; the bundle was produced by a different Attest revision, so the rendering is not comparable (digests above still apply)")
        except Exception as error:  # noqa: BLE001
            report.add("proof_md_matches", False, f"PROOF.md could not be re-rendered: {type(error).__name__}: {str(error)[:160]}")
    else:
        report.add("proof_md_present", False, "PROOF.md missing", severity="error" if current else "warning")
    return bundle


def check_bundle(path: str | Path) -> dict:
    """Check a run directory or a zip. Returns the report dict (see Report.to_dict); raises CheckError for non-bundles."""
    report = Report(str(path))
    run_dir, temp = locate_run_dir(Path(path))
    try:
        bundle = check_run_dir(run_dir, report)
    finally:
        if temp:
            shutil.rmtree(temp, ignore_errors=True)
    out = report.to_dict()
    checks = {c["name"]: c for c in report.checks}
    out["run_id"] = bundle.get("run_id")
    out["verdict"] = (bundle.get("verdict") or {}).get("verdict")
    out["protocol"] = protocol_version(bundle)
    out["historical"] = out["protocol"] is None
    digests_ok = bool(checks.get("manifest_digests", {}).get("ok"))
    complete = bool(checks.get("manifest_complete", {}).get("ok")) and bool(checks.get("manifest_entries", {}).get("ok")) and bool(checks.get("no_symlinks", {}).get("ok"))
    out["manifest_present"] = "manifest_digests" in checks
    out["manifest_verified"] = digests_ok and complete  # the integrity badge needs correct digests AND a complete, well-formed listing (CORE-07)
    out["manifest_partial"] = digests_ok and not complete
    out["evidence_complete"] = (bool(checks.get("required_evidence", {}).get("ok")) if "required_evidence" in checks else None)
    out["fully_verified"] = bool(out["ok"] and out["manifest_verified"] and out["evidence_complete"])
    out["redacted_export"] = "redacted_export" in checks
    return out


def format_report(report: dict) -> str:
    if report.get("manifest_verified"):
        manifest_state = "manifest verified: integrity and complete listing"
    elif report.get("manifest_partial"):
        manifest_state = "manifest PARTIAL: digests match but the listing is incomplete or malformed"
    elif report.get("manifest_present"):
        manifest_state = "manifest MISMATCH"
    else:
        manifest_state = "no manifest: integrity not checkable"
    if report.get("historical"):
        protocol_state = "historical bundle (no evidence protocol): internal consistency only, never fully verified"
    else:
        protocol_state = (f"evidence protocol v{report.get('protocol')}: " + ("complete evidence" if report.get("evidence_complete") else "evidence INCOMPLETE"))
    state = f"{protocol_state}; {manifest_state}"
    if report.get("redacted_export"):
        state += "; redacted public copy"
    lines = [f"attest check {report['path']}", f"run {report.get('run_id')} verdict {report.get('verdict')} ({state})"]
    for check in report["checks"]:
        mark = "ok  " if check["ok"] else ("warn" if check["ok"] is None or check["severity"] == "warning" else "FAIL")
        lines.append(f"  {mark} {check['name']}: {check['detail']}")
    # the badge speaks about the RECORD (complete evidence for the recorded verdict, integrity intact), never about the patch:
    # an ERROR or NEEDS HUMAN bundle with complete evidence earns it just as a VERIFIED one does
    if report.get("fully_verified"):
        badge = f"OK, EVIDENCE COMPLETE for verdict {report.get('verdict')} (protocol v{report.get('protocol')}, manifest verified)"
    elif report.get("historical") and report["ok"]:
        badge = "OK (historical bundle, partial checks)"
    else:
        badge = "OK" if report["ok"] else "FAILED"
    lines.append(f"result: {badge} ({report['errors']} error(s), {report['warnings']} warning(s))")
    return "\n".join(lines)
