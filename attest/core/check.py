"""`attest check`: offline verification of a Proof Bundle (run directory or downloaded zip).

What it recomputes, without any network or sandbox access:
1. every artifact digest and size against manifest.json (a bundle without a manifest is reported as `no manifest`: its
   integrity cannot be checked, which is different from a mismatch);
2. the frozen task digest, the sealed and adversarial module digests and their statically discovered test ids;
3. the sealed, adversarial, existing and held-out bindings from the raw supervisor results in verify_raw.json, and the
   per-test outcomes the bundle summarises from them;
4. the ledger totals from the individual model calls;
5. the gate records against the stage records they summarise, and the gate-to-verdict rule;
6. PROOF.md, re-rendered from proof_bundle.json (compared byte for byte when the bundle was produced by this Attest revision).

Any mismatch is an error and the exit code is 1. Checks that cannot run on an older bundle are warnings. The tool never
re-executes sandbox runs; it establishes that the bundle is internally consistent and unchanged since its manifest was
written.

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
from .manifest import MANIFEST_FILE, build_manifest, verify_manifest
from .proof import render_markdown
from .provenance import attest_revision
from .sealed import bind_modules, bind_verification, static_test_ids, summarize
from .verdict import expected_verdict

RAW_FILE = "verify_raw.json"


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


def check_run_dir(run_dir: Path, report: Report) -> dict:
    run_dir = Path(run_dir)
    bundle_path = run_dir / "proof_bundle.json"
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"proof_bundle.json unreadable: {error}") from None
    report.add("bundle_parses", True, f"run {bundle.get('run_id')} verdict {(bundle.get('verdict') or {}).get('verdict')}")

    # 1. manifest
    manifest_path = run_dir / MANIFEST_FILE
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            manifest = None
            report.add("manifest_parses", False, f"manifest.json unreadable: {error}")
        if manifest:
            result = verify_manifest(run_dir, manifest)
            detail = f"{result['checked']} file(s) checked"
            if result["mismatched"]:
                detail += "; digest or size mismatch: " + ", ".join(m["path"] for m in result["mismatched"])
            if result["missing"]:
                detail += "; missing: " + ", ".join(result["missing"])
            report.add("manifest_digests", result["ok"], detail)
            if result["unlisted"]:
                report.add("manifest_complete", False, "files not listed in the manifest: " + ", ".join(result["unlisted"]), severity="warning")
            else:
                report.add("manifest_complete", True, "every file in the run directory is listed")
            report.add("manifest_run_id", manifest.get("run_id") == bundle.get("run_id"),
                       f"manifest run_id {manifest.get('run_id')} vs bundle {bundle.get('run_id')}")
    else:
        computed = build_manifest(run_dir, bundle.get("run_id"))
        report.add("manifest_present", None, f"no manifest.json (bundle predates milestone M2, integrity not checkable); {computed['file_count']} file(s) present, digests computed but nothing to compare against")

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

    # 3. bindings from raw supervisor results
    raw_path = run_dir / RAW_FILE
    raw = None
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            report.add("raw_results_parse", False, f"{RAW_FILE} unreadable: {error}")
    if raw is None:
        if raw_path.is_file():
            pass
        else:
            report.add("raw_results_present", None, f"no {RAW_FILE}: bindings cannot be recomputed (bundle predates milestone M2)")
    else:
        sealed_v = verification.get("sealed") or {}
        if raw.get("sealed") is not None and verification.get("binding") is not None:
            recomputed_binding = bind_verification(raw["sealed"], verification.get("expected_ids") or [], sealed.get("sha256"), sealed_v.get("nonce"))
            recorded = verification["binding"]
            same = recomputed_binding["checks"] == recorded.get("checks") and recomputed_binding["ok"] == recorded.get("ok")
            diff = [k for k in set(recomputed_binding["checks"]) | set(recorded.get("checks") or {}) if recomputed_binding["checks"].get(k) != (recorded.get("checks") or {}).get(k)]
            report.add("sealed_binding_recomputed", same, "binding checks recomputed from the raw supervisor result " + ("match the record" if same else f"differ: {', '.join(sorted(diff))}"))
            report.add("sealed_outcomes_match_raw", _outcomes(summarize(raw["sealed"])["tests"]) == _outcomes(sealed_v.get("tests")),
                       "per-test outcomes in the bundle equal those in the raw result")
        elif "sealed" in raw and raw.get("sealed") is None and verification.get("binding") is not None:
            report.add("sealed_binding_recomputed", (verification["binding"].get("checks") or {}).get("result_file_present") is False,
                       "no raw sealed result; the recorded binding must say the result file was absent")
        if adversarial.get("sha256") and raw.get("adversarial") is not None:
            adv_summary = adversarial.get("summary") or {}
            recomputed_binding = bind_verification(raw["adversarial"], adversarial.get("expected_ids") or [], adversarial["sha256"], adv_summary.get("nonce"))
            recorded = adversarial.get("binding") or {}
            same = recomputed_binding["checks"] == recorded.get("checks") and recomputed_binding["ok"] == recorded.get("ok")
            report.add("adversarial_binding_recomputed", same, "adversarial binding recomputed from the raw result " + ("matches the record" if same else "differs from the record"))
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
                recorded = record.get("binding") or {}
                same = recomputed_binding["checks"] == recorded.get("checks") and recomputed_binding["ok"] == recorded.get("ok")
                report.add(f"{name}_binding_recomputed", same, f"{name} suite binding recomputed from the raw result " + ("matches the record" if same else "differs from the record"))
                report.add(f"{name}_outcomes_match_raw", _outcomes(summarize(raw[name])["tests"]) == _outcomes(record.get("tests")),
                           f"per-test {name} outcomes in the bundle equal those in the raw result")
        red = bundle.get("red_run") or {}
        if raw.get("red") is not None and red:
            report.add("red_outcomes_match_raw", _outcomes(summarize(raw["red"])["tests"]) == _outcomes(red.get("tests")),
                       "red-check outcomes in the bundle equal those in the raw result")
            report.add("red_check_failed_on_base", (red.get("failing") or 0) > 0, f"{red.get('failing')} of {red.get('ran')} sealed tests failed on the unmodified base")

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
    if "sealed_binding" in gates and verification.get("binding") is not None:
        if bool(gates["sealed_binding"].get("ok")) != bool(verification["binding"].get("ok")):
            mismatches.append("sealed_binding")
    heldout = verification.get("heldout")
    if "heldout_suite" in gates and heldout:
        if bool(gates["heldout_suite"].get("ok")) != bool(heldout.get("all_passed")):
            mismatches.append("heldout_suite")
    if "adversarial_tests" in gates and adversarial and not gates["adversarial_tests"].get("skipped"):
        if "summary" in adversarial or adversarial.get("unusable"):
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
    recorded_verdict = (bundle.get("verdict") or {}).get("verdict")
    reasons = (bundle.get("verdict") or {}).get("reasons") or []
    if recorded_verdict == "VERIFIED":
        report.add("verified_has_no_reasons", not reasons, "a VERIFIED verdict carries no blocking reasons" if not reasons else f"VERIFIED with reasons recorded: {reasons[0][:120]}")
    elif recorded_verdict == "NEEDS HUMAN":
        report.add("hold_has_reasons", bool(reasons), "a NEEDS HUMAN verdict names at least one reason" if reasons else "NEEDS HUMAN without any recorded reason")
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
        report.add("proof_md_present", False, "PROOF.md missing", severity="warning")
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
    out["run_id"] = bundle.get("run_id")
    out["verdict"] = (bundle.get("verdict") or {}).get("verdict")
    out["manifest_verified"] = any(c["name"] == "manifest_digests" and c["ok"] for c in report.checks)
    out["manifest_present"] = any(c["name"] == "manifest_digests" for c in report.checks)
    return out


def format_report(report: dict) -> str:
    state = ("manifest verified: integrity and internal consistency" if report.get("manifest_verified")
             else "manifest MISMATCH" if report.get("manifest_present") else "no manifest: integrity not checkable")
    lines = [f"attest check {report['path']}", f"run {report.get('run_id')} verdict {report.get('verdict')} ({state})"]
    for check in report["checks"]:
        mark = "ok  " if check["ok"] else ("warn" if check["ok"] is None or check["severity"] == "warning" else "FAIL")
        lines.append(f"  {mark} {check['name']}: {check['detail']}")
    lines.append(f"result: {'OK' if report['ok'] else 'FAILED'} ({report['errors']} error(s), {report['warnings']} warning(s))")
    return "\n".join(lines)
