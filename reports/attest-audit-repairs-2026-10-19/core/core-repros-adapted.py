"""Offline audit reproductions only. No provider, network, SSH or real sandbox use.

Run from the repository root with PYTHONDONTWRITEBYTECODE=1 python3 -B
reports/attest-audit-2026-10-19/core-repros.py. Writes only synthetic audit
artifacts beneath this script's directory. Does not edit product code or tests.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import io
import json
import sys
import subprocess
import traceback
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

AUDIT = Path('/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/audit-repro')
REPO = Path('/work/attest')
sys.path.insert(0, str(REPO))

from attest.core.check import check_bundle
from attest.core.manifest import build_manifest
from attest.core.pipeline import Pipeline, GUEST_BREAKER_DIR, GUEST_SEALED_DIR, methods_changed, oracle_disagreement, coverage_gaps
from attest.core.sealed import SUPERVISOR_SRC, bind_verification, static_test_ids
from attest.core.task import TaskSpec
from attest.core.verdict import derive, expected_verdict
from attest.ledger import Ledger
from attest.models.base import ModelError
from tests.test_verification import FakeExecutor, TASK


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alter_result(run, transform):
    steps = []
    for step in run.steps:
        if step.name.endswith("_result"):
            raw = json.loads(step.stdout)
            transform(raw)
            step = dataclasses.replace(step, stdout=json.dumps(raw))
        steps.append(step)
    return dataclasses.replace(run, steps=steps)


class MissingBase(FakeExecutor):
    def run_branch(self, *args, **kwargs):
        run = super().run_branch(*args, **kwargs)
        if kwargs.get("stage", "").endswith("-base"):
            return dataclasses.replace(run, steps=[], runner_error="OFFLINE AUDIT: lost base result")
        return run


class UntrustedMutant(FakeExecutor):
    def run_branch(self, *args, **kwargs):
        run = super().run_branch(*args, **kwargs)
        if kwargs.get("stage", "") == "arbitrate-adversarial-m1":
            def corrupt(raw):
                raw["nonce"] = "OFFLINE AUDIT: wrong nonce"
                raw["tests"][0].update(outcome="FORGED", nonce_ok=False)
            return alter_result(run, corrupt)
        return run


class PartialMutant(FakeExecutor):
    def run_branch(self, *args, **kwargs):
        run = super().run_branch(*args, **kwargs)
        if kwargs.get("stage", "").startswith("mutant-"):
            def corrupt(raw):
                raw["completed"] = False
                raw["privilege_separation"] = False
                raw["tests"] = []
                raw["expected_ids"] = []
                raw["discovery_error"] = "OFFLINE AUDIT: incomplete supervisor"
                for module in raw["modules"]:
                    module["expected_ids"] = []
            return alter_result(run, corrupt)
        return run


def pipeline(executor_type=FakeExecutor, scenario="honest"):
    p = Pipeline.__new__(Pipeline)
    p.task = TaskSpec.load(TASK)
    p.executor = executor_type(Ledger(), scenario)
    p.save = lambda *args: None
    p.log = lambda *args: None
    p.raw_results = {}
    p.bundle = {}
    p.out_dir = AUDIT / "synthetic-work"
    p.out_dir.mkdir(exist_ok=True)
    return p


SPEC = {"restated_task": "Return one", "acceptance_criteria": ["Return one"], "interface_contract": [], "out_of_scope": []}
ORIGINAL = "import unittest\nclass B(unittest.TestCase):\n    def test_a(self): self.assertEqual(1, 2)\n"
CORRECTED = ORIGINAL.replace("self.assertEqual(1, 2)", "self.assertEqual(1, 1, 'corrected')")
CHANGED = {"durationkit/parse.py": b"def f(): return 1\n"}


def arbitrate(p, original=ORIGINAL, corrected=CORRECTED, label="adversarial", failing=None, spec=SPEC):
    name, guest = ("test_sealed", GUEST_SEALED_DIR) if label == "sealed" else ("test_breaker", GUEST_BREAKER_DIR)
    ids = static_test_ids(original, name)
    failing = failing or [{"id": ids[0], "outcome": "FAIL"}]
    p.ask = lambda *args: SimpleNamespace(json={
        "classifications": [{"test_id": t["id"], "classification": "test_defect", "rationale": "OFFLINE AUDIT fake arbiter"} for t in failing],
        "corrected_module": corrected, "corrected_notes": "OFFLINE AUDIT"})
    return p.arbitrate_module(label, name, guest, original, failing, spec, "", "offline-checkpoint", CHANGED, [])


def correction_summary(result):
    gates = {name: {"ok": True} for name in ("existing_suite", "sealed_binding", "heldout_suite", "mutation", "drift_audit", "adversarial_tests")}
    gate_name = "sealed_binding" if result["module"] == "sealed" else "adversarial_tests"
    gates[gate_name] = {"ok": bool(result["validated"]), "corrected": bool(result["validated"])}
    return {k: result.get(k) for k in ("validated", "cleared_module", "sealed_assertion_hold", "candidate_rerun", "base_rerun", "mutant_reruns", "error")} | {
        "discrimination": (result.get("corrected") or {}).get("discrimination"),
        "derived_when_validated_flag_applied": derive(gates, {"scope_ok": True, "implementer_finished": True}, True)["verdict"]}


def check_synthetic(name, bundle, manifest_mode="complete"):
    path = AUDIT / "synthetic-bundles" / name
    path.mkdir(parents=True, exist_ok=True)
    write_json(path / "proof_bundle.json", bundle)
    manifest = build_manifest(path, bundle["run_id"])
    if manifest_mode == "empty-list":
        manifest.update(files=[], file_count=0, total_bytes=0)
    write_json(path / "manifest.json", manifest)
    return check_bundle(path)


def child_timeout_fake():
    """Execute the exact run_child AST with a fake process and fake elapsed time.

    No process is spawned. The second communicate models a descendant that keeps
    inherited stdout/stderr open after its immediate parent has been killed.
    """
    calls, clock = [], [0.0]
    class FakeProc:
        returncode = -9
        pid = 4242
        stdout = stderr = stdin = None
        def wait(self, timeout=None):
            return -9
        def communicate(self, input=None, timeout=None):
            calls.append({"method": "communicate", "timeout": timeout})
            if timeout is not None:
                clock[0] += timeout
                raise subprocess.TimeoutExpired("OFFLINE-AUDIT-FAKE", timeout)
            clock[0] += 3600.0
            return b"", b""
        def kill(self):
            calls.append({"method": "kill", "target": "immediate process only"})
    class FakeThread:
        def __init__(self, **kwargs): pass
        def start(self): pass
        def join(self, **kwargs): pass
    import signal as _signal
    namespace = {"os": SimpleNamespace(pipe=lambda: (100, 101), close=lambda fd: None, killpg=lambda pid, sig: calls.append({"method": "killpg", "target": "whole process group"}),
                                       path=SimpleNamespace(isdir=lambda p: False), getpid=lambda: 1),
                 "signal": _signal, "CLEANUP_GRACE": 5.0, "MARK_VAR": "ATTEST_TEST_MARK", "marked_processes": lambda mark, kill: 0,
                 "report": {"cleanup_incomplete": 0},
                 "time": SimpleNamespace(monotonic=lambda: clock[0]),
                 "subprocess": SimpleNamespace(Popen=lambda *a, **kw: FakeProc(), PIPE=-1, TimeoutExpired=subprocess.TimeoutExpired),
                 "threading": SimpleNamespace(Thread=FakeThread), "sys": sys, "json": json,
                 "child_src": "OFFLINE AUDIT", "sys_path": [], "cwd": "/OFFLINE-AUDIT", "env": {},
                 "child_kw": {}, "nonce": "OFFLINE-AUDIT", "per_test_timeout": 1.0}
    node = next(n for n in ast.parse(SUPERVISOR_SRC).body if isinstance(n, ast.FunctionDef) and n.name == "run_child")
    exec(compile(ast.Module(body=[node], type_ignores=[]), "<exact-supervisor-run_child>", "exec"), namespace)
    record = namespace["run_child"]("test.T.test_a", "test", "mark-1")
    return {"configured_timeout_s": 1.0, "calls": calls, "fake_elapsed_s": clock[0], "record": record,
            "actual_os_descendant_process_executed": False}


def main():
    outputs = {}
    outputs["missing_base"] = correction_summary(arbitrate(pipeline(MissingBase)))

    p = pipeline(UntrustedMutant, "arb_refactor")
    p.bundle = {"breaker": {"mutation": {"mutants": [{"id": "m1", "path": "durationkit/parse.py", "status": "killed", "description": "OFFLINE AUDIT mutation"}]}}}
    (p.out_dir / "mutants_m1.py").write_text("def f(): return -1\n", encoding="utf-8")
    outputs["untrusted_corrected_mutant"] = correction_summary(arbitrate(p))

    p = pipeline()
    arbitrate(p)  # installs the offline arbiter answer; no real model is used
    (p.out_dir / "breaker_tests.py").write_text(ORIGINAL, encoding="utf-8")
    forged = {"id": "test_breaker.B.test_a", "outcome": "FORGED", "nonce_ok": False}
    p.bundle = {"breaker": {"adversarial": {"summary": {"tests": [forged]}, "binding": {"ok": False}}}}
    p.arbitration_apply = True
    gates = {"existing_suite": {"ok": True}, "sealed_binding": {"ok": True}, "adversarial_tests": {"ok": False}}
    entered = p.arbitrate_failures(SPEC, "", ORIGINAL, hashlib.sha256(ORIGINAL.encode()).hexdigest(),
        static_test_ids(ORIGINAL), "offline-checkpoint", CHANGED, [], gates, {"ok": True, "checks": {}}, {"tests": []}, True, True)
    outputs["original_adversarial_forgery_arbitrated"] = {
        "initial_adversarial_outcome": "FORGED", "initial_adversarial_binding_ok": False,
        "arbitration_entered": bool(entered and entered.get("modules")), "validated_modules": (entered or {}).get("validated_modules"),
        "headline": (entered or {}).get("headline"), "module": correction_summary(entered["modules"][0]) if entered and entered.get("modules") else None}

    pair_original = "import unittest\nfrom durationkit.parse import f\nclass T(unittest.TestCase):\n    def test_pair(self):\n        a, b = f()\n        self.assertEqual((a, b), (1, 2))\n"
    pair_corrected = pair_original.replace("a, b = f()", "a, b, *extra = f()")
    def toy_suite(source):
        namespace = {"f": lambda: (1, 2, 3)}
        exec(compile(source.replace("from durationkit.parse import f\n", ""), "/tmp/sealed/test_sealed.py", "exec"), namespace)
        result = unittest.TestResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(namespace["T"]).run(result)
        return result
    original_run = toy_suite(pair_original)
    corrected_run = toy_suite(pair_corrected)
    tail = original_run.errors[0][1]
    failure = {"id": "test_sealed.T.test_pair", "outcome": "ERROR", "failure_tail": tail}
    p = pipeline()
    p.task = dataclasses.replace(p.task, statement="Return exactly the two-item tuple (1, 2).", acceptance_criteria=["Return exactly two items, 1 and 2."])
    pair_spec = dict(SPEC, restated_task=p.task.statement, acceptance_criteria=p.task.acceptance_criteria)
    outputs["candidate_caused_test_internal_error"] = {
        "contract": p.task.statement, "candidate_return": [1, 2, 3], "original_failure": failure,
        "oracle_disagreement": oracle_disagreement(failure), "weakened_test_passes_same_bad_candidate": corrected_run.wasSuccessful(),
        "actual_arbitration": correction_summary(arbitrate(p, pair_original, pair_corrected, "sealed", [failure], pair_spec))}

    original = "import unittest\nfrom durationkit.parse import f\nclass T(unittest.TestCase):\n    def test_bad(self): self.assertEqual(f(), 1)\n    def test_good(self): self.assertEqual(f(), 2)\n"
    import_change = original.replace("from durationkit.parse import f", "from other_module import f").replace("f(), 1)", "f(), 1, 'changed')")
    base_change = original.replace("class T(unittest.TestCase):", "class T(other.TestCase):").replace("f(), 1)", "f(), 1, 'changed')")
    outputs["correction_scope"] = {"import_rebound_detected_changes": sorted(methods_changed(original, import_change, "test_sealed")),
        "testcase_base_replaced_detected_changes": sorted(methods_changed(original, base_change, "test_sealed")),
        "unchanged_test_good_semantics_are_protected": False}

    p = pipeline()
    arbitrate(p)
    answer = p.ask()
    answer.json["classifications"] = [{"test_id": "unknown.T.not_a_failing_test", "classification": "test_defect"}]
    p.ask = lambda *args: answer
    r = p.arbitrate_module("adversarial", "test_breaker", GUEST_BREAKER_DIR, ORIGINAL,
        [{"id": "test_breaker.B.test_a", "outcome": "FAIL"}], SPEC, "", "offline-checkpoint", CHANGED, [])
    outputs["classification_ids_not_matched"] = {"returned_classification_ids": ["unknown.T.not_a_failing_test"],
        "actual_failing_ids": ["test_breaker.B.test_a"], "validated": r["validated"], "error": r["error"]}

    p = pipeline(PartialMutant)
    p.max_mutants, p.mutant_workers, p.mutation_threshold = 1, 1, 0.5
    def no_model(*args):
        raise ModelError("OFFLINE AUDIT: no model called")
    p.ask = no_model
    mutant = SimpleNamespace(id="m1", path="durationkit/parse.py", source="def f(): return -1\n", lineno=1, operator="audit", description="OFFLINE AUDIT")
    with patch("attest.core.pipeline.generate_mutants", return_value=[mutant]):
        broken = p.breaker_pass({}, CHANGED, [], ORIGINAL, hashlib.sha256(ORIGINAL.encode()).hexdigest(), "offline-checkpoint", SPEC, "", static_test_ids(ORIGINAL), [])
    outputs["incomplete_normal_mutant"] = broken["mutation"]

    minimal = {"run_id": "OFFLINE-AUDIT-ONLY", "candidate": {"scope_ok": True, "implementer_finished": True},
               "gates": {"sealed_binding": {"ok": True}}, "verdict": {"verdict": "VERIFIED", "reasons": []}}
    outputs["incomplete_verified_bundle"] = check_synthetic("incomplete-verified", minimal)
    outputs["empty_manifest_listing"] = check_synthetic("empty-manifest-list", minimal, "empty-list")
    legacy = dict(minimal, gates={"heldout_suite": {"ok": False}}, arbitration={"applied": True, "cleared": True},
                  provenance={"created_at_utc": "2026-10-19T12:00:00Z"})
    outputs["modern_bundle_legacy_bypass"] = {"rule": expected_verdict(legacy), "checker": check_synthetic("modern-legacy-bypass", legacy)}
    infeasible = {"run_id": "OFFLINE-AUDIT-ONLY", "verdict": {"verdict": "INFEASIBLE"}, "contract_audit": {"conflicts": [{"demonstrated": True}]}}
    outputs["infeasible_without_witness"] = check_synthetic("infeasible-without-witness", infeasible)
    outputs["coverage_missing_or_unmapped"] = {"none": coverage_gaps(None, ["A", "B"], ["test.T.test_a"]), "empty": coverage_gaps([], ["A", "B"], ["test.T.test_a"])}
    outputs["per_test_timeout_descendant_pipes"] = child_timeout_fake()

    p = pipeline()
    p.ask = lambda *args: SimpleNamespace(call=SimpleNamespace(requested_model="OFFLINE-AUDIT-FAKE"), json={
        "consistent": False, "notes": "OFFLINE AUDIT: self-declaration is not semantic proof",
        "conflicts": [{"requirement_ids": ["AC999"], "summary": "OFFLINE AUDIT fake conflict",
                       "witness": "import sys\nprint('CONTRADICTION no actual contradiction calculated')\nsys.exit(3)\n"}]})
    outputs["marker_only_witness"] = p.contract_audit(SPEC, {}, "offline-checkpoint")

    p = pipeline()
    valid = arbitrate(p)
    raw = dict(p.raw_results["adversarial_corrected"])
    raw.pop("privilege_separation", None)
    binding = bind_verification(raw, valid["corrected"]["expected_ids"], valid["corrected"]["sha256"], valid["corrected"]["nonce"])
    outputs["missing_isolation_field"] = {"privilege_separation_present": "privilege_separation" in raw,
        "binding_ok": binding["ok"], "verifier_isolation_active": binding["checks"]["verifier_isolation_active"]}

    audited = ["attest/core/pipeline.py", "attest/core/sealed.py", "attest/core/check.py", "attest/core/manifest.py", "attest/core/verdict.py", "attest/core/prompts.py", "tests/test_verification.py"]
    outputs["source_sha256"] = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in audited}
    write_json(AUDIT / "core-repro-results.json", outputs)
    print(json.dumps({key: value for key, value in outputs.items() if key not in {"incomplete_verified_bundle", "empty_manifest_listing", "modern_bundle_legacy_bypass", "infeasible_without_witness", "source_sha256"}}, indent=2))
    for key in ("incomplete_verified_bundle", "empty_manifest_listing", "modern_bundle_legacy_bypass", "infeasible_without_witness"):
        result = outputs[key].get("checker", outputs[key])
        print(key, json.dumps({k: result[k] for k in ("ok", "errors", "warnings", "verdict", "manifest_verified")}))


if __name__ == "__main__":
    main()
