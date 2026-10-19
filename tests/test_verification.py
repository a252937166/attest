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
from attest.models.base import ModelError, ModelResult
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
# witness programs the fake contract auditor returns; the fake executor "runs" them by their exit marker and echoes the ids they name
# grounded: task criteria, and a literal-input witness in attest-witness/1 that calls the repository's own function (its origin
# resolves through durationkit/__init__.py to the definition in durationkit/parse.py)
WITNESS_DEMONSTRATES = ("import sys\nfrom durationkit import parse_duration\n\nseconds = parse_duration('90')\nif seconds == 90:\n"
                        "    print('CONTRADICTION TC1,TC2: for input \"1h\" TC1 demands 3600 and TC2 demands 60')\n    sys.exit(3)\n"
                        "print('NOT DEMONSTRATED: the reference value differs')\nsys.exit(0)\n")
# the revision-6 review's bypass of the old blacklist (an import alias of type builds a str subclass), verbatim but for the ids
WITNESS_ALIAS_BYPASS = ("from builtins import type as make_type\nimport sys\nZ = make_type('Z', (str,), {'__len__': (0).__int__})\nx = Z('a=b')\n"
                        "print('CONTRADICTION TC1: this value is a custom str subclass')\nsys.exit(3)\n")
WITNESS_DEMONSTRATES_DERIVED = "import sys\nprint('CONTRADICTION AC1,AC2: for input \"1h\" AC1 demands 3600 and AC2 demands 60')\nsys.exit(3)\n"  # specification criteria
WITNESS_UNCONSTRAINED = ("import sys\ndef required(x):\n    return 60\nprint('CONTRADICTION TC1,TC2: my own implementation returns 60 for \"1h\"')\nsys.exit(3)\n")
WITNESS_NOT_SHOWN = "import sys\nprint('NOT DEMONSTRATED: no input found up to length 6')\nsys.exit(0)\n"
PRIVATE_MARKER = "SYNTHETIC_PRIVATE_DIAGNOSTIC /opt/attest/private/module.py"  # must never reach a public record (R5-04)
BREAKER_WITH_SYNTAX_ERROR = SEALED_SRC.replace("class T(", "class B(").replace("def test_a(self):", "def test_a(self)")  # missing colon
CORRECTED_TEST_A = 'self.assertEqual(parse_duration("1h"), 3600.0, "corrected")'


class FakeProvider:
    name = "fake"

    def __init__(self, ledger, scenario="honest"):
        self.ledger = ledger
        self.scenario = scenario
        self.turn = 0

    def describe(self):
        return {"provider": self.name}

    def breaker_payload(self, stage):
        if self.scenario == "breaker_syntax_error" and not stage.endswith("-escalated"):
            return {"test_file": BREAKER_WITH_SYNTAX_ERROR, "test_count": 6, "notes": "fake broken breaker"}
        src = THIN_BREAKER_SRC if self.scenario == "no_mutants_thin_adversarial" else SEALED_SRC.replace("class T(", "class B(")
        return {"test_file": src, "test_count": 6, "notes": "fake breaker"}

    def arbitration_payload(self, stage):
        module = "test_sealed" if stage.endswith("sealed") else "test_breaker"
        klass = "T" if module == "test_sealed" else "B"
        original = SEALED_SRC if module == "test_sealed" else SEALED_SRC.replace("class T(", "class B(")
        defect = {"test_id": f"{module}.{klass}.test_a", "classification": "test_defect", "defect_kind": "wrong_expectation",
                  "rationale": "fake defect", "contract_basis": "fake"}
        corrected = original.replace('self.assertEqual(parse_duration("1h"), 3600.0)', CORRECTED_TEST_A, 1)
        if self.scenario in ("arb_clear", "arb_refactor", "sealed_one_fail", "sealed_one_crash", "sealed_one_code_error", "sealed_one_timeout",
                             "arb_base_lost", "arb_mutant_forged", "sealed_cleanup_incomplete"):
            return {"classifications": [defect], "corrected_module": corrected, "corrected_notes": "fixed defect"}
        if self.scenario == "arb_bad_ids":  # the arbiter talks about a test that did not fail (CORE-05)
            return {"classifications": [dict(defect, test_id=f"{module}.{klass}.test_zzz")], "corrected_module": corrected, "corrected_notes": "wrong ids"}
        if self.scenario == "arb_rebinds_import":  # replaces an existing import: the unchanged tests now call something else (CORE-05)
            rebound = corrected.replace("from durationkit import parse_duration", "from durationkit.other import parse_duration")
            return {"classifications": [defect], "corrected_module": rebound, "corrected_notes": "rebound import"}
        if self.scenario == "arb_changes_base":  # swaps the TestCase base class (CORE-05)
            rebased = "import unittest\nclass LooseTestCase(unittest.TestCase):\n    def assertEqual(self, a, b, *r): pass\n" + corrected.replace(
                "import unittest\n", "", 1).replace(f"class {klass}(unittest.TestCase)", f"class {klass}(LooseTestCase)")
            return {"classifications": [defect], "corrected_module": rebased, "corrected_notes": "changed base"}
        if self.scenario == "arb_adds_skip":  # decorates the failing test instead of fixing its body (CORE-05)
            skipped = corrected.replace("    def test_a(self):", "    @unittest.skip('x')\n    def test_a(self):", 1)
            return {"classifications": [defect], "corrected_module": skipped, "corrected_notes": "skipped it"}
        if self.scenario == "arb_identical":
            return {"classifications": [defect], "corrected_module": original, "corrected_notes": "no real change"}
        if self.scenario == "arb_drops_test":
            dropped = "\n".join(line for line in corrected.splitlines() if "def test_f" not in line and "parse_duration(\"1x\")" not in line) + "\n"
            return {"classifications": [defect], "corrected_module": dropped, "corrected_notes": "dropped a test"}
        if self.scenario == "arb_alters_passing":
            altered = corrected.replace('self.assertEqual(parse_duration("2m"), 120.0)', 'self.assertEqual(parse_duration("2m"), 120.0, "touched")', 1)
            return {"classifications": [defect], "corrected_module": altered, "corrected_notes": "touched a passing test"}
        return {"classifications": [{"test_id": "test_sealed.T.test_x", "classification": "implementation_bug", "defect_kind": None,
                                     "rationale": "fake", "contract_basis": "fake"}],
                "corrected_module": None, "corrected_notes": "fake: treated as a real bug, no correction"}

    def structured(self, role, prompt, schema, stage):
        if role == "spec" and self.scenario == "spec_provider_error":
            raise ModelError(f"HTTP 502 from https://private-gateway.invalid/run: {PRIVATE_MARKER}")  # fails the run at the first model call (R5-04)
        if role == "spec":
            infeasible = self.scenario in ("spec_infeasible_unproven", "spec_infeasible_demonstrated")
            two = ("coverage_gap", "contract_conflict", "spec_infeasible_demonstrated", "contract_claim_unproven", "spec_infeasible_unproven",
                   "contract_conflict_derived", "contract_conflict_mixed", "contract_conflict_unconstrained", "contract_conflict_alias_bypass")
            criteria = ["units work", "errors raise ValueError"] if self.scenario in two else ["units work"]
            payload = {"feasible": not infeasible, "infeasibility_reason": "fake: the criteria contradict" if infeasible else None,
                       "restated_task": "add units",
                       "interface_contract": [{"name": "parse_duration", "signature": "parse_duration(text: str) -> float",
                                               "behavior": "parse", "error_cases": ["ValueError"]}],
                       "acceptance_criteria": criteria, "out_of_scope": ["tests"], "external_references_needed": []}
        elif role == "seal":
            coverage = [{"criterion": 1, "tests": ["test_a", "test_b"]}]
            if self.scenario != "coverage_gap":
                coverage.append({"criterion": 2, "tests": ["test_f"]})
            payload = {"test_file": SEALED_SRC, "test_count": 6, "notes": "fake", "coverage": coverage}
        elif role == "break" or (role == "arbitrate" and stage.startswith("break-tests")):
            payload = self.breaker_payload(stage)
        elif role == "audit" and stage == "contract-audit":
            if self.scenario in ("contract_conflict", "spec_infeasible_demonstrated"):
                payload = {"consistent": False, "notes": "fake conflict", "conflicts": [
                    {"requirement_ids": ["TC1", "TC2"], "summary": "TC1 and TC2 demand different values for the same input", "witness": WITNESS_DEMONSTRATES}]}
            elif self.scenario == "contract_conflict_derived":
                payload = {"consistent": False, "notes": "fake derived conflict", "conflicts": [
                    {"requirement_ids": ["AC1", "AC2"], "summary": "AC1 and AC2 demand different values for the same input", "witness": WITNESS_DEMONSTRATES_DERIVED}]}
            elif self.scenario == "contract_conflict_mixed":
                payload = {"consistent": False, "notes": "fake mixed conflict", "conflicts": [
                    {"requirement_ids": ["TC1", "AC2"], "summary": "TC1 and AC2 demand different values", "witness": WITNESS_DEMONSTRATES}]}
            elif self.scenario == "contract_conflict_unconstrained":
                payload = {"consistent": False, "notes": "fake unconstrained conflict", "conflicts": [
                    {"requirement_ids": ["TC1", "TC2"], "summary": "my own implementation disagrees with the original", "witness": WITNESS_UNCONSTRAINED}]}
            elif self.scenario == "contract_conflict_alias_bypass":
                payload = {"consistent": False, "notes": "fake bypass of the old blacklist", "conflicts": [
                    {"requirement_ids": ["TC1"], "summary": "a custom str subclass built through an import alias of type", "witness": WITNESS_ALIAS_BYPASS}]}
            elif self.scenario in ("contract_claim_unproven", "spec_infeasible_unproven"):
                payload = {"consistent": False, "notes": "fake suspicion", "conflicts": [
                    {"requirement_ids": ["AC1"], "summary": "AC1 may be impossible", "witness": WITNESS_NOT_SHOWN}]}
            else:
                payload = {"consistent": True, "notes": "fake: consistent", "conflicts": []}
        elif role == "audit" and self.scenario == "drift_provider_error":
            raise ModelError(f"HTTP 502 from https://private-gateway.invalid/run: {PRIVATE_MARKER}")  # a provider failure carrying private text (R5-04)
        elif role == "audit":
            score = 0.9 if self.scenario == "drift_high" else 0.1
            payload = {"drift_score": score, "assessment": "off_target" if score > 0.5 else "aligned", "scope_narrowed": [],
                       "scope_widened": [], "unsupported_claims": [], "summary": "fake audit"}
        elif role == "arbitrate":
            payload = self.arbitration_payload(stage)
        else:
            self.turn += 1
            if self.scenario == "implementer_idle":
                payload = {"action": "read_file", "path": "durationkit/parse.py", "content": None, "find": None, "replace": None,
                           "start_line": None, "end_line": None, "code": None, "reason": "looking", "summary": None}
            elif self.turn == 1:
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
        self.decorate(call)
        self.ledger.add_call(call)
        return ModelResult(json=payload, text=None, call=call)

    def decorate(self, call):
        """Hook for paid fakes: set cost and reservation BEFORE the ledger records (and journals) the call."""


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
                # under test is not implemented, so every test errors; a corrected module must still fail here. In the
                # `arb_refactor` scenario the base already behaves correctly (a refactor), so the corrected adversarial module
                # passes on the base and must be caught by a mutant instead.
                red = name in ("sealed", "arbbase") and not candidate_present
                if red and name == "arbbase" and self.scenario in ("arb_refactor", "arb_mutant_forged"):
                    tests.append(self._record(test_id))  # a refactor: the corrected module passes on the base, so a mutant must catch it
                elif red:
                    tests.append(self._record(test_id, "ERROR", 1))
                elif name == "arbmut" and self.scenario in ("arb_refactor", "arb_mutant_forged") and k == 0:
                    tests.append(self._record(test_id, "FAIL", 1))
                elif mutant and self.scenario == "mutants_timeout" and k == 0:
                    tests.append(self._record(test_id, "TIMEOUT", None, signal=9, timed_out=True, child_outcome=None, nonce_ok=False))
                elif mutant:
                    survive = self.scenario == "mutants_survive"
                    tests.append(self._record(test_id) if (survive or k) else self._record(test_id, "FAIL", 1))
                elif name == "breaker" and self.scenario == "adversarial_forged_original" and k == 0:
                    tests.append(self._record(test_id, "FORGED", 1, nonce_ok=False, child_outcome="ok"))  # a forged child report (CORE-01)
                elif name == "breaker" and self.scenario in ("breaker_fail", "arb_clear", "arb_refactor", "arb_drops_test", "arb_alters_passing", "arb_identical",
                                                             "arb_base_lost", "arb_mutant_forged", "arb_bad_ids", "arb_rebinds_import", "arb_changes_base",
                                                             "arb_adds_skip") and k == 0:
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
            if self.scenario == "sealed_one_fail" and b"corrected" not in self._source(files, job["modules"][0]["path"]):
                tests[0].update(exit_code=1, outcome="FAIL", child_outcome="FAIL", failure_tail="AssertionError: 3600.0 != 60.0")
            if self.scenario == "sealed_one_code_error" and b"corrected" not in self._source(files, job["modules"][0]["path"]):
                tests[0].update(exit_code=1, outcome="ERROR", child_outcome="ERROR",
                                failure_tail='Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 5, in test_a\n    self.assertEqual(parse_duration("1h"), 3600.0)\n  File "/tmp/w/durationkit/parse.py", line 9, in parse_duration\n    raise TypeError("bad")\nTypeError: bad')
            if self.scenario == "sealed_one_crash" and b"corrected" not in self._source(files, job["modules"][0]["path"]):
                tests[0].update(exit_code=1, outcome="ERROR", child_outcome="ERROR",
                                failure_tail='Traceback (most recent call last):\n  File "/tmp/sealed/test_sealed.py", line 5, in test_a\n    a, b = (1, 2, 3)\nValueError: too many values to unpack (expected 2)')
            if self.scenario in ("sealed_one_timeout", "sealed_cleanup_incomplete") and b"corrected" not in self._source(files, job["modules"][0]["path"]):
                # the supervisor killed the child at the per-test budget (v7: the whole process group, cleanup recorded)
                tests[0].update(exit_code=None, signal=9, timed_out=True, outcome="TIMEOUT", child_outcome=None, nonce_ok=False,
                                cleanup={"group_killed": True, "grace_exceeded": self.scenario == "sealed_cleanup_incomplete", "escaped_killed": 0,
                                         "escaped_remaining": 1 if self.scenario == "sealed_cleanup_incomplete" else 0,
                                         "complete": self.scenario != "sealed_cleanup_incomplete"})
        if mutant and self.scenario == "mutants_incomplete":  # the supervisor never finished and discovered nothing (CORE-03)
            tests = []
            for module in modules:
                module["expected_ids"] = []
        canaries, canary_ok = [], None
        if job.get("canary"):
            forged = self.scenario == "forge_all_ok" and sealed_on_candidate
            canaries = [self._record(CANARY_PASS_ID),
                        self._record(CANARY_FAIL_ID) if forged else self._record(CANARY_FAIL_ID, "FAIL", 1)]
            canary_ok = not forged
        bad_nonce = ((self.scenario == "forged_nonce" and sealed_on_candidate) or (self.scenario == "mutants_unknown" and mutant)
                     or (self.scenario == "arb_mutant_forged" and name == "arbmut"))
        incomplete = mutant and self.scenario == "mutants_incomplete"
        report = {"supervisor": SUPERVISOR_VERSION, "privilege_separation": (self.scenario != "no_isolation") and not incomplete,
                  "operation_uid": 0 if self.scenario != "no_isolation" else 65534, "test_uid": 65534,
                  "nonce": nonce if not bad_nonce else "deadbeef", "completed": not incomplete, "modules": modules,
                  "sealed_sha256_before": modules[0]["sha256_before"] if modules else None,
                  "sealed_sha256_after": modules[0]["sha256_after"] if modules else None,
                  "expected_ids": [i for m in modules for i in m["expected_ids"]], "discovery_error": "OFFLINE: incomplete supervisor" if incomplete else None,
                  "tests": tests, "canaries": canaries, "canary_ok": canary_ok, "ran": len(tests), "python": "3.12.13",
                  "cleanup_incomplete": sum(1 for t in tests if t.get("cleanup") and not t["cleanup"].get("complete")), "procfs": True}
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
            elif name.startswith("witness-"):
                source = files.get(step["cmd"][-1], b"").decode()
                if "sys.exit(3)" in source:
                    # the fake "runs" the witness by echoing the marker line its source prints (so the ids it names are the ones recorded)
                    marker = next((line.split("'", 1)[1].rsplit("'", 1)[0] for line in source.splitlines() if "CONTRADICTION" in line), "CONTRADICTION TC1,TC2: fake")
                    results.append(StepResult(name, step["cmd"], 3, False, 0.1, marker + "\n", ""))
                else:
                    results.append(StepResult(name, step["cmd"], 0, False, 0.1, "NOT DEMONSTRATED: no input found up to length 6\n", ""))
            elif name.endswith("_result"):
                prefix = name[:-len("_result")]
                if self.scenario in ("premature_exit", "forged_text") and candidate_present and not mutant and prefix == "sealed":
                    results.append(StepResult(name, step["cmd"], 1, False, 0.0, "", "No such file"))
                elif self.scenario == "arb_base_lost" and prefix == "arbbase":
                    results.append(StepResult(name, step["cmd"], 1, False, 0.0, "", "No such file"))  # the base re-run's result was lost (CORE-01)
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


def run_scenario(scenario, apply=True, heldout=None, return_executor=False):
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

    def test_validated_correction_reruns_the_adversarial_gate(self):
        applied = run_scenario("arb_clear")
        self.assertEqual(applied["verdict"]["verdict"], "VERIFIED", applied["verdict"])
        module = applied["arbitration"]["modules"][0]
        self.assertTrue(module["validated"], module)
        self.assertEqual(module["corrected"]["changed_tests"], ["test_breaker.B.test_a"])
        self.assertIn("fail on the unmodified base", module["corrected"]["discrimination"])
        gate = applied["gates"]["adversarial_tests"]
        self.assertTrue(gate["ok"] and gate["corrected"], gate)
        self.assertEqual(gate["original_failing"], ["test_breaker.B.test_a"])
        self.assertEqual(applied["verdict"]["derivation"]["corrected_gates"], ["adversarial_tests"])
        self.assertEqual(applied["verdict"]["before_corrections"]["verdict"], "NEEDS HUMAN")
        self.assertIn("adversarial tests failed", " ".join(applied["verdict"]["before_corrections"]["reasons"]))
        self.assertEqual(applied["breaker"]["adversarial"]["corrected"]["sha256"], module["corrected"]["sha256"])
        self.assertFalse(applied["verdict"].get("cleared_by_arbitration", False))  # no legacy clearing: the gate itself was re-run

    def test_advisory_mode_records_the_validated_correction_but_keeps_the_hold(self):
        advisory = run_scenario("arb_clear", apply=False)
        self.assertEqual(advisory["verdict"]["verdict"], "NEEDS HUMAN", advisory["verdict"])
        self.assertTrue(advisory["arbitration"]["modules"][0]["validated"])
        self.assertEqual(advisory["arbitration"]["applied_to_gates"], [])
        self.assertFalse(advisory["gates"]["adversarial_tests"].get("corrected"))

    def test_corrections_that_drop_or_touch_other_tests_or_change_nothing_are_rejected(self):
        for scenario, expected in (("arb_drops_test", "set of test methods changed"), ("arb_alters_passing", "tests that were not failing were altered"),
                                   ("arb_identical", "identical to the original")):
            bundle = run_scenario(scenario)
            module = bundle["arbitration"]["modules"][0]
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", scenario)
            self.assertFalse(module["validated"], scenario)
            self.assertIn(expected, module["error"], scenario)
            self.assertIsNone(module["candidate_rerun"], f"{scenario}: a rejected correction is never run")

    def test_corrected_adversarial_module_that_passes_on_the_base_must_be_caught_by_a_mutant(self):
        bundle = run_scenario("arb_refactor")
        module = bundle["arbitration"]["modules"][0]
        self.assertTrue(module["validated"], module)
        self.assertIn("catch mutant", module["corrected"]["discrimination"])
        self.assertEqual(len(module["mutant_reruns"]), 1)
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")

    def test_sealed_assertion_failure_is_never_overridden(self):
        bundle = run_scenario("sealed_one_fail")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        module = bundle["arbitration"]["modules"][0]
        self.assertEqual(module["module"], "sealed")
        self.assertTrue(module["sealed_assertion_hold"])
        self.assertTrue(module["cleared_module"], "the correction was validated by execution and recorded for the human")
        self.assertFalse(module["validated"])
        self.assertEqual(bundle["arbitration"]["applied_to_gates"], [])
        self.assertIn("never overridden", bundle["arbitration"]["headline"])

    def test_sealed_error_raised_by_the_code_under_test_is_never_overridden(self):
        bundle = run_scenario("sealed_one_code_error")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        module = bundle["arbitration"]["modules"][0]
        self.assertTrue(module["sealed_assertion_hold"])
        self.assertEqual(module["sealed_disagreeing_tests"], ["test_sealed.T.test_a"])
        self.assertTrue(module["cleared_module"] and not module["validated"])
        self.assertIn("whatever its origin, is never overridden", bundle["arbitration"]["headline"])

    def test_sealed_test_that_crashed_in_its_own_body_is_held_not_corrected(self):
        """CORE-02: an exception inside the test body (here an unpacking error) can be caused by a bad candidate's return value,
        so neither its type nor its frame establishes a test defect; the executed sealed oracle stays with the human."""
        bundle = run_scenario("sealed_one_crash")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        module = bundle["arbitration"]["modules"][0]
        self.assertTrue(module["sealed_assertion_hold"])
        self.assertTrue(module["cleared_module"] and not module["validated"])
        self.assertFalse(bundle["gates"]["sealed_binding"].get("corrected"))
        self.assertEqual(bundle["arbitration"]["applied_to_gates"], [])

    def test_sealed_test_killed_at_its_timeout_is_corrected_and_the_breaker_reruns(self):
        """The one sealed correction that remains: a test the supervisor itself killed at the per-test budget (a workload fact,
        not a disagreement about behaviour) may be corrected, validated on the candidate and the base, and its gate re-run."""
        bundle, executor = run_scenario("sealed_one_timeout", return_executor=True)
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", bundle["verdict"])
        gate = bundle["gates"]["sealed_binding"]
        self.assertTrue(gate["ok"] and gate["corrected"], gate)
        self.assertIn("red check preserved", bundle["verification"]["corrected"]["discrimination"])
        self.assertTrue(bundle["verification"]["corrected"]["base_rerun"]["binding"]["ok"] is False)  # the base is red, as it must be
        self.assertEqual(bundle["verification"]["corrected"]["base_rerun"]["structural_problems"], [])
        self.assertTrue(bundle["breaker"]["after_sealed_correction"])
        self.assertTrue(bundle["gates"]["mutation"]["ok"] and bundle["gates"]["adversarial_tests"]["ok"])
        self.assertEqual([c["gate"] for c in bundle["verdict"]["corrections"]], ["sealed_binding"])
        self.assertTrue(bundle["verdict"]["corrections"][0]["breaker_rerun"])
        stages = [op["stage"] for op in executor.operations]
        self.assertIn("arbitrate-sealed-candidate", stages)
        self.assertTrue(any(s.startswith("mutant-") for s in stages[stages.index("arbitrate-sealed-candidate"):]), "mutants ran after the correction")

    def test_breaker_syntax_errors_escalate_to_the_arbiter_model(self):
        bundle = run_scenario("breaker_syntax_error")
        adversarial = bundle["breaker"]["adversarial"]
        self.assertTrue(adversarial["escalated"], adversarial)
        self.assertEqual(adversarial["attempts"], 3)
        self.assertEqual(adversarial["author_role"], "arbitrate")
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")
        self.assertTrue(bundle["gates"]["adversarial_tests"]["ok"])

    def test_demonstrated_contract_conflict_ends_infeasible_with_the_witness_recorded(self):
        bundle = run_scenario("contract_conflict")
        self.assertEqual(bundle["verdict"]["verdict"], "INFEASIBLE", bundle["verdict"])
        audit = bundle["contract_audit"]
        self.assertEqual(audit["outcome"], "contradiction demonstrated")
        conflict = audit["conflicts"][0]
        self.assertTrue(conflict["demonstrated"])
        self.assertEqual(conflict["exit_code"], 3)
        self.assertEqual(conflict["witness_path"], "contract_audit/witness_1.py")
        self.assertIn("CONTRADICTION", conflict["stdout_tail"])
        self.assertIsNone(bundle["sealed_tests"], "no sealing after a demonstrated contradiction")
        self.assertIn("executed witness in attest-witness/1 on the task's own criteria", bundle["verdict"]["reasons"][0])
        self.assertTrue(conflict["grounded"] and conflict["provenance"] == "task" and conflict["witness_constrained"])

    def test_claimed_conflict_without_a_demonstration_does_not_stop_the_run(self):
        bundle = run_scenario("contract_claim_unproven")
        self.assertEqual(bundle["contract_audit"]["outcome"], "conflicts claimed, none demonstrated")
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", bundle["verdict"])

    def test_spec_infeasibility_needs_a_demonstrated_witness(self):
        held = run_scenario("spec_infeasible_unproven")
        self.assertEqual(held["verdict"]["verdict"], "NEEDS HUMAN", held["verdict"])
        self.assertIn("no executed witness demonstrated", held["verdict"]["reasons"][0])
        shown = run_scenario("spec_infeasible_demonstrated")
        self.assertEqual(shown["verdict"]["verdict"], "INFEASIBLE", shown["verdict"])

    def test_turn_budget_exhausted_without_a_patch_is_an_unfinished_no_change(self):
        bundle = run_scenario("implementer_idle")
        self.assertEqual(bundle["verdict"]["verdict"], "NO CHANGE")
        self.assertTrue(bundle["candidate"]["unfinished"])
        self.assertFalse(bundle["candidate"]["implementer_finished"])
        self.assertIn("unfinished", bundle["verdict"]["reasons"][0])
        self.assertIn("without a patch", bundle["verdict"]["reasons"][0])

    def test_sealer_coverage_gaps_are_recorded_after_the_last_attempt(self):
        bundle = run_scenario("coverage_gap")
        self.assertEqual(bundle["sealed_tests"]["coverage_gaps"], ["AC2"])
        self.assertEqual(bundle["sealed_tests"]["attempts"], 3)  # the gap was fed back twice, then accepted and recorded
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED")

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
        self.assertEqual(bundle["arbitration"]["modules"], [], "a flipped canary is tampering, never a test defect to arbitrate")
        self.assertIn("not attempted", bundle["arbitration"]["headline"])
        self.assertIn("canary_must_fail_failed", bundle["arbitration"]["headline"])
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
