"""Adversarial regression tests for the verification binding, run offline with fake provider and executor.

Scenarios: honest candidate; sealed file modified during the run; forged result (wrong nonce); missing tests;
extra tests; premature exit (no result file); forged console text without a result file; blanket result forgery
(caught by the verifier canaries); verification order (the sealed supervisor is the first step of its branch and the
repository suite runs in its own branch); bound repository and held-out suites; a patch with no mutable sites.
"""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from attest.core import pipeline as pipeline_module
from attest.core.pipeline import Pipeline
from attest.core.sealed import CANARY_FAIL_ID, CANARY_PASS_ID, SUPERVISOR_VERSION, is_supervisor_step, static_test_ids
from attest.core.task import TaskSpec
from attest.core.testparse import parse_pytest, parse_unittest
from attest.ledger import Ledger, ModelCall, utcnow
from attest.models.base import ModelResult
from attest.sandbox.base import RunResult, StepResult

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "examples" / "durationkit-task" / "task.json"

SEALED_SRC = '''import unittest
from durationkit import parse_duration

class T(unittest.TestCase):
    def test_a(self): self.assertEqual(parse_duration("1h"), 3600.0)
    def test_b(self): self.assertEqual(parse_duration("2m"), 120.0)
    def test_c(self): self.assertEqual(parse_duration("3s"), 3.0)
    def test_d(self): self.assertEqual(parse_duration("500ms"), 0.5)
    def test_e(self): self.assertEqual(parse_duration("1h30m"), 5400.0)
    def test_f(self):
        with self.assertRaises(ValueError): parse_duration("1x")
'''
THIN_BREAKER_SRC = '''import unittest
from durationkit import parse_duration

class B(unittest.TestCase):
    def test_a(self): self.assertEqual(parse_duration("1h"), 3600.0)
    def test_b(self): self.assertEqual(parse_duration("2m"), 120.0)
    def test_c(self): self.assertEqual(parse_duration("3s"), 3.0)
'''
HELDOUT_SRC = '''import unittest
from durationkit import parse_duration

class HeldOut(unittest.TestCase):
    def test_h1(self): self.assertEqual(parse_duration("2d"), 172800.0)
    def test_h2(self): self.assertEqual(parse_duration("1s500ms"), 1.5)
'''
CANDIDATE_SRC = '''def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("duration must be a string")
    s = text.strip()
    if not s:
        raise ValueError("empty")
    if s.isdigit():
        return float(s)
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
    total = 0.0
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i:
            raise ValueError("bad")
        unit = "ms" if s.startswith("ms", j) else s[j:j + 1]
        if unit not in units:
            raise ValueError("bad unit")
        total += int(s[i:j]) * units[unit]
        i = j + len(unit)
    return float(total)
'''
TAMPERING_CANDIDATE_SRC = "import sys, os\nsys.modules['unittest'] = sys.modules.get('unittest')\n" + CANDIDATE_SRC


class FakeProvider:
    name = "fake"

    def __init__(self, ledger, scenario="honest"):
        self.ledger = ledger
        self.scenario = scenario
        self.turn = 0

    def describe(self):
        return {"provider": self.name}

    def structured(self, role, prompt, schema, stage):
        if role == "spec":
            payload = {"feasible": True, "infeasibility_reason": None, "restated_task": "add units",
                       "interface_contract": [{"name": "parse_duration", "signature": "parse_duration(text: str) -> float",
                                               "behavior": "parse", "error_cases": ["ValueError"]}],
                       "acceptance_criteria": ["units work"], "out_of_scope": ["tests"], "external_references_needed": []}
        elif role == "seal":
            payload = {"test_file": SEALED_SRC, "test_count": 6, "notes": "fake"}
        elif role == "break":
            src = THIN_BREAKER_SRC if self.scenario == "no_mutants_thin_adversarial" else SEALED_SRC.replace("class T(", "class B(")
            payload = {"test_file": src, "test_count": 6, "notes": "fake breaker"}
        elif role == "audit":
            score = 0.9 if self.scenario == "drift_high" else 0.1
            payload = {"drift_score": score, "assessment": "off_target" if score > 0.5 else "aligned", "scope_narrowed": [],
                       "scope_widened": [], "unsupported_claims": [], "summary": "fake audit"}
        elif role == "arbitrate":
            if self.scenario == "arb_clear":
                payload = {"classifications": [{"test_id": "test_breaker.B.test_a", "classification": "test_defect",
                                                "rationale": "fake defect", "contract_basis": "fake"}],
                           "corrected_module": SEALED_SRC.replace("class T(", "class B("), "corrected_notes": "fixed defect"}
            else:
                payload = {"classifications": [{"test_id": "test_sealed.T.test_x", "classification": "implementation_bug",
                                                "rationale": "fake", "contract_basis": "fake"}],
                           "corrected_module": None, "corrected_notes": "fake: treated as a real bug, no correction"}
        else:
            self.turn += 1
            if self.turn == 1:
                content = TAMPERING_CANDIDATE_SRC if self.scenario == "tamper_scan" else CANDIDATE_SRC
                payload = {"action": "write_file", "path": "durationkit/parse.py", "content": content, "find": None,
                           "replace": None, "start_line": None, "end_line": None, "code": None, "reason": "implement", "summary": None}
            else:
                payload = {"action": "finish", "path": None, "content": None, "find": None, "replace": None, "start_line": None,
                           "end_line": None, "code": None, "reason": "done", "summary": "done"}
        call = ModelCall(provider=self.name, role=role, stage=stage, requested_model="fake", requested_effort=None,
                         returned_model="fake", returned_effort=None, started_at_utc=utcnow(), elapsed_ms=1,
                         gateway_duration_ms=None, prompt_chars=len(prompt), tokens_in=1, tokens_out=1, tokens_cached=0,
                         usage_raw={}, cost_usd=None, cost_note="fake", ok=True)
        self.ledger.add_call(call)
        return ModelResult(json=payload, text=None, call=call)


class FakeExecutor:
    """Emulates the guest: supervisor results are synthesized from the job file and module sources according to the
    scenario. Records every operation's step list so tests can assert the verification order."""
    name = "fake"

    def __init__(self, ledger, scenario="honest"):
        self.ledger = ledger
        self.scenario = scenario
        self.counter = 0
        self.checkpoint_files: dict[str, bytes] = {}
        self.operations: list[dict] = []

    def describe(self):
        return {"executor": self.name, "scenario": self.scenario}

    def resolve_image(self, tag):
        return "base-image"

    def _source(self, files, path):
        data = files.get(path)
        if data is None:
            data = self.checkpoint_files.get(path, b"")
        return data if isinstance(data, bytes) else data.encode()

    def _repo_test_modules(self, files):
        paths = sorted({p for p in list(self.checkpoint_files) + list(files)
                        if p.startswith("/tmp/w/tests/") and p.endswith(".py") and Path(p).name.startswith("test")})
        return [(f"tests.{Path(p).stem}", self._source(files, p).decode()) for p in paths]

    def _verbose_unittest(self, ids, failing=()):
        lines = [f"{i.split('.')[-1]} ({i}) ... {'FAIL' if i in failing else 'ok'}" for i in ids]
        bad = len([i for i in ids if i in failing])
        return "\n".join(lines) + f"\n\nRan {len(ids)} tests in 0.001s\n\n" + (f"FAILED (failures={bad})\n" if bad else "OK\n")

    @staticmethod
    def _record(test_id, outcome="ok", exit_code=0, **extra):
        rec = {"id": test_id, "exit_code": exit_code, "signal": None, "timed_out": False, "outcome": outcome,
               "child_outcome": outcome, "nonce_ok": True}
        rec.update(extra)
        return rec

    def _supervisor(self, step, files, name, candidate_present, mutant):
        cmd = step["cmd"]
        nonce, job_path = cmd[4], cmd[5]
        job = json.loads(files[job_path].decode())
        modules, tests = [], []
        sealed_on_candidate = name == "sealed" and candidate_present and not mutant
        for m in job["modules"]:
            src = self._source(files, m["path"])
            sha = hashlib.sha256(src).hexdigest()
            ids = static_test_ids(src, m["name"])
            after = "0" * 64 if (self.scenario == "modified_tests" and sealed_on_candidate) else sha
            modules.append({"name": m["name"], "path": m["path"], "sha256_before": sha, "sha256_after": after,
                            "expected_ids": ids, "discovery_error": None})
            for k, test_id in enumerate(ids):
                # on the unmodified base (red check, and the arbitration base re-run of a corrected module) the behaviour
                # under test is not implemented, so every test errors; a corrected module must still fail here
                red = name in ("sealed", "arbbase") and not candidate_present
                if red:
                    tests.append(self._record(test_id, "ERROR", 1))
                elif mutant:
                    survive = self.scenario == "mutants_survive"
                    tests.append(self._record(test_id) if (survive or k) else self._record(test_id, "FAIL", 1))
                elif name == "breaker" and self.scenario in ("breaker_fail", "arb_clear") and k == 0:
                    tests.append(self._record(test_id, "FAIL", 1))
                elif name == "existing" and self.scenario == "existing_fail_bound" and k == 0:
                    tests.append(self._record(test_id, "FAIL", 1))
                elif name == "heldout" and self.scenario == "heldout_fail" and k == 0:
                    tests.append(self._record(test_id, "FAIL", 1))
                else:
                    tests.append(self._record(test_id))
        if sealed_on_candidate:
            if self.scenario == "missing_tests":
                tests = tests[:-1]
            if self.scenario == "extra_tests":
                tests.append(self._record("test_sealed.T.test_injected"))
            if self.scenario == "child_crash":
                tests[0].update(exit_code=None, signal=11, outcome="CRASH")
            if self.scenario == "child_timeout":
                tests[0].update(exit_code=None, timed_out=True, outcome="TIMEOUT")
            if self.scenario == "sealed_defect":
                tests = [{**t, "exit_code": 1, "outcome": "FAIL", "child_outcome": "FAIL"} for t in tests]
        canaries, canary_ok = [], None
        if job.get("canary"):
            forged = self.scenario == "forge_all_ok" and sealed_on_candidate
            canaries = [self._record(CANARY_PASS_ID),
                        self._record(CANARY_FAIL_ID) if forged else self._record(CANARY_FAIL_ID, "FAIL", 1)]
            canary_ok = not forged
        bad_nonce = (self.scenario == "forged_nonce" and sealed_on_candidate) or (self.scenario == "mutants_unknown" and mutant)
        report = {"supervisor": SUPERVISOR_VERSION, "privilege_separation": self.scenario != "no_isolation",
                  "operation_uid": 0 if self.scenario != "no_isolation" else 65534, "test_uid": 65534,
                  "nonce": nonce if not bad_nonce else "deadbeef", "completed": True, "modules": modules,
                  "sealed_sha256_before": modules[0]["sha256_before"] if modules else None,
                  "sealed_sha256_after": modules[0]["sha256_after"] if modules else None,
                  "expected_ids": [i for m in modules for i in m["expected_ids"]], "discovery_error": None,
                  "tests": tests, "canaries": canaries, "canary_ok": canary_ok, "ran": len(tests), "python": "3.12.13"}
        exit_code = 0 if all(t["outcome"] == "ok" for t in tests) and canary_ok is not False else 1
        return report, exit_code

    def _run(self, stage, files, steps, disposable):
        self.counter += 1
        op = f"op-{self.counter}"
        self.operations.append({"stage": stage, "steps": [s["name"] for s in steps],
                                "supervisor_first": bool(steps) and is_supervisor_step(steps[0]),
                                "imports_candidate_before_supervisor": any(
                                    not is_supervisor_step(s) and s["name"] in ("existing", "heldout", "judge")
                                    and any(is_supervisor_step(t) for t in steps[i + 1:]) for i, s in enumerate(steps))})
        results = []
        candidate_present = any(p.startswith("/tmp/w/durationkit/") for p in files)
        mutant = stage.startswith("mutant-")
        pending = {}
        for step in steps:
            name = step["name"]
            if is_supervisor_step(step):
                report, exit_code = self._supervisor(step, files, name, candidate_present, mutant)
                pending[name] = report
                fake_text = "".join(f"{i.split('.')[-1]} ({i}) ... ok\n" for i in report["expected_ids"]) + f"\nRan {len(report['expected_ids'])} tests\n\nOK\n"
                stderr = fake_text if self.scenario == "forged_text" else ""
                results.append(StepResult(name, step["cmd"], exit_code, False, 0.1, "SEALED-RESULT-WRITTEN\n", stderr))
            elif name.endswith("_result"):
                prefix = name[:-len("_result")]
                if self.scenario in ("premature_exit", "forged_text") and candidate_present and not mutant and prefix == "sealed":
                    results.append(StepResult(name, step["cmd"], 1, False, 0.0, "", "No such file"))
                else:
                    results.append(StepResult(name, step["cmd"], 0, False, 0.0, json.dumps(pending[prefix]), ""))
            elif name in ("existing", "heldout", "judge"):
                # stdout-parsed path: the task's own test command (used at checkpoint and when binding is impossible)
                ids = []
                for module, src in self._repo_test_modules(files):
                    ids.extend(static_test_ids(src, module))
                failing = set()
                if name == "heldout" and self.scenario in ("heldout_fail", "heldout_fail_stdout"):
                    failing = {ids[-1]} if ids else set()
                    if not failing:
                        ids, failing = ["tests.test_heldout.H.test_y"], {"tests.test_heldout.H.test_y"}
                text = self._verbose_unittest(ids, failing)
                results.append(StepResult(name, step["cmd"], 1 if failing else 0, False, 0.1, "", text))
            else:
                results.append(StepResult(name, step["cmd"], 0, False, 0.0, "", ""))
        return RunResult(stage=stage, operation_uuid=op, status="SUCCESS", exit_code=0, timed_out=False, signal=-1,
                         duration_s=0.5, image_uuid="base-image", result_image_uuid=None if disposable else "ckpt-image",
                         steps=results)

    def create_checkpoint(self, image, files, steps, stage, timeout=120, networking=False):
        self.checkpoint_files = dict(files)
        return self._run(stage, files, steps, disposable=False)

    def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
        return self._run(stage, files, steps, disposable=True)


def run_scenario(scenario, apply=False, heldout=None, return_executor=False):
    tmp = Path(tempfile.mkdtemp(prefix="attest-test-"))
    try:
        ledger = Ledger()
        task = TaskSpec.load(TASK)
        if heldout is not None:
            task.heldout_tests = heldout
        elif scenario == "heldout_fail":
            task.heldout_tests = {"tests/test_heldout.py": HELDOUT_SRC}
        elif scenario == "heldout_fail_stdout":
            task.heldout_tests = {"tests/test_heldout.py": "import unittest\n"}  # nothing statically discoverable
        executor = FakeExecutor(ledger, scenario)
        pipeline = Pipeline(task=task, provider=FakeProvider(ledger, scenario), executor=executor, ledger=ledger,
                            out_dir=tmp, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="test",
                            arbitration_apply=apply)
        if scenario.startswith("no_mutants"):
            with mock.patch.object(pipeline_module, "generate_mutants", lambda *a, **k: []):
                bundle = pipeline.run()
        else:
            bundle = pipeline.run()
        return (bundle, executor) if return_executor else bundle
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class VerificationBinding(unittest.TestCase):
    def test_honest_candidate_is_verified_with_breaker(self):
        bundle = run_scenario("honest")
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", bundle["verdict"])
        self.assertTrue(bundle["verification"]["binding"]["ok"])
        self.assertTrue(bundle["verification"]["binding"]["checks"]["canary_must_fail_failed"])
        self.assertEqual(bundle["red_run"]["failing"], 6)
        self.assertIsNotNone(bundle["breaker"])
        mutation = bundle["breaker"]["mutation"]
        self.assertGreater(mutation["generated"], 0)
        self.assertEqual(mutation["killed"], mutation["evaluated"])
        self.assertTrue(bundle["breaker"]["adversarial"]["summary"]["all_passed"])
        self.assertTrue(all(g["ok"] for g in bundle["gates"].values()), bundle["gates"])
        self.assertLess(bundle["drift"]["drift_score"], 0.6)
        self.assertEqual(bundle["verdict"]["warnings"], [], "an honest unittest run with bound suites has no warnings")

    def test_modified_sealed_file_is_rejected(self):
        bundle = run_scenario("modified_tests")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("integrity" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])
        self.assertIsNone(bundle["breaker"])
        self.assertFalse(bundle["gates"]["mutation"]["ok"])

    def test_forged_nonce_is_rejected(self):
        bundle = run_scenario("forged_nonce")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("nonce" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_missing_tests_are_rejected(self):
        bundle = run_scenario("missing_tests")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("missing" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_extra_tests_are_rejected(self):
        bundle = run_scenario("extra_tests")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("unexpected test IDs" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_premature_exit_is_rejected(self):
        bundle = run_scenario("premature_exit")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("no trusted sealed result" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_forged_console_text_is_not_trusted(self):
        bundle = run_scenario("forged_text")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("no trusted sealed result" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_child_crash_and_timeout_block_verified(self):
        for scenario, needle in (("child_crash", "signal"), ("child_timeout", "timed out")):
            with self.subTest(scenario=scenario):
                bundle = run_scenario(scenario)
                self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
                self.assertTrue(any(needle in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_heldout_failures_block_verified_bound(self):
        bundle = run_scenario("heldout_fail")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("held-out tests failed" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])
        self.assertFalse(bundle["gates"]["heldout_suite"]["ok"])
        self.assertEqual(bundle["gates"]["heldout_suite"]["evidence_class"], "bound")
        self.assertEqual(bundle["verification"]["heldout"]["modules"][0]["name"], "tests.test_heldout")
        self.assertIsNone(bundle["arbitration"], "held-out failures are never arbitrated")

    def test_heldout_falls_back_to_stdout_when_not_discoverable(self):
        bundle = run_scenario("heldout_fail_stdout")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertEqual(bundle["gates"]["heldout_suite"]["evidence_class"], "stdout")
        self.assertIn("not statically discoverable", bundle["verification"]["heldout"]["evidence_note"])

    def test_surviving_mutants_block_verified(self):
        bundle = run_scenario("mutants_survive")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("mutation score" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_all_unknown_mutants_block_verified(self):
        bundle = run_scenario("mutants_unknown")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertFalse(bundle["gates"]["mutation"]["ok"], bundle["gates"])
        self.assertTrue(any("mutants were unknown" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_failing_adversarial_tests_block_verified(self):
        bundle = run_scenario("breaker_fail")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("adversarial tests failed" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_high_drift_blocks_verified(self):
        bundle = run_scenario("drift_high")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("drift audit score" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_arbitration_is_advisory_then_clears_in_apply_mode(self):
        advisory = run_scenario("arb_clear", apply=False)
        self.assertEqual(advisory["verdict"]["verdict"], "NEEDS HUMAN", advisory["verdict"])
        self.assertTrue(advisory["arbitration"]["cleared"], advisory["arbitration"])  # recommends clearing
        self.assertFalse(advisory["verdict"].get("cleared_by_arbitration", False))    # but does not apply it
        applied = run_scenario("arb_clear", apply=True)
        self.assertEqual(applied["verdict"]["verdict"], "VERIFIED", applied["verdict"])
        self.assertTrue(applied["verdict"].get("cleared_by_arbitration"))
        self.assertEqual(applied["arbitration"]["counts"]["test_defect"], 1)
        self.assertIn("adversarial tests failed", " ".join(applied["verdict"]["superseded_reasons"]))

    def test_sealed_test_failure_triggers_arbitration(self):
        # A sealed test that FAILs makes the child exit 1; that nonzero exit must not be mistaken for tampering, so
        # arbitration still runs (it stays advisory because the breaker was skipped when sealing failed).
        bundle = run_scenario("sealed_defect")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertIsNotNone(bundle["arbitration"], "arbitration should run on a plain sealed-test failure")
        self.assertFalse(bundle["verdict"].get("cleared_by_arbitration", False))

    def test_implementation_bug_is_not_cleared_by_arbitration(self):
        bundle = run_scenario("breaker_fail", apply=True)  # arbiter calls it a real bug -> stays NEEDS HUMAN even in apply mode
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertFalse(bundle["arbitration"]["cleared"])
        self.assertEqual(bundle["arbitration"]["counts"]["implementation_bug"], 1)

    def test_missing_privilege_separation_blocks_verified(self):
        bundle = run_scenario("no_isolation")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertTrue(any("privilege separation" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])
        self.assertFalse(bundle["verification"]["binding"]["checks"]["verifier_isolation_active"])


class VerificationOrderAndCanaries(unittest.TestCase):
    """M1.1 and M1.2: supervisor-first order, separate branches for the repository suite, canaries, evidence classes."""

    def test_supervisor_is_first_and_repo_suite_runs_in_its_own_branch(self):
        bundle, executor = run_scenario("honest", return_executor=True)
        verify = [op for op in executor.operations if op["stage"] == "verify"]
        self.assertEqual(len(verify), 1)
        self.assertTrue(verify[0]["supervisor_first"], verify[0])
        self.assertEqual(verify[0]["steps"], ["sealed", "sealed_result"], "the verify branch runs the supervisor and nothing else")
        self.assertFalse(any(op["imports_candidate_before_supervisor"] for op in executor.operations),
                         "no operation may run the repository's test command ahead of a supervisor step")
        existing = [op for op in executor.operations if op["stage"] == "existing"]
        self.assertEqual(len(existing), 1, "the repository suite runs exactly once, in its own branch")
        self.assertTrue(existing[0]["supervisor_first"], "for a unittest repository the suite is bound through the supervisor")
        stages = [op["stage"] for op in executor.operations]
        self.assertLess(stages.index("verify"), stages.index("existing"))
        self.assertEqual(bundle["verification"]["order"][0][:6], "verify")

    def test_evidence_classes_are_recorded_per_gate(self):
        bundle = run_scenario("honest")
        classes = {name: g.get("evidence_class") for name, g in bundle["gates"].items()}
        self.assertEqual(classes, {"existing_suite": "bound", "sealed_binding": "bound", "mutation": "bound",
                                   "adversarial_tests": "bound", "drift_audit": "model"})
        existing = bundle["verification"]["existing"]
        self.assertEqual(existing["evidence_class"], "bound")
        self.assertTrue(existing["binding"]["ok"], existing["binding"])
        self.assertTrue(existing["binding"]["checks"]["module_digests_unchanged"])
        self.assertEqual(bundle["execution"]["suite_binding"]["mode"], "bound")
        self.assertNotEqual(existing["operation_uuid"], bundle["verification"]["operation_uuid"])

    def test_bound_existing_suite_failure_blocks_verified(self):
        bundle = run_scenario("existing_fail_bound")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertFalse(bundle["gates"]["existing_suite"]["ok"])
        self.assertTrue(any("existing test suite failed" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])
        self.assertIsNone(bundle["breaker"], "the breaker does not run when the repository suite fails")

    def test_blanket_forgery_flips_the_canary_and_is_recorded_as_tamper(self):
        bundle = run_scenario("forge_all_ok")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        checks = bundle["verification"]["binding"]["checks"]
        self.assertTrue(checks["all_expected_pass"], "every real test was reported as passing by the forgery")
        self.assertFalse(checks["canary_must_fail_failed"])
        self.assertTrue(any("canary flipped" in r and "forged" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])
        self.assertIsNone(bundle["arbitration"], "a flipped canary is tampering, never a test defect to arbitrate")
        self.assertIn("CANARY FLIPPED", bundle["verification"]["sealed"]["summary_line"])

    def test_mutants_run_without_canaries_and_are_bound_without_them(self):
        bundle = run_scenario("honest")
        self.assertEqual(bundle["breaker"]["mutation"]["unknown"], 0)
        self.assertEqual(bundle["breaker"]["mutation"]["killed"], bundle["breaker"]["mutation"]["generated"])

    def test_tamper_scan_warns_on_suspicious_added_lines(self):
        bundle = run_scenario("tamper_scan")
        scan = bundle["candidate"]["tamper_scan"]
        self.assertTrue(scan["flagged"], scan)
        self.assertIn("sys.modules manipulation", scan["labels"])
        self.assertTrue(any("static tamper scan" in w for w in bundle["verdict"]["warnings"]), bundle["verdict"])
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", "the scan warns; it is not a gate")

    def test_no_mutable_sites_fails_closed_with_a_thin_adversarial_suite(self):
        bundle = run_scenario("no_mutants_thin_adversarial")
        self.assertEqual(bundle["breaker"]["mutation"]["generated"], 0)
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
        self.assertFalse(bundle["gates"]["mutation"]["ok"])
        self.assertTrue(any("no mutable sites" in r and "adversarial suite has only 3" in r for r in bundle["verdict"]["reasons"]), bundle["verdict"])

    def test_no_mutable_sites_passes_with_warning_when_adversarial_suite_is_real(self):
        bundle = run_scenario("no_mutants_strong_adversarial")
        self.assertEqual(bundle["breaker"]["mutation"]["generated"], 0)
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", bundle["verdict"])
        self.assertTrue(bundle["gates"]["mutation"].get("weak"))
        self.assertTrue(any("no mutable sites" in w for w in bundle["verdict"]["warnings"]), bundle["verdict"])

    def test_adversarial_result_has_no_skipped_fail_open_path(self):
        bundle = run_scenario("honest")
        self.assertNotIn("skipped", bundle["breaker"]["adversarial"])
        self.assertNotIn("skipped", bundle["gates"]["adversarial_tests"])


class SubtestAccounting(unittest.TestCase):
    def test_methods_and_events_are_counted_separately(self):
        lines = []
        for k in range(18):
            lines.append(f"test_ok{k} (test_sealed.T.test_ok{k}) ... ok")
        for k in range(9):
            lines.append(f"test_bad{k} (test_sealed.T.test_bad{k}) ... ")
            for j in range(3 if k < 6 else 2):
                lines.append(f"  test_bad{k} (test_sealed.T.test_bad{k}) [text='x{j}'] ... ERROR")
        text = "\n".join(lines) + "\n\nRan 27 tests in 0.010s\n\nFAILED (errors=24)\n"
        parsed = parse_unittest("", text, 1)
        self.assertEqual(parsed["ran"], 27)
        self.assertEqual(len(parsed["tests"]), 27)
        self.assertEqual(parsed["passed"], 18)
        self.assertEqual(parsed["failing"], 9)
        self.assertEqual(parsed["subtest_events"], 24)
        self.assertEqual(parsed["errors"], 24)


class PytestParsing(unittest.TestCase):
    def test_summary_and_ids(self):
        out = ("PASSED tests/test_a.py::test_x\nPASSED tests/test_a.py::test_y[1-2]\nFAILED tests/test_b.py::test_z - AssertionError\n"
               "========= 1 failed, 2 passed in 0.12s =========\n")
        parsed = parse_pytest(out, "", 1)
        self.assertEqual((parsed["ran"], parsed["passed"], parsed["failing"]), (3, 2, 1))
        self.assertFalse(parsed["all_passed"])
        self.assertEqual(parsed["tests"][2]["outcome"], "FAIL")
        ok = parse_pytest("PASSED tests/t.py::a\n== 1 passed in 0.01s ==\n", "", 0)
        self.assertTrue(ok["all_passed"])
        quiet = parse_pytest("PASSED tests/t.py::a\nPASSED tests/t.py::b\n312 passed in 0.65s\n", "", 0)
        self.assertEqual((quiet["ran"], quiet["passed"]), (312, 312))
        self.assertTrue(quiet["all_passed"])
        skipped = parse_pytest("3 passed, 1 skipped, 2 failed in 1.00s\n", "", 1)
        self.assertEqual((skipped["ran"], skipped["failing"], skipped["skipped"]), (5, 2, 1))


if __name__ == "__main__":
    unittest.main()
