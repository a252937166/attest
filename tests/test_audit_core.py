"""Acceptance tests for the core verification findings of the 19 Oct 2026 audit (CORE-01 to CORE-07) and the atomic bundle write
(API-08). Offline only: the fake provider and executor of tests/test_verification.py supply controlled evidence; the real
supervisor runs locally (not as root) for the process-group and cleanup findings.

Counterexamples (must hold or fail the checker) and positive controls (must still verify) sit side by side so that a repair
which merely fails closed everywhere would be caught too."""

import contextlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from attest.core import exhibits as exhibits_module
from attest.core import pipeline as pipeline_module
from attest.core.check import check_bundle
from attest.core.manifest import MANIFEST_FILE, build_manifest, verify_manifest
from attest.core.pipeline import (Pipeline, classification_problems, classify_mutant_run, correction_problems, methods_changed,
                                  oracle_disagreement)
from attest.core.proof import write_bundle
from attest.core.sealed import (CLEANUP_GRACE_S, SUPERVISOR_VERSION, bind_verification, guest_files_for, new_nonce, outcome_class,
                                sealed_steps, static_test_ids, structural_problems)
from attest.core.task import TaskSpec
from attest.core.workspace import snapshot_repo
from attest.core.verdict import EVIDENCE_PROTOCOL_VERSION, expected_verdict, legacy_clearing_allowed
from attest.ledger import Ledger
from tests.test_verification import TASK, FakeExecutor, FakeProvider, run_scenario

ROOT = Path(__file__).resolve().parent.parent


def kept_run(scenario: str, heldout: dict | None = None, events: list | None = None, **kwargs) -> tuple[dict, Path, Path]:
    """Run the offline pipeline into a kept temporary directory; returns (bundle, run_dir, tmp_root). `heldout` sets the task's
    held-out tests; `events` collects the progress events (what the console would store)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"attest-audit-{scenario}-"))
    ledger = Ledger()
    task = TaskSpec.load(TASK)
    if heldout is not None:
        task.heldout_tests = heldout
    progress = (lambda event: events.append(event)) if events is not None else None
    pipeline = Pipeline(task=task, provider=FakeProvider(ledger, scenario), executor=FakeExecutor(ledger, scenario), ledger=ledger,
                        out_dir=tmp, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="audit-offline",
                        run_id=f"audit-{scenario}", progress=progress, **kwargs)
    with contextlib.redirect_stdout(io.StringIO()):
        bundle = pipeline.run()
    return bundle, pipeline.out_dir, tmp


def failed_checks(report: dict) -> dict:
    return {c["name"]: c["detail"] for c in report["checks"] if c["ok"] is False and c["severity"] == "error"}


def rewrite_bundle(run_dir: Path, mutate) -> None:
    """Apply `mutate(bundle)` to proof_bundle.json, re-render PROOF.md and regenerate the manifest, as a forger who controls the
    whole directory would, so that only the semantic finding under test can fail the checker (not a digest mismatch)."""
    path = run_dir / "proof_bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    mutate(bundle)
    write_bundle(run_dir, bundle)
    (run_dir / MANIFEST_FILE).write_text(json.dumps(build_manifest(run_dir, bundle.get("run_id")), indent=2) + "\n", encoding="utf-8")


def rewrite_raw(run_dir: Path, mutate) -> None:
    path = run_dir / "verify_raw.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    mutate(raw)
    path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    run_id = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8")).get("run_id")
    (run_dir / MANIFEST_FILE).write_text(json.dumps(build_manifest(run_dir, run_id), indent=2) + "\n", encoding="utf-8")


class Core01UntrustedDiscriminationEvidence(unittest.TestCase):
    """CORE-01: lost, forged or untrusted execution results never become discrimination evidence, and tampered original
    adversarial evidence is never turned into a test defect."""

    def test_lost_base_result_leaves_the_correction_unvalidated(self):
        bundle = run_scenario("arb_base_lost")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        module = bundle["arbitration"]["modules"][0]
        self.assertFalse(module["validated"])
        self.assertIn("base re-run evidence untrusted", module["error"])
        self.assertIn("result_file_present", module["base_rerun"]["untrusted"])
        self.assertEqual(module["base_rerun"]["corrected_tests_failing_on_base"], [])
        self.assertFalse(bundle["gates"]["adversarial_tests"].get("corrected"))

    def test_forged_mutant_rerun_is_not_discrimination(self):
        bundle = run_scenario("arb_mutant_forged")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        module = bundle["arbitration"]["modules"][0]
        self.assertFalse(module["validated"])
        self.assertIn("no validly killed mutant", module["error"])
        self.assertEqual(len(module["mutant_reruns"]), 3, "every candidate mutant was tried; none produced trusted evidence")
        for rerun in module["mutant_reruns"]:
            self.assertEqual(rerun["corrected_tests_failing"], [])
            self.assertIn("nonce_matches", rerun["structural_problems"])
            self.assertIn("structural problems", rerun["untrusted"])

    def test_forged_original_adversarial_failure_is_never_arbitrated(self):
        bundle = run_scenario("adversarial_forged_original")
        self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", bundle["verdict"])
        self.assertFalse(bundle["gates"]["adversarial_tests"]["ok"])
        arbitration = bundle["arbitration"]
        self.assertEqual(arbitration["modules"], [])
        self.assertIn("not attempted", arbitration["headline"])
        self.assertIn("no_missing_or_forged_result", arbitration["headline"])
        self.assertEqual(arbitration["applied_to_gates"], [])

    def test_positive_controls_still_verify_and_record_recomputable_evidence(self):
        for scenario in ("arb_clear", "arb_refactor"):
            bundle, run_dir, tmp = kept_run(scenario)
            try:
                self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", (scenario, bundle["verdict"]))
                corrected = bundle["breaker"]["adversarial"]["corrected"]
                self.assertTrue(corrected["base_rerun"]["binding"]["checks"]["nonce_matches"])
                self.assertEqual(corrected["base_rerun"]["structural_problems"], [])
                raw = json.loads((run_dir / "verify_raw.json").read_text())
                self.assertIsNotNone(raw["adversarial_corrected_base"])
                report = check_bundle(run_dir)
                self.assertTrue(report["ok"], failed_checks(report))
                names = {c["name"] for c in report["checks"]}
                self.assertIn("adversarial_base_evidence_recomputed", names)
                self.assertIn("adversarial_discrimination_recomputed", names)
                if scenario == "arb_refactor":
                    self.assertIn("adversarial_mutant_rerun_recomputed", names)
                    self.assertIsNotNone(raw["adversarial_corrected_mutants"])
                # tampering with the recorded base outcome is caught offline
                rewrite_bundle(run_dir, lambda b: b["breaker"]["adversarial"]["corrected"]["base_rerun"]["outcomes"].update(
                    {"test_breaker.B.test_a": "red"}) if scenario == "arb_refactor" else b["breaker"]["adversarial"]["corrected"]["base_rerun"].update({"corrected_tests_failing_on_base": []}))
                tampered = check_bundle(run_dir)
                self.assertFalse(tampered["ok"])
                self.assertIn("adversarial_base_evidence_recomputed", failed_checks(tampered))
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_outcome_classes_and_structural_filter(self):
        self.assertEqual(outcome_class({"exit_code": 0, "outcome": "ok", "nonce_ok": True}), "green")
        self.assertEqual(outcome_class({"exit_code": 1, "outcome": "FAIL", "nonce_ok": True}), "red")
        self.assertEqual(outcome_class({"exit_code": 1, "outcome": "ERROR", "nonce_ok": True}), "red")
        self.assertEqual(outcome_class({"exit_code": None, "signal": 9, "timed_out": True, "outcome": "TIMEOUT"}), "timeout")
        for record in ({"exit_code": 1, "outcome": "FORGED", "nonce_ok": False}, {"exit_code": None, "signal": 11, "outcome": "CRASH"},
                       {"exit_code": 1, "outcome": "MISSING_RESULT"}, {"exit_code": 0, "outcome": "MISMATCH", "nonce_ok": True},
                       {"exit_code": 1, "outcome": "skipped", "nonce_ok": True}, {"exit_code": 0, "outcome": "FAIL", "nonce_ok": True}):
            self.assertEqual(outcome_class(record), "untrusted", record)
        binding = {"checks": {"all_expected_pass": False, "no_nonzero_exit": False, "no_timeout": False, "no_signal": False, "nonce_matches": True}}
        result = {"tests": [{"id": "a", "signal": 9, "timed_out": True}]}
        self.assertEqual(structural_problems(binding, result), [], "a supervisor-killed timeout is excused, with its signal")
        result = {"tests": [{"id": "a", "signal": 11, "timed_out": False}]}
        self.assertEqual(structural_problems(binding, result), ["no_signal"], "a crash is structural")
        self.assertEqual(structural_problems({"checks": {"nonce_matches": False}}, {"tests": []}), ["nonce_matches"])
        self.assertEqual(structural_problems(None, None), ["result_file_present"])


class Core02SealedOracleNeverWeakened(unittest.TestCase):
    """CORE-02: an exception raised while a sealed test runs is a disagreement with the candidate whatever its type or frame;
    the executed oracle is never corrected on that basis. Only a supervisor-killed timeout may be corrected."""

    def test_candidate_caused_exceptions_in_test_code_are_disagreements(self):
        tails = ['  File "/tmp/sealed/test_sealed.py", line 5, in test_pair\n    a, b = f()\nValueError: too many values to unpack (expected 2)',
                 '  File "/tmp/sealed/test_sealed.py", line 5, in test_attr\n    self.assertEqual(f().value, 1)\nAttributeError: \'int\' object has no attribute \'value\'',
                 '  File "/tmp/sealed/test_sealed.py", line 5, in test_type\n    self.assertEqual(f() + 1, 2)\nTypeError: can only concatenate str (not "int") to str',
                 '  File "/tmp/sealed/test_sealed.py", line 5, in test_div\n    self.assertEqual(10 / f(), 5)\nZeroDivisionError: division by zero',
                 '  File "/tmp/sealed/test_sealed.py", line 5, in test_name\n    self.assertEqual(g(), 1)\nNameError: name \'g\' is not defined']
        for tail in tails:
            self.assertTrue(oracle_disagreement({"outcome": "ERROR", "failure_tail": tail}), tail)
        self.assertTrue(oracle_disagreement({"outcome": "FAIL", "failure_tail": "AssertionError: 1 != 2"}))
        self.assertFalse(oracle_disagreement({"outcome": "TIMEOUT", "timed_out": True}))

    def test_weakened_tuple_test_does_not_restore_verified(self):
        """The audit's example: a contract demands exactly (1, 2); the candidate returns (1, 2, 3); the correct test errors in
        its own body; the arbiter offers `a, b, *extra = f()`. The correction passes on the candidate and fails on the base, and
        the hold still stands."""
        for scenario in ("sealed_one_crash", "sealed_one_code_error", "sealed_one_fail"):
            bundle = run_scenario(scenario)
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", (scenario, bundle["verdict"]))
            module = bundle["arbitration"]["modules"][0]
            self.assertTrue(module["sealed_assertion_hold"], scenario)
            self.assertTrue(module["cleared_module"], f"{scenario}: the correction itself was validated by execution and recorded for the human")
            self.assertFalse(module["validated"], scenario)
            self.assertFalse(bundle["gates"]["sealed_binding"].get("corrected"), scenario)
            self.assertEqual(bundle["arbitration"]["applied_to_gates"], [], scenario)

    def test_supervisor_killed_timeout_is_the_only_sealed_correction(self):
        bundle = run_scenario("sealed_one_timeout")
        self.assertEqual(bundle["verdict"]["verdict"], "VERIFIED", bundle["verdict"])
        self.assertTrue(bundle["gates"]["sealed_binding"]["corrected"])
        self.assertEqual(bundle["verdict"]["corrections"][0]["gate"], "sealed_binding")


class Core03MutantEvidence(unittest.TestCase):
    """CORE-03: incomplete, non-isolated, forged, crashed or timed-out mutant runs are unknown, never killed, and `attest check`
    recomputes every mutant from its raw result."""

    def _result(self, **over):
        tests = [{"id": "test_sealed.T.test_a", "exit_code": 1, "signal": None, "timed_out": False, "outcome": "FAIL", "nonce_ok": True},
                 {"id": "test_sealed.T.test_b", "exit_code": 0, "signal": None, "timed_out": False, "outcome": "ok", "nonce_ok": True}]
        result = {"supervisor": SUPERVISOR_VERSION, "privilege_separation": True, "nonce": "n", "completed": True, "cleanup_incomplete": 0,
                  "sealed_sha256_before": "s", "sealed_sha256_after": "s", "expected_ids": [t["id"] for t in tests], "discovery_error": None,
                  "tests": tests, "canaries": [], "startup_hooks_before": [], "startup_hooks_after": []}
        result.update(over)
        return result

    def _classify(self, result):
        binding = bind_verification(result, ["test_sealed.T.test_a", "test_sealed.T.test_b"], "s", "n", canary=False)
        return classify_mutant_run(result, binding, ["test_sealed.T.test_a", "test_sealed.T.test_b"])

    def test_authentic_failure_kills_and_untrusted_runs_are_unknown(self):
        status, evidence, killed_by = self._classify(self._result())
        self.assertEqual((status, killed_by), ("killed", ["test_sealed.T.test_a"]), evidence)
        survived = self._result()
        survived["tests"][0].update(exit_code=0, outcome="ok")
        self.assertEqual(self._classify(survived)[0], "survived")
        for name, over in (("incomplete", {"completed": False}), ("no_isolation", {"privilege_separation": False}),
                           ("isolation_unrecorded", {"privilege_separation": None}), ("wrong_nonce", {"nonce": "other"}),
                           ("module_changed", {"sealed_sha256_after": "x"}), ("discovery_error", {"discovery_error": "boom"}),
                           ("zero_tests", {"tests": [], "expected_ids": []}), ("cleanup_incomplete", {"cleanup_incomplete": 1}),
                           ("startup_hook", {"startup_hooks_before": ["/tmp/w/sitecustomize.py"]})):
            status, evidence, _ = self._classify(self._result(**over))
            self.assertEqual(status, "unknown", (name, evidence))
        forged = self._result()
        forged["tests"][0].update(outcome="FORGED", nonce_ok=False)
        self.assertEqual(self._classify(forged)[0], "unknown")
        missing = self._result()
        missing["tests"][0].update(outcome="MISSING_RESULT", exit_code=1)
        self.assertEqual(self._classify(missing)[0], "unknown")
        crashed = self._result()
        crashed["tests"][0].update(outcome="CRASH", exit_code=None, signal=11)
        self.assertEqual(self._classify(crashed)[0], "unknown")
        timed = self._result()
        timed["tests"][0].update(outcome="TIMEOUT", exit_code=None, signal=9, timed_out=True, nonce_ok=False)
        status, evidence, _ = self._classify(timed)
        self.assertEqual(status, "unknown")
        self.assertIn("timed out", evidence)
        self.assertIsNone(self._classify(None)[2] or None)

    def test_incomplete_and_timed_out_mutant_runs_do_not_score_and_the_gate_holds(self):
        for scenario in ("mutants_incomplete", "mutants_timeout"):
            bundle = run_scenario(scenario)
            mutation = bundle["breaker"]["mutation"]
            self.assertEqual(mutation["killed"], 0, (scenario, mutation))
            self.assertEqual(mutation["unknown"], mutation["generated"], scenario)
            self.assertIsNone(mutation["score"])
            self.assertFalse(bundle["gates"]["mutation"]["ok"], scenario)
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", scenario)
            self.assertTrue(all(m["status"] == "unknown" for m in mutation["mutants"]), scenario)
        honest = run_scenario("honest")
        self.assertEqual(honest["breaker"]["mutation"]["killed"], honest["breaker"]["mutation"]["generated"])
        self.assertTrue(all(m["evidence"].startswith("1 sealed test") or "authentic" in m["evidence"] for m in honest["breaker"]["mutation"]["mutants"]))

    def test_checker_reclassifies_mutants_from_raw_results(self):
        bundle, run_dir, tmp = kept_run("honest")
        try:
            raw = json.loads((run_dir / "verify_raw.json").read_text())
            self.assertEqual(set(raw["mutants"]), {m["id"] for m in bundle["breaker"]["mutation"]["mutants"]})
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"], failed_checks(report))
            self.assertIn("mutants_recomputed", {c["name"] for c in report["checks"]})
            # forge a kill: mark a mutant's raw result incomplete while the record still says killed
            first = bundle["breaker"]["mutation"]["mutants"][0]["id"]
            rewrite_raw(run_dir, lambda r: r["mutants"][first].update({"completed": False}))
            tampered = check_bundle(run_dir)
            self.assertFalse(tampered["ok"])
            self.assertIn("mutants_recomputed", failed_checks(tampered))
            self.assertIn("mutation_score_recomputed", failed_checks(tampered))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Core04SupervisorProcessGroups(unittest.TestCase):
    """CORE-04: the real supervisor kills the test child's whole process group at the per-test timeout, drains pipes for a
    bounded grace only, reaps the child and records the cleanup; a descendant that escaped the group is reported."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-core04-"))
        self.repo = self.tmp / "w"
        (self.repo / "pkg").mkdir(parents=True)
        (self.repo / "pkg" / "__init__.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
        self.pidfile = self.tmp / "grandchild.pid"

    def tearDown(self):
        pid = self._grandchild()
        if pid:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _grandchild(self):
        try:
            return int(self.pidfile.read_text().strip() or 0)
        except (OSError, ValueError):
            return None

    def _alive(self, pid) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        try:
            waited, _ = os.waitpid(pid, os.WNOHANG)  # reap a zombie we may own
            return waited == 0
        except ChildProcessError:
            return True

    def _run(self, module_src: str, per_test_timeout: int = 2) -> tuple[dict, float]:
        suite_dir = self.tmp / "suite"
        files = guest_files_for(str(suite_dir), "test_mod", module_src, repo_dir=str(self.repo), extra_paths=[], canary=True)
        for path, data in files.items():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(data)
        nonce = new_nonce()
        steps = sealed_steps(sys.executable, str(self.repo), str(suite_dir), nonce, [], {}, timeout=120, per_test_timeout=per_test_timeout, step_prefix="s")
        env = {**os.environ, "PYTHONPATH": str(self.repo), "PIDFILE": str(self.pidfile)}
        started = time.monotonic()
        subprocess.run(steps[0]["cmd"], cwd=steps[0]["cwd"], env=env, capture_output=True, timeout=120)
        elapsed = time.monotonic() - started
        out = subprocess.run(steps[1]["cmd"], cwd=steps[1]["cwd"], env=env, capture_output=True, timeout=60).stdout.decode()
        return json.loads(out), elapsed

    GRANDCHILD = ("import os, time, signal\n"
                  "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                  "open(os.environ['PIDFILE'], 'w').write(str(os.getpid()))\n"
                  "time.sleep(120)\n")

    def test_descendant_holding_the_pipes_is_killed_with_the_group_and_the_timeout_is_bounded(self):
        module = ("import os, subprocess, sys, time, unittest\n"
                  "from pkg import f\n"
                  "class T(unittest.TestCase):\n"
                  "    def test_hang(self):\n"
                  f"        subprocess.Popen([sys.executable, '-c', {self.GRANDCHILD!r}])  # inherits stdout/stderr, ignores TERM\n"
                  "        time.sleep(120)\n"
                  "    def test_ok(self):\n"
                  "        self.assertEqual(f(1), 2)\n")
        result, elapsed = self._run(module, per_test_timeout=2)
        by = {t["id"].split(".")[-1]: t for t in result["tests"]}
        self.assertEqual(by["test_hang"]["outcome"], "TIMEOUT", by["test_hang"])
        self.assertTrue(by["test_hang"]["cleanup"]["group_killed"], by["test_hang"]["cleanup"])
        self.assertFalse(by["test_hang"]["cleanup"]["grace_exceeded"], "the grandchild died with the group, so the pipes closed at once")
        self.assertTrue(by["test_hang"]["cleanup"]["complete"])
        self.assertEqual(result["cleanup_incomplete"], 0)
        self.assertEqual(by["test_ok"]["outcome"], "ok")
        self.assertLess(elapsed, 2 + CLEANUP_GRACE_S + 8, "the supervisor returned within the timeout plus a bounded cleanup")
        pid = self._grandchild()
        self.assertTrue(pid)
        deadline = time.monotonic() + 5
        while self._alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(self._alive(pid), "no descendant remains")
        binding = bind_verification(result, static_test_ids(module, "test_mod"), None, result["nonce"])
        self.assertTrue(binding["checks"]["supervisor_cleanup_complete"])
        self.assertFalse(binding["checks"]["no_timeout"])

    def test_descendant_holding_the_result_fd_cannot_stall_the_drain(self):
        module = ("import os, subprocess, sys, time, unittest\n"
                  "from pkg import f\n"
                  "class T(unittest.TestCase):\n"
                  "    def test_hang(self):\n"
                  "        fd = int(sys.argv[2])  # the child's result pipe, handed to a sleeping grandchild\n"
                  f"        subprocess.Popen([sys.executable, '-c', {self.GRANDCHILD!r}], pass_fds=(fd,))\n"
                  "        time.sleep(120)\n"
                  "    def test_ok(self):\n"
                  "        self.assertEqual(f(1), 2)\n")
        result, elapsed = self._run(module, per_test_timeout=2)
        by = {t["id"].split(".")[-1]: t for t in result["tests"]}
        self.assertEqual(by["test_hang"]["outcome"], "TIMEOUT")
        self.assertTrue(by["test_hang"]["cleanup"]["complete"])
        self.assertEqual(by["test_hang"]["result_bytes"], 0)
        self.assertLess(elapsed, 2 + CLEANUP_GRACE_S + 8)
        pid = self._grandchild()
        deadline = time.monotonic() + 5
        while pid and self._alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(pid and self._alive(pid))

    def test_descendant_that_escaped_the_group_is_reported_and_bounded(self):
        module = ("import os, subprocess, sys, time, unittest\n"
                  "from pkg import f\n"
                  "class T(unittest.TestCase):\n"
                  "    def test_hang(self):\n"
                  f"        subprocess.Popen([sys.executable, '-c', {self.GRANDCHILD!r}], start_new_session=True)  # leaves the group\n"
                  "        time.sleep(120)\n"
                  "    def test_ok(self):\n"
                  "        self.assertEqual(f(1), 2)\n")
        result, elapsed = self._run(module, per_test_timeout=2)
        by = {t["id"].split(".")[-1]: t for t in result["tests"]}
        cleanup = by["test_hang"]["cleanup"]
        self.assertEqual(by["test_hang"]["outcome"], "TIMEOUT")
        self.assertTrue(cleanup["group_killed"])
        self.assertTrue(cleanup["grace_exceeded"], "the escaped grandchild kept stdout open past the grace period")
        self.assertLess(elapsed, 2 + 2 * CLEANUP_GRACE_S + 10, "bounded even when a descendant escaped")
        pid = self._grandchild()
        if os.path.isdir("/proc"):
            # the Linux guest: the marked escapee is found through /proc and killed, so the cleanup completes
            self.assertEqual(cleanup["escaped_killed"], 1, cleanup)
            self.assertEqual(cleanup["escaped_remaining"], 0)
            self.assertTrue(cleanup["complete"])
            self.assertEqual(result["cleanup_incomplete"], 0)
        else:
            # no /proc: the supervisor cannot find the escapee, says so, and the host binding refuses VERIFIED
            self.assertFalse(cleanup["complete"], cleanup)
            self.assertEqual(result["cleanup_incomplete"], 1)
            binding = bind_verification(result, static_test_ids(module, "test_mod"), None, result["nonce"])
            self.assertFalse(binding["checks"]["supervisor_cleanup_complete"])
            self.assertTrue(any("cleanup" in r for r in binding["reasons"]), binding["reasons"])
            self.assertTrue(pid and self._alive(pid), "the escapee is still alive here (killed in tearDown)")


class Core05CorrectionScope(unittest.TestCase):
    """CORE-05: a correction may change only the failing tests' bodies (plus additive, non-colliding imports); every other
    change is rejected, and the arbiter's classifications must cover exactly the failing tests."""

    ORIGINAL = ("import unittest\nfrom m import f\n\n\ndef helper():\n    return 1\n\n\nclass T(unittest.TestCase):\n    def setUp(self):\n        self.k = 1\n\n"
                "    def test_a(self):\n        self.assertEqual(f(1), 2)\n\n    def test_b(self):\n        self.assertEqual(f(2), 3)\n")

    def _problems(self, corrected, failing=("test_x.T.test_a",)):
        return correction_problems(self.ORIGINAL, corrected, "test_x", set(failing), 3)

    def test_body_only_corrections_with_additive_imports_pass(self):
        fixed = self.ORIGINAL.replace("self.assertEqual(f(1), 2)", "self.assertEqual(f(1), 3)")
        self.assertEqual(self._problems(fixed), ([], {"test_x.T.test_a"}))
        with_import = "import math\n" + fixed
        self.assertEqual(self._problems(with_import), ([], {"test_x.T.test_a"}))
        with_local_import = fixed.replace("        self.assertEqual(f(1), 3)", "        import math\n        self.assertEqual(f(1), math.floor(3.5))")
        self.assertEqual(self._problems(with_local_import), ([], {"test_x.T.test_a"}))

    def test_import_rebinding_removal_and_metadata_changes_are_rejected(self):
        fixed = self.ORIGINAL.replace("self.assertEqual(f(1), 2)", "self.assertEqual(f(1), 3)")
        cases = {
            "replaced import": fixed.replace("from m import f", "from other import f"),
            "removed import": fixed.replace("from m import f\n", ""),
            "rebinding import": "from other import f\n" + fixed,
            "rebinding helper": "from other import helper\n" + fixed,
            "base class": fixed.replace("class T(unittest.TestCase)", "class T(LooseTestCase)").replace("import unittest\n", "import unittest\nfrom loose import LooseTestCase\n"),
            "decorator": fixed.replace("    def test_a(self):", "    @unittest.skip('x')\n    def test_a(self):"),
            "signature": fixed.replace("    def test_a(self):", "    def test_a(self, *args):"),
            "helper body": fixed.replace("    return 1\n", "    return 2\n"),
            "setUp": fixed.replace("self.k = 1", "self.k = 2"),
            "class decorator": fixed.replace("class T(unittest.TestCase):", "@unittest.skip('all')\nclass T(unittest.TestCase):"),
            "module statement": fixed + "\nX = 1\n",
        }
        for name, corrected in cases.items():
            problems, _ = self._problems(corrected)
            self.assertTrue(problems, name)
            self.assertIn("<module>", methods_changed(self.ORIGINAL, corrected, "test_x"), name)
        touched_other = fixed.replace("self.assertEqual(f(2), 3)", "self.assertEqual(f(2), 4)")
        problems, changed = self._problems(touched_other)
        self.assertTrue(any("not failing" in p for p in problems), problems)
        self.assertEqual(changed, {"test_x.T.test_a", "test_x.T.test_b"})
        dropped = fixed.replace("    def test_b(self):\n        self.assertEqual(f(2), 3)\n", "")
        self.assertTrue(any("set of test methods" in p for p in self._problems(dropped)[0]))
        self.assertTrue(any("identical" in p for p in self._problems(self.ORIGINAL)[0]))

    def test_classification_ids_must_cover_exactly_the_failing_tests(self):
        failing = {"test_x.T.test_a", "test_x.T.test_b"}
        ok, by_id = classification_problems([{"test_id": "test_x.T.test_a", "classification": "test_defect"}, {"test_id": "test_b", "classification": "test_defect"}], failing)
        self.assertEqual(ok, [])
        self.assertEqual(set(by_id), failing)
        unknown, _ = classification_problems([{"test_id": "unknown.T.test_c", "classification": "test_defect"}], failing)
        self.assertTrue(any("unknown" in p for p in unknown) and any("without a classification" in p for p in unknown))
        duplicate, _ = classification_problems([{"test_id": "test_x.T.test_a"}, {"test_id": "test_a"}, {"test_id": "test_x.T.test_b"}], failing)
        self.assertTrue(any("duplicate" in p for p in duplicate))
        omitted, _ = classification_problems([{"test_id": "test_x.T.test_a"}], failing)
        self.assertTrue(any("without a classification" in p for p in omitted))

    def test_scenarios_reject_bad_ids_rebinding_base_change_and_skip(self):
        expectations = {"arb_bad_ids": "classification ids do not match", "arb_rebinds_import": "import statement(s) removed or rewritten",
                        "arb_changes_base": "class metadata", "arb_adds_skip": "class metadata"}
        for scenario, needle in expectations.items():
            bundle = run_scenario(scenario)
            module = bundle["arbitration"]["modules"][0]
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", scenario)
            self.assertFalse(module["validated"], scenario)
            self.assertIn(needle, module["error"], (scenario, module["error"]))
            self.assertIsNone(module["candidate_rerun"], f"{scenario}: a rejected correction is never executed")


class Core06EvidenceProtocol(unittest.TestCase):
    """CORE-06: a current bundle must carry the complete evidence for its verdict; historical bundles are checked for internal
    consistency only and never fully verified; the former apply mode is confined to dated historical bundles."""

    def test_current_verified_bundle_is_fully_verified_and_each_stripped_item_fails(self):
        bundle, run_dir, tmp = kept_run("honest")
        try:
            self.assertEqual(bundle["evidence_protocol"]["version"], EVIDENCE_PROTOCOL_VERSION)
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"], failed_checks(report))
            self.assertTrue(report["fully_verified"] and report["evidence_complete"] and report["manifest_verified"], report)
            self.assertFalse(report["historical"])
            strips = {
                "gate inventory": lambda b: b["gates"].pop("mutation"),
                "skipped gate": lambda b: b["gates"]["drift_audit"].update({"skipped": True, "ok": False}),
                "isolation not recorded": lambda b: b["verification"]["binding"]["checks"].update({"verifier_isolation_active": None}),
                "no contract audit": lambda b: b.__setitem__("contract_audit", None),
                "candidate facts": lambda b: b["candidate"].update({"scope_ok": None}),
                "no ledger": lambda b: b.__setitem__("ledger", {}),
                "no red run": lambda b: b.__setitem__("red_run", {}),
                "no sealed record": lambda b: b["sealed_tests"].update({"expected_ids": []}),
            }
            for name, strip in strips.items():
                copy = Path(tempfile.mkdtemp(prefix="attest-strip-")) / run_dir.name
                shutil.copytree(run_dir, copy)
                try:
                    rewrite_bundle(copy, strip)
                    stripped = check_bundle(copy)
                    self.assertFalse(stripped["ok"], name)
                    self.assertFalse(stripped["fully_verified"], name)
                    self.assertTrue({"required_evidence", "sealed_binding_recomputed", "gates_match_stage_records", "verdict_derivation"} & set(failed_checks(stripped)), (name, failed_checks(stripped)))
                finally:
                    shutil.rmtree(copy.parent, ignore_errors=True)
            for name, path in (("raw results", "verify_raw.json"), ("sealed module", "sealed/test_sealed.py"), ("adversarial module", "breaker_tests.py"), ("PROOF.md", "PROOF.md")):
                copy = Path(tempfile.mkdtemp(prefix="attest-strip-")) / run_dir.name
                shutil.copytree(run_dir, copy)
                try:
                    (copy / path).unlink()
                    run_id = json.loads((copy / "proof_bundle.json").read_text())["run_id"]
                    (copy / MANIFEST_FILE).write_text(json.dumps(build_manifest(copy, run_id)) + "\n")
                    stripped = check_bundle(copy)
                    self.assertFalse(stripped["ok"], name)
                    self.assertFalse(stripped["fully_verified"], name)
                finally:
                    shutil.rmtree(copy.parent, ignore_errors=True)
            # raw results of evaluated mutants are mandatory
            rewrite_raw(run_dir, lambda r: r.__setitem__("mutants", {}))
            stripped = check_bundle(run_dir)
            self.assertFalse(stripped["ok"])
            self.assertIn("required_evidence", failed_checks(stripped))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_current_infeasible_bundle_needs_its_executed_witness(self):
        bundle, run_dir, tmp = kept_run("contract_conflict")
        try:
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"] and report["fully_verified"], failed_checks(report))
            for name, strip in (("undemonstrated", lambda b: b["contract_audit"]["conflicts"][0].update({"demonstrated": False})),
                                ("no operation", lambda b: b["contract_audit"]["conflicts"][0].update({"operation_uuid": None})),
                                ("wrong exit", lambda b: b["contract_audit"]["conflicts"][0].update({"exit_code": 0})),
                                ("no marker", lambda b: b["contract_audit"]["conflicts"][0].update({"stdout_tail": "nothing"})),
                                ("no digest", lambda b: b["contract_audit"]["conflicts"][0].update({"witness_sha256": None})),
                                ("no requirements", lambda b: b["contract_audit"]["conflicts"][0].update({"requirement_ids": []}))):
                copy = Path(tempfile.mkdtemp(prefix="attest-inf-")) / run_dir.name
                shutil.copytree(run_dir, copy)
                try:
                    rewrite_bundle(copy, strip)
                    stripped = check_bundle(copy)
                    self.assertFalse(stripped["ok"], name)
                    self.assertFalse(stripped["fully_verified"], name)
                finally:
                    shutil.rmtree(copy.parent, ignore_errors=True)
            (run_dir / "contract_audit" / "witness_1.py").unlink()
            rewrite_bundle(run_dir, lambda b: None)
            self.assertFalse(check_bundle(run_dir)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_legacy_clearing_is_confined_to_dated_historical_bundles(self):
        bundle, run_dir, tmp = kept_run("breaker_fail")
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")

            def clear(b):
                b["verdict"].update({"verdict": "VERIFIED", "reasons": [], "cleared_by_arbitration": True})
                b["arbitration"].update({"applied": True, "cleared": True, "applied_to_gates": []})
            rewrite_bundle(run_dir, clear)
            current = check_bundle(run_dir)
            self.assertFalse(current["ok"])
            self.assertIn("verdict_derivation", failed_checks(current))
            copy = json.loads((run_dir / "proof_bundle.json").read_text())
            self.assertFalse(legacy_clearing_allowed(copy))
            copy.pop("evidence_protocol")
            copy["started_at_utc"] = "2026-10-18T12:00:00+00:00"
            copy["provenance"]["attest_version"] = "0.3.0"
            self.assertTrue(legacy_clearing_allowed(copy))
            self.assertTrue(expected_verdict(copy)["consistent"], "a dated historical bundle keeps the former apply mode")
            copy["started_at_utc"] = None
            self.assertFalse(legacy_clearing_allowed(copy))
            self.assertFalse(expected_verdict(copy)["consistent"], "an undated bundle gets no legacy clearing")
            copy["started_at_utc"] = "2026-10-19T00:00:01+00:00"
            self.assertFalse(legacy_clearing_allowed(copy))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_historical_bundle_is_partial_and_a_downgraded_claim_is_an_error(self):
        bundle, run_dir, tmp = kept_run("honest")
        try:
            rewrite_bundle(run_dir, lambda b: (b.pop("evidence_protocol"), b["provenance"].update({"attest_version": "0.4.0"})))
            historical = check_bundle(run_dir)
            self.assertTrue(historical["ok"], failed_checks(historical))
            self.assertTrue(historical["historical"])
            self.assertFalse(historical["fully_verified"])
            self.assertIsNone(historical["evidence_complete"])
            rewrite_bundle(run_dir, lambda b: b["provenance"].update({"attest_version": "0.5.0"}))
            downgraded = check_bundle(run_dir)
            self.assertFalse(downgraded["ok"])
            self.assertIn("evidence_protocol", failed_checks(downgraded))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_missing_isolation_field_is_not_isolation(self):
        bundle, run_dir, tmp = kept_run("honest")
        try:
            raw = json.loads((run_dir / "verify_raw.json").read_text())
            sealed = dict(raw["sealed"])
            sealed.pop("privilege_separation")
            binding = bind_verification(sealed, bundle["verification"]["expected_ids"], bundle["sealed_tests"]["sha256"], bundle["verification"]["sealed"]["nonce"])
            self.assertFalse(binding["ok"])
            self.assertFalse(binding["checks"]["verifier_isolation_active"])
            rewrite_raw(run_dir, lambda r: r["sealed"].pop("privilege_separation"))
            report = check_bundle(run_dir)
            self.assertFalse(report["ok"])
            self.assertIn("sealed_binding_recomputed", failed_checks(report))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Core07ManifestCompleteness(unittest.TestCase):
    """CORE-07: the integrity badge needs correct digests AND a complete, well-formed listing without links."""

    def setUp(self):
        self.bundle, self.run_dir, self.tmp = kept_run("honest")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _manifest(self):
        return json.loads((self.run_dir / MANIFEST_FILE).read_text())

    def _write(self, manifest):
        (self.run_dir / MANIFEST_FILE).write_text(json.dumps(manifest) + "\n")

    def test_complete_manifest_is_verified_and_each_defect_fails(self):
        clean = check_bundle(self.run_dir)
        self.assertTrue(clean["manifest_verified"] and clean["ok"], failed_checks(clean))
        base = self._manifest()
        self.assertEqual(base["version"], 2)
        empty = dict(base, files=[], file_count=0, total_bytes=0)
        self._write(empty)
        report = check_bundle(self.run_dir)
        self.assertFalse(report["ok"] or report["manifest_verified"])
        self.assertIn("manifest_complete", failed_checks(report))
        duplicate = dict(base, files=base["files"] + [base["files"][0]], file_count=len(base["files"]) + 1, total_bytes=base["total_bytes"] + base["files"][0]["bytes"])
        self._write(duplicate)
        report = check_bundle(self.run_dir)
        self.assertIn("manifest_entries", failed_checks(report))
        self.assertFalse(report["manifest_verified"])
        wrong_count = dict(base, file_count=base["file_count"] + 1)
        self._write(wrong_count)
        self.assertIn("manifest_entries", failed_checks(check_bundle(self.run_dir)))
        wrong_total = dict(base, total_bytes=base["total_bytes"] + 1)
        self._write(wrong_total)
        self.assertIn("manifest_entries", failed_checks(check_bundle(self.run_dir)))
        exclusions = dict(base, excluded=[MANIFEST_FILE, "proof_bundle.json"], files=[f for f in base["files"] if f["path"] != "proof_bundle.json"])
        exclusions.update(file_count=len(exclusions["files"]), total_bytes=sum(f["bytes"] for f in exclusions["files"]))
        self._write(exclusions)
        self.assertIn("manifest_entries", failed_checks(check_bundle(self.run_dir)))
        escaping = dict(base, files=base["files"] + [{"path": "../outside.json", "bytes": 1, "sha256": "0" * 64, "purpose": "x"}])
        escaping.update(file_count=len(escaping["files"]), total_bytes=sum(f["bytes"] for f in escaping["files"]))
        self._write(escaping)
        self.assertIn("manifest_entries", failed_checks(check_bundle(self.run_dir)))
        self._write(base)
        (self.run_dir / "extra.txt").write_text("unlisted\n")
        report = check_bundle(self.run_dir)
        self.assertIn("manifest_complete", failed_checks(report))
        self.assertFalse(report["manifest_verified"])
        (self.run_dir / "extra.txt").unlink()
        (self.run_dir / "link.json").symlink_to(self.run_dir / "spec.json")
        report = check_bundle(self.run_dir)
        self.assertIn("no_symlinks", failed_checks(report))
        self.assertFalse(report["manifest_verified"])
        (self.run_dir / "link.json").unlink()
        self.assertTrue(check_bundle(self.run_dir)["manifest_verified"])

    def test_historical_version_one_manifest_with_unlisted_files_is_partial_not_verified(self):
        rewrite_bundle(self.run_dir, lambda b: (b.pop("evidence_protocol"), b["provenance"].update({"attest_version": "0.4.0"})))
        base = self._manifest()
        self._write(dict(base, version=1))
        (self.run_dir / "late.json").write_text("{}\n")
        report = check_bundle(self.run_dir)
        self.assertTrue(report["ok"], failed_checks(report))  # a warning for a historical bundle
        self.assertFalse(report["manifest_verified"])
        self.assertTrue(report["manifest_partial"])
        self.assertTrue(any(c["name"] == "manifest_complete" and c["severity"] == "warning" for c in report["checks"]))

    def test_verify_manifest_reports_links_and_listing_facts(self):
        (self.run_dir / "link.json").symlink_to(self.run_dir / "spec.json")
        result = verify_manifest(self.run_dir, self._manifest())
        self.assertEqual(result["symlinks"], ["link.json"])
        self.assertTrue(result["complete"] and result["entries_ok"] and result["ok"])
        listed_link = dict(self._manifest())
        listed_link["files"] = listed_link["files"] + [{"path": "link.json", "bytes": 1, "sha256": "0" * 64, "purpose": "x"}]
        listed_link.update(file_count=len(listed_link["files"]), total_bytes=sum(f["bytes"] for f in listed_link["files"]))
        result = verify_manifest(self.run_dir, listed_link)
        self.assertFalse(result["ok"], "a listed entry that is a link is never opened")


class Api08AtomicArtifacts(unittest.TestCase):
    def test_bundle_and_artifacts_are_written_through_a_rename(self):
        bundle, run_dir, tmp = kept_run("honest")
        try:
            self.assertEqual([p.name for p in run_dir.rglob("*.tmp")], [])
            with mock.patch("os.replace", wraps=os.replace) as replace:
                write_bundle(run_dir, bundle)
            targets = [str(call.args[1]) for call in replace.call_args_list]
            self.assertIn(str(run_dir / "proof_bundle.json"), targets)
            self.assertIn(str(run_dir / "PROOF.md"), targets)
            self.assertTrue(all(str(call.args[0]).endswith(".tmp") for call in replace.call_args_list))
            self.assertEqual(json.loads((run_dir / "proof_bundle.json").read_text())["run_id"], bundle["run_id"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class WitnessValidation(unittest.TestCase):
    def test_witness_must_name_existing_requirements_and_the_marker_must_name_a_claimed_one(self):
        from types import SimpleNamespace
        from tests.test_verification import WITNESS_DEMONSTRATES
        from attest.sandbox.base import RunResult, StepResult

        class WitnessExecutor(FakeExecutor):
            stdout = "CONTRADICTION TC1,TC2: for input \"1h\" TC1 demands 3600 and TC2 demands 60\n"

            def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
                step = steps[0]
                return RunResult(stage=stage, operation_uuid="op-w", status="SUCCESS", exit_code=0, timed_out=False, signal=None, duration_s=0.1,
                                 image_uuid=image, result_image_uuid=None, steps=[StepResult(step["name"], step["cmd"], 3, False, 0.1, self.stdout, "")])
        tmp = Path(tempfile.mkdtemp(prefix="attest-witness-"))
        try:
            ledger = Ledger()
            executor = WitnessExecutor(ledger, "honest")
            pipeline = Pipeline(task=TaskSpec.load(TASK), provider=FakeProvider(ledger, "honest"), executor=executor, ledger=ledger,
                                out_dir=tmp, max_turns=2, tavily=None, profile_label="t")
            spec = {"acceptance_criteria": ["one", "two"], "restated_task": "r", "interface_contract": []}
            answers = iter([
                {"consistent": False, "notes": "", "conflicts": [{"requirement_ids": ["TC99"], "summary": "ghost", "witness": WITNESS_DEMONSTRATES}]},
                {"consistent": False, "notes": "", "conflicts": [{"requirement_ids": [], "summary": "nothing", "witness": WITNESS_DEMONSTRATES}]},
                {"consistent": False, "notes": "", "conflicts": [{"requirement_ids": ["TC2"], "summary": "real", "witness": WITNESS_DEMONSTRATES}]},
                {"consistent": False, "notes": "", "conflicts": [{"requirement_ids": ["TC1"], "summary": "real", "witness": WITNESS_DEMONSTRATES}]},
            ])
            pipeline.ask = lambda *args: SimpleNamespace(json=next(answers), call=SimpleNamespace(requested_model="fake"))
            snapshot = snapshot_repo(TaskSpec.load(TASK).repo_dir)
            with contextlib.redirect_stdout(io.StringIO()):
                ghost = pipeline.contract_audit(spec, snapshot, "ckpt")
                nothing = pipeline.contract_audit(spec, snapshot, "ckpt")
                real = pipeline.contract_audit(spec, snapshot, "ckpt")
                executor.stdout = "CONTRADICTION TC2: the marker names a requirement the conflict did not claim\n"
                unnamed = pipeline.contract_audit(spec, snapshot, "ckpt")
            self.assertFalse(ghost["conflicts"][0]["demonstrated"])
            self.assertIn("unknown requirement", ghost["conflicts"][0]["status"])
            self.assertIsNone(ghost["conflicts"][0]["operation_uuid"], "a witness for a nonexistent requirement is not executed")
            self.assertIn("names no requirement", nothing["conflicts"][0]["status"])
            self.assertTrue(real["conflicts"][0]["demonstrated"] and real["conflicts"][0]["grounded"])
            self.assertEqual(real["outcome"], "contradiction demonstrated")
            self.assertEqual(real["requirement_ids_known"]["task"][:2], ["TC1", "TC2"])
            self.assertFalse(unnamed["conflicts"][0]["demonstrated"])
            self.assertIn("does not name", unnamed["conflicts"][0]["status"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# The recorded evidence under reports/ is classified EXPLICITLY (revision-6 review, item 3): the historical corpus is the frozen set of
# report folders recorded before the evidence protocol existed, the modern corpus names every folder recorded under a protocol with
# that protocol, and every run directory must belong to exactly one class, so that new evidence can never silently join (or be
# tested as) the historical corpus. A new batch folder fails RecordedCorpusInventory until it is added to MODERN_CORPUS.
HISTORICAL_CORPUS = (  # recorded before Attest 0.5.0 (19 Oct 2026 07:58 UTC); frozen
    "attest-first-slice-2026-10-15", "attest-verification-2026-10-15", "attest-evaluation-2026-10-16", "attest-m1-2026-10-16",
    "attest-m4-2026-10-17", "attest-reliability-2026-10-17", "attest-freeze-2026-10-17", "attest-evaluation-2026-10-17-nebius-m5",
    "attest-revision-2026-10-19/evaluation-codex-2", "attest-revision-2026-10-19/evaluation-codex-3",
    "attest-revision-2026-10-19/evaluation-codex-semver", "attest-revision-2026-10-19/evaluation-codex-slugkit",
    "attest-revision-2026-10-19/runs-luna")
MODERN_CORPUS = {  # folder -> the evidence protocol every bundle in it declares
    "attest-audit-repairs-2026-10-19/evaluation-codex": 2,
    "attest-audit-repairs-2026-10-19/evaluation-codex-2": 2,
    "attest-revision5-repairs-2026-10-19/evaluation-codex": 3,
    "attest-revision6-repairs-2026-10-19/evaluation-codex": 4,
    "attest-revision6-repairs-2026-10-19/evaluation-codex-2": 4,
    "attest-revision6-repairs-2026-10-19/evaluation-codex-3": 4,
    "attest-revision6-repairs-2026-10-19/evaluation-codex-4": 4,
    "attest-revision7-repairs-2026-10-19/evaluation-codex": 4,  # revision 8 (protocol unchanged); the batch the 19 Oct 19:0x outage stopped
    "attest-revision7-repairs-2026-10-19/evaluation-codex-2": 4,
    "attest-revision7-repairs-2026-10-19/evaluation-codex-3": 4,
    "attest-revision9-repairs-2026-10-20/live-codex": 5,  # revision 9: one development run of the clean checkout, evidence protocol 5
    "attest-revision10-repairs-2026-10-20/live-codex": 5,  # revision 10: one development run of the clean checkout of 775248c, protocol 5
    "attest-validation-2026-10-21-nebius-r10/smoke": 5,  # the two-run Nemotron smoke test of the pinned 0.10.0 checkout, 20-21 Oct
    "attest-demo-run-2026-10-21/bundle": 5,  # the owner-approved live run of the demonstration film (0.10.3, 21 Oct): NO CHANGE
    "attest-evaluation-2026-10-21-nebius-r10": 5,  # the paid 32-cell Nemotron evaluation of the pinned 0.10.0 checkout, 21 Oct
}
KNOWN_DEFECTIVE = (  # partial copies or a stopped batch; they fail attest check by construction and are not exported
    "attest-hardening-2026-10-16/semver-v2-codex-verified", "attest-hardening-2026-10-16/smoke-run-durationkit-codex",
    "attest-revision-2026-10-19/evaluation-codex")
SYNTHETIC_DEFECTIVE = ("attest-audit-2026-10-19/synthetic-bundles",)  # the 19 Oct audit's deliberately defective bundles


def _recorded_run_dirs() -> list[tuple[str, Path]]:
    found = []
    for bundle in sorted(ROOT.glob("reports/*/**/proof_bundle.json")):
        run_dir = bundle.parent
        if "snapshot" in run_dir.parts:
            continue
        found.append((run_dir.relative_to(ROOT / "reports").as_posix(), run_dir))
    return found


def _within(rel: str, folder: str) -> bool:
    return rel == folder or rel.startswith(folder.rstrip("/") + "/")


def _classes(rel: str) -> list[str]:
    classes = [f"historical:{f}" for f in HISTORICAL_CORPUS if _within(rel, f)]
    classes += [f"modern:{f}" for f in MODERN_CORPUS if _within(rel, f)]
    classes += [f"defective:{f}" for f in KNOWN_DEFECTIVE + SYNTHETIC_DEFECTIVE if _within(rel, f)]
    return classes


class RecordedCorpusInventory(unittest.TestCase):
    def test_every_recorded_run_directory_belongs_to_exactly_one_class(self):
        unclassified, ambiguous = [], []
        for rel, _ in _recorded_run_dirs():
            classes = _classes(rel)
            if not classes:
                unclassified.append(rel)
            elif len(classes) > 1:
                ambiguous.append((rel, classes))
        self.assertEqual(unclassified, [], "classify new evidence folders in HISTORICAL_CORPUS (never for new runs) or MODERN_CORPUS")
        self.assertEqual(ambiguous, [])


class RecordedCorpusHistorical(unittest.TestCase):
    def test_the_frozen_historical_corpus_still_checks_as_historical(self):
        checked = 0
        failures = []
        for rel, run_dir in _recorded_run_dirs():
            if not any(c.startswith("historical:") for c in _classes(rel)):
                continue
            declared = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8")).get("evidence_protocol")
            self.assertIsNone(declared, f"{rel} declares an evidence protocol, so it is not historical: classify it in MODERN_CORPUS")
            report = check_bundle(run_dir)
            checked += 1
            self.assertTrue(report["historical"], rel)
            self.assertIsNone(report["protocol"], rel)
            self.assertFalse(report["fully_verified"], rel)
            self.assertIsNone(report["evidence_complete"], rel)
            if not report["ok"]:
                failures.append((rel, list(failed_checks(report))))
        self.assertGreater(checked, 100)
        self.assertEqual(failures, [])


class RecordedCorpusModern(unittest.TestCase):
    def test_every_modern_bundle_checks_complete_under_its_declared_protocol(self):
        checked = {folder: 0 for folder in MODERN_CORPUS}
        failures = []
        for rel, run_dir in _recorded_run_dirs():
            folder = next((f for f in MODERN_CORPUS if _within(rel, f)), None)
            if folder is None:
                continue
            report = check_bundle(run_dir)
            checked[folder] += 1
            self.assertEqual(report["protocol"], MODERN_CORPUS[folder], rel)
            self.assertFalse(report["historical"], rel)
            if not (report["ok"] and report["evidence_complete"] and report["fully_verified"]):
                failures.append((rel, failed_checks(report)))
        self.assertEqual(failures, [])
        self.assertEqual([f for f, n in checked.items() if n == 0], [], "every modern folder must contain bundles")


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------------------------------------------------
# Follow-up review of 19 Oct 2026 (revision 5 -> revision 6): R5-02, R5-03 and the pipeline side of R5-04.
from tests.test_verification import HELDOUT_SRC, PRIVATE_MARKER  # noqa: E402


def _copy_run(run_dir: Path) -> Path:
    copy = Path(tempfile.mkdtemp(prefix="attest-r5-copy-")) / run_dir.name
    shutil.copytree(run_dir, copy)
    return copy


class R502MandatoryStagesDerivedFromTheTask(unittest.TestCase):
    """R5-02: the mandatory stage records come from the protocol, the verdict, the frozen task and the execution mode; jointly
    deleting a stage record with its raw result or its gate must fail with a named completeness error."""

    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.run_dir, cls.tmp = kept_run("honest")
        cls.held_bundle, cls.held_run_dir, cls.held_tmp = kept_run("honest", heldout={"tests/test_heldout.py": HELDOUT_SRC})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)
        shutil.rmtree(cls.held_tmp, ignore_errors=True)

    def _stripped(self, run_dir: Path, mutate_bundle=None, mutate_raw=None) -> dict:
        copy = _copy_run(run_dir)
        try:
            if mutate_raw:
                rewrite_raw(copy, mutate_raw)
            if mutate_bundle:
                rewrite_bundle(copy, mutate_bundle)
            else:
                rewrite_bundle(copy, lambda b: None)
            return check_bundle(copy)
        finally:
            shutil.rmtree(copy.parent, ignore_errors=True)

    def test_positive_controls_are_complete(self):
        for run_dir in (self.run_dir, self.held_run_dir):
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"] and report["fully_verified"] and report["evidence_complete"], failed_checks(report))
            self.assertEqual(report["protocol"], EVIDENCE_PROTOCOL_VERSION)
        self.assertEqual(self.held_bundle["gates"]["heldout_suite"]["ok"], True)
        self.assertTrue(self.held_bundle["task"]["heldout_tests_sha256"])

    def test_joint_omission_of_the_existing_suite_evidence_fails_with_a_named_error(self):
        cases = {
            "stage and raw": (lambda b: b["verification"].pop("existing"), lambda r: r.pop("existing")),
            "stage and gate": (lambda b: (b["verification"].pop("existing"), b["gates"].pop("existing_suite")), None),
            "stage, raw and gate": (lambda b: (b["verification"].pop("existing"), b["gates"].pop("existing_suite")), lambda r: r.pop("existing")),
            "raw only": (None, lambda r: r.pop("existing")),
            "binding mode lost": (lambda b: b["execution"].pop("suite_binding"), None),
            "stage says stdout but mode is bound": (lambda b: b["verification"]["existing"].update({"evidence_class": "stdout"}), None),
        }
        for name, (mutate_bundle, mutate_raw) in cases.items():
            report = self._stripped(self.run_dir, mutate_bundle, mutate_raw)
            self.assertFalse(report["ok"], name)
            self.assertFalse(report["fully_verified"], name)
            self.assertIn("required_evidence", failed_checks(report), (name, failed_checks(report)))
            needle = "binding" if name == "binding mode lost" else "existing"
            self.assertIn(needle, failed_checks(report)["required_evidence"].lower(), name)

    def test_joint_omission_of_held_out_evidence_fails_when_the_task_declares_held_out_tests(self):
        cases = {
            "stage and raw": (lambda b: b["verification"].__setitem__("heldout", None), lambda r: r.pop("heldout")),
            "stage and gate": (lambda b: (b["verification"].__setitem__("heldout", None), b["gates"].pop("heldout_suite")), None),
            "stage, raw and gate": (lambda b: (b["verification"].__setitem__("heldout", None), b["gates"].pop("heldout_suite")), lambda r: r.pop("heldout")),
        }
        for name, (mutate_bundle, mutate_raw) in cases.items():
            report = self._stripped(self.held_run_dir, mutate_bundle, mutate_raw)
            self.assertFalse(report["ok"], name)
            self.assertIn("held-out", failed_checks(report).get("required_evidence", "").lower(), (name, failed_checks(report)))
        # the other direction: held-out evidence on a task that declares none is also a completeness error
        report = self._stripped(self.run_dir, lambda b: (b["verification"].__setitem__("heldout", self.held_bundle["verification"]["heldout"]),
                                                          b["gates"].__setitem__("heldout_suite", {"ok": True, "detail": "x", "evidence_class": "bound"})))
        self.assertIn("declares no held-out tests", failed_checks(report).get("required_evidence", ""))

    def test_gate_without_its_stage_record_is_an_error_for_any_current_verdict(self):
        report = self._stripped(self.run_dir, lambda b: (b["verification"].pop("existing"), b["verdict"].update({"verdict": "NEEDS HUMAN", "reasons": ["x"]}),
                                                          b["gates"]["drift_audit"].update({"ok": False})))
        self.assertFalse(report["ok"])
        self.assertIn("has no stage record", failed_checks(report).get("required_evidence", ""))
        self.assertIn("gates_match_stage_records", failed_checks(report))

    def test_historical_copy_keeps_partial_handling(self):
        report = self._stripped(self.run_dir, lambda b: (b["verification"].pop("existing"), b.pop("evidence_protocol"), b["provenance"].update({"attest_version": "0.4.0"})),
                                lambda r: r.pop("existing"))
        self.assertTrue(report["ok"], failed_checks(report))
        self.assertTrue(report["historical"])
        self.assertFalse(report["fully_verified"])
        self.assertIsNone(report["evidence_complete"])


class R503GroundedInfeasibility(unittest.TestCase):
    """R5-03: only a demonstrated conflict grounded in the requester's own criteria, with a constrained witness inside the input
    domain, may end a run as INFEASIBLE; derived, mixed or unconstrained demonstrations are held for a human."""

    def test_grounded_conflict_ends_infeasible_and_checks_complete_under_the_current_protocol(self):
        bundle, run_dir, tmp = kept_run("contract_conflict")
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "INFEASIBLE")
            conflict = bundle["contract_audit"]["conflicts"][0]
            self.assertEqual((conflict["provenance"], conflict["witness_constrained"], conflict["grounded"]), ("task", True, True))
            self.assertIn("input_domain", bundle["contract_audit"])
            self.assertEqual(bundle["contract_audit"]["witness_language"], "attest-witness/1")
            self.assertTrue(conflict["witness_language"]["conforms"])
            self.assertEqual(sorted(conflict["witness_language"]["repository_files"]), ["durationkit/__init__.py", "durationkit/parse.py"])
            for path in conflict["witness_language"]["repository_files"]:
                self.assertTrue((run_dir / "contract_audit/repository" / path).is_file(), path)
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"] and report["fully_verified"], failed_checks(report))
            self.assertEqual(report["protocol"], EVIDENCE_PROTOCOL_VERSION)
            self.assertGreaterEqual(EVIDENCE_PROTOCOL_VERSION, 4)
            self.assertTrue(any(c["name"] == "witness_language_rederived" and c["ok"] for c in report["checks"]))
            # forging the grounded flag on a conflict that names derived criteria is caught offline
            rewrite_bundle(run_dir, lambda b: b["contract_audit"]["conflicts"][0].update({"requirement_ids": ["AC1", "AC2"]}))
            forged = check_bundle(run_dir)
            self.assertFalse(forged["ok"])
            self.assertIn("not all the task's own", failed_checks(forged).get("required_evidence", ""))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_derived_mixed_and_unconstrained_demonstrations_are_held(self):
        expectations = {"contract_conflict_derived": ("derived", True), "contract_conflict_mixed": ("mixed", True), "contract_conflict_unconstrained": ("task", False)}
        for scenario, (provenance, constrained) in expectations.items():
            bundle, run_dir, tmp = kept_run(scenario)
            try:
                self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN", (scenario, bundle["verdict"]))
                conflict = bundle["contract_audit"]["conflicts"][0]
                self.assertTrue(conflict["demonstrated"], scenario)
                self.assertFalse(conflict["grounded"], scenario)
                self.assertEqual(conflict["provenance"], provenance, scenario)
                self.assertEqual(conflict["witness_constrained"], constrained, scenario)
                if not constrained:
                    self.assertTrue(any("defines a function" in p for p in conflict["constraint_problems"]), conflict["constraint_problems"])
                self.assertIn("not grounded", bundle["verdict"]["reasons"][0])
                self.assertIsNone(bundle["sealed_tests"], "no sealing: the hold is decided before any code")
                decision = exhibits_module.decision(bundle)
                self.assertEqual(decision["reason_class"], "contract_conflict_held", scenario)
                self.assertIn("not grounded", decision["explanation"])
                report = check_bundle(run_dir)
                self.assertTrue(report["ok"] and report["fully_verified"], (scenario, failed_checks(report)))
                # the hold must never be recorded as INFEASIBLE: a forged verdict fails the required-evidence check
                rewrite_bundle(run_dir, lambda b: b["verdict"].update({"verdict": "INFEASIBLE"}))
                forged = check_bundle(run_dir)
                self.assertFalse(forged["ok"], scenario)
                self.assertIn("grounded", failed_checks(forged).get("required_evidence", ""), scenario)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_recorded_witnesses_classify_as_the_review_argued(self):
        from attest.core.pipeline import requirement_provenance, witness_constraint_problems
        from attest.core.witness import Repository
        repairs = ROOT / "reports/attest-audit-repairs-2026-10-19"
        kvparse = next(repairs.glob("evaluation-codex-2/runs/kvparse-refactor-001-*/contract_audit/witness_1.py"), None)
        rle_old = next(repairs.glob("evaluation-codex/runs/rle-encode-*/contract_audit/witness_1.py"), None)
        rle_new = next((ROOT / "reports/attest-revision5-repairs-2026-10-19").glob("evaluation-codex/runs/rle-encode-*/contract_audit/witness_1.py"), None)
        self.assertIsNotNone(kvparse, "recorded kvparse witness")
        self.assertIsNotNone(rle_old, "recorded revision-5 rle witness")
        self.assertIsNotNone(rle_new, "recorded revision-6 rle witness")
        kv_repo = Repository.from_snapshot(snapshot_repo(ROOT / "examples/eval/kvparse-refactor/repo"))
        rle_repo = lambda: Repository.from_snapshot(snapshot_repo(ROOT / "examples/eval/rle-encode/repo"))  # noqa: E731
        problems = witness_constraint_problems(kvparse.read_text(encoding="utf-8"), kv_repo)
        self.assertTrue(any("defines a class" in p for p in problems) and any("defines a function" in p for p in problems), problems)
        # the revision-5 rle witness passed the old blacklist; it calls type() and reads __name__, so it is outside the positive language
        old_problems = witness_constraint_problems(rle_old.read_text(encoding="utf-8"), rle_repo())
        self.assertTrue(any("calls type" in p for p in old_problems) and any("__name__" in p for p in old_problems), old_problems)
        # positive control from recorded evidence: the revision-6 witness is literal inputs plus the repository's own decode
        self.assertEqual(witness_constraint_problems(rle_new.read_text(encoding="utf-8"), rle_repo()), [])
        # the recorded kvparse conflict named only derived criteria of the specification, never the task's own
        self.assertEqual(requirement_provenance(["AC1", "AC2", "AC16"], {"TC1", "TC2"}, {f"AC{i}" for i in range(1, 19)}), "derived")
        self.assertEqual(requirement_provenance(["TC1", "AC2"], {"TC1"}, {"AC2"}), "mixed")
        self.assertEqual(requirement_provenance(["TC1"], {"TC1"}, {"AC2"}), "task")
        self.assertEqual(requirement_provenance(["ZZ1"], {"TC1"}, {"AC2"}), "unknown")
        # the language's vocabulary for the constructs the blacklist named
        for source, needle in (("x = lambda v: v\n", "defines a lambda"), ("Z = type('Z', (str,), {})\n", "calls type"), ("exec('1')\n", "calls exec"),
                               ("class Q(str):\n    pass\n", "defines a class"), ("def f():\n    pass\n", "defines a function")):
            self.assertTrue(any(needle in p for p in witness_constraint_problems(source)), source)
        pkg = Repository.from_snapshot({"pkg/__init__.py": b"def f(x):\n    return x\n"})
        self.assertEqual(witness_constraint_problems("import sys\nfrom pkg import f\nprint(f('a'))\nsys.exit(0)\n", pkg), [])
        self.assertTrue(witness_constraint_problems("import sys\nfrom pkg import f\nprint(f('a'))\nsys.exit(0)\n"),
                        "without the repository the import cannot be resolved, so the witness cannot conform")

    def test_recorded_protocol_two_infeasible_bundle_still_checks_under_its_own_protocol(self):
        run_dir = next((ROOT / "reports/attest-audit-repairs-2026-10-19/evaluation-codex/runs").glob("rle-encode-*"), None)
        self.assertIsNotNone(run_dir, "the recorded revision-5 INFEASIBLE bundle is part of the recorded evidence")
        report = check_bundle(run_dir)
        self.assertEqual(report["protocol"], 2)
        self.assertTrue(report["ok"] and report["evidence_complete"], failed_checks(report))


class R504DiagnosticsStayPrivate(unittest.TestCase):
    """R5-04: raw exception text never enters bundle reasons, stage records, progress events, the trajectory, PROOF.md or any
    artifact; it lives in the private sidecar behind a correlation reference, and the console's public routes never carry it."""

    def _all_public_text(self, run_dir: Path) -> str:
        return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in run_dir.rglob("*") if p.is_file())

    def test_provider_failure_at_the_first_call_is_sanitized_everywhere(self):
        events: list = []
        bundle, run_dir, tmp = kept_run("spec_provider_error", events=events)
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "ERROR")
            reason = bundle["verdict"]["reasons"][0]
            self.assertIn("HTTP 502", reason)
            self.assertIn("[ref ", reason)
            self.assertNotIn(PRIVATE_MARKER, reason)
            self.assertNotIn("private-gateway", reason)
            public = self._all_public_text(run_dir)
            self.assertNotIn(PRIVATE_MARKER, public)
            self.assertNotIn("private-gateway", public)
            self.assertFalse(any(PRIVATE_MARKER in e["message"] for e in events), "progress events are public")
            sidecar = tmp / "diagnostics" / f"{run_dir.name}.jsonl"
            self.assertTrue(sidecar.is_file(), "the private sidecar lives next to the run directories, outside the bundle")
            entries = [json.loads(line) for line in sidecar.read_text().splitlines()]
            self.assertTrue(any(PRIVATE_MARKER in e["detail"] for e in entries))
            self.assertIn(entries[-1]["reference"], reason)
            manifest = json.loads((run_dir / MANIFEST_FILE).read_text())
            self.assertFalse(any("diagnostics" in f["path"] for f in manifest["files"]))
            self.assertTrue(check_bundle(run_dir)["ok"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_provider_failure_in_a_late_stage_is_sanitized_in_gates_and_reasons(self):
        events: list = []
        bundle, run_dir, tmp = kept_run("drift_provider_error", events=events)
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
            self.assertFalse(bundle["gates"]["drift_audit"]["ok"])
            self.assertIn("[ref ", bundle["gates"]["drift_audit"]["detail"])
            public = self._all_public_text(run_dir)
            self.assertNotIn(PRIVATE_MARKER, public)
            self.assertFalse(any(PRIVATE_MARKER in e["message"] for e in events))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_console_routes_never_carry_the_private_text(self):
        try:
            import httpx  # noqa: F401
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi.testclient needs httpx")
        import importlib
        import os
        import sys
        import zipfile
        bundle, run_dir, tmp = kept_run("spec_provider_error")
        data = Path(tempfile.mkdtemp(prefix="attest-r504-console-"))
        saved = dict(os.environ)
        try:
            os.environ.update({"ATTEST_DATA_DIR": str(data), "ATTEST_IMPORT_DIRS": str(tmp), "ATTEST_IMPORT_PROVIDERS": "fake",
                               "ATTEST_ADMIN_TOKEN": "", "ATTEST_PUBLIC_RUNS_PER_HOUR": "3"})
            sys.modules.pop("attest.app.server", None)
            server = importlib.import_module("attest.app.server")
            client = TestClient(server.app)
            try:
                runs = client.get("/api/runs").json()["runs"]
                self.assertTrue(any(r["run_id"] == bundle["run_id"] for r in runs), runs)
                texts = [client.get("/api/runs").text, client.get(f"/api/runs/{bundle['run_id']}").text, client.get(f"/api/runs/{bundle['run_id']}/events").text,
                         client.get(f"/api/runs/{bundle['run_id']}/artifacts/proof_bundle.json").text, client.get(f"/api/runs/{bundle['run_id']}/artifacts/PROOF.md").text]
                zipped = client.get(f"/api/runs/{bundle['run_id']}/bundle.zip")
                self.assertEqual(zipped.status_code, 200)
                with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
                    texts.extend(archive.read(name).decode("utf-8", "replace") for name in archive.namelist())
                    self.assertFalse(any("diagnostics" in name for name in archive.namelist()))
                for text in texts:
                    self.assertNotIn(PRIVATE_MARKER, text)
                    self.assertNotIn("private-gateway", text)
            finally:
                client.close()
                server.store._conn.close()
        finally:
            os.environ.clear()
            os.environ.update(saved)
            sys.modules.pop("attest.app.server", None)
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(data, ignore_errors=True)


class R504CallRecordsStayPublic(unittest.TestCase):
    """R5-04, the accounting carrier: a failed model call's record (ledger, journal, bundle) carries the public vocabulary and a
    correlation reference; the provider's raw error text (URL, response body) goes to the private sidecar only."""

    def _sidecar(self, tmp: Path, run_id: str):
        from attest.core.diagnostics import Diagnostics
        return Diagnostics(run_id, tmp / "diagnostics")

    def test_nebius_http_and_transport_failures_are_recorded_publicly(self):
        from attest.http import HttpError, TransportError
        from attest.models.base import ModelError
        from attest.models.nebius_tokenfactory import NebiusTokenFactory
        tmp = Path(tempfile.mkdtemp(prefix="attest-r504-calls-"))
        try:
            body = {"error": {"message": f"{PRIVATE_MARKER} request body echo: secret-shaped-text-123456"}}
            failures = [HttpError(502, body, "https://api.example.invalid/v1/chat/completions?trace=" + PRIVATE_MARKER),
                        TransportError(f"timed out talking to https://api.example.invalid {PRIVATE_MARKER}")]
            sidecar_tool = self._sidecar(tmp, "calls-nebius")
            calls = []
            # revision 9: each failure stops its run (a 502 after the request was sent is uncertain too), so each one gets a run of its own
            for index, failure in enumerate(failures):
                ledger = Ledger()
                ledger.attach_sink(tmp / f"ledger-{index}.jsonl")
                ledger.diagnostics = sidecar_tool
                provider = NebiusTokenFactory("offline-fake-key", ledger, usd_cap=0.5)

                def fake(method, url, headers, payload=None, timeout=60, _failure=failure, **kw):
                    raise _failure

                with mock.patch("attest.models.nebius_tokenfactory.request_json", fake):
                    with self.assertRaises(ModelError) as caught:
                        provider.structured("spec", "p", {"type": "object", "properties": {}}, "spec")
                self.assertTrue(caught.exception.uncertain, f"failure {index} is uncertain: the request was sent")
                self.assertEqual(len(ledger.model_calls), 1)
                self.assertTrue(ledger.halted)
                calls.append(ledger.model_calls[0])
                journal = (tmp / f"ledger-{index}.jsonl").read_text(encoding="utf-8")
                self.assertNotIn(PRIVATE_MARKER, journal)
                self.assertNotIn(PRIVATE_MARKER, json.dumps(ledger.to_dict()))
            for call in calls:
                self.assertIn("[ref ", call.error or "")
                self.assertNotIn(PRIVATE_MARKER, call.error)
                self.assertNotIn("example.invalid", call.error)
                self.assertEqual(call.settlement, "unsettled")
            self.assertIn("HTTP 502", calls[0].error)
            self.assertIn("uncertain", calls[1].error)
            sidecar = (tmp / "diagnostics" / "calls-nebius.jsonl").read_text(encoding="utf-8")
            self.assertEqual(sidecar.count(PRIVATE_MARKER), 2, "both raw texts recorded privately, once each")
            for call in calls:
                self.assertIn(call.error.rsplit("[ref ", 1)[1].rstrip("]"), sidecar)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_gateway_failures_are_recorded_publicly_too(self):
        from attest.http import HttpError
        from attest.models.base import ModelError
        from attest.models.codex_gateway import CodexGateway
        from attest.models.pacing import RateGovernor
        tmp = Path(tempfile.mkdtemp(prefix="attest-r504-gateway-"))
        try:
            ledger = Ledger()
            ledger.attach_sink(tmp / "ledger.jsonl")  # every call takes a pending record before it is sent (revision 9)
            ledger.diagnostics = self._sidecar(tmp, "calls-gateway")
            governor = RateGovernor("offline-fake-key", state_path=None)  # explicit pacing in memory: nothing under HOME
            provider = CodexGateway("offline-fake-key", ledger, base_url="https://gateway.example.invalid/v1", governor=governor)
            provider._catalog = {"gpt-6-sol": ["low", "medium"], "gpt-6-astra": ["low", "medium"], "gpt-6-luna": ["low"]}

            def fake(method, url, headers, payload=None, timeout=60, **kw):
                if url.endswith("/status"):
                    return 200, {"limits": {"hourly_requests_enforced": False, "max_concurrent_requests": 1}}, {}
                raise HttpError(500, {"error": PRIVATE_MARKER}, url)

            with mock.patch("attest.models.codex_gateway.request_json", fake):
                with self.assertRaises(ModelError) as caught:
                    provider.structured("spec", "p", {"type": "object", "properties": {}}, "spec")
            self.assertTrue(caught.exception.uncertain, "an HTTP 500 after the request was sent may have run upstream (revision 9)")
            self.assertEqual(len(ledger.model_calls), 1)
            self.assertIn("HTTP 500", ledger.model_calls[0].error)
            self.assertNotIn(PRIVATE_MARKER, ledger.model_calls[0].error)
            self.assertNotIn("gateway.example.invalid", ledger.model_calls[0].error)
            self.assertIn(PRIVATE_MARKER, (tmp / "diagnostics" / "calls-gateway.jsonl").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_without_a_sink_the_record_still_carries_only_the_public_sentence(self):
        from attest.http import HttpError
        ledger = Ledger()
        text = ledger.public_error("spec-http", HttpError(503, {"error": PRIVATE_MARKER}, "https://x.invalid/" + PRIVATE_MARKER))
        self.assertEqual(text, "the model provider returned HTTP 503")


# ---------------------------------------------------------------------------------------------------------------------
# Revision-6 independent review (19 Oct 2026), item 1 (R5-03 continued): the constrained witness language attest-witness/1.
# The old rule was a list of forbidden spellings; the review bypassed it with an import alias of type. The language is a positive
# grammar whose call origins are resolved statically; anything outside it can only hold a run for a person.
from tests.test_verification import WITNESS_ALIAS_BYPASS, WITNESS_DEMONSTRATES  # noqa: E402

_EXIT = "print('CONTRADICTION TC1: demonstrated')\nimport sys\nsys.exit(3)\n"
BYPASS_PROGRAMS = {
    # imported aliases
    "imported alias of type (the review's program)": (WITNESS_ALIAS_BYPASS, "from the module builtins"),
    "imported builtins module": ("import builtins as b\nZ = b.type('Z', (str,), {})\n" + _EXIT, "the module builtins"),
    "imported alias of exec": ("from builtins import exec as run\nrun('x = 1')\n" + _EXIT, "from the module builtins"),
    "imported alias of eval": ("from builtins import eval as ev\nx = ev('1')\n" + _EXIT, "from the module builtins"),
    "imported types.new_class": ("from types import new_class as nc\nZ = nc('Z', (str,))\n" + _EXIT, "from the module types"),
    "imported types module": ("import types\nZ = types.new_class('Z', (str,))\n" + _EXIT, "the module types"),
    "imported operator.attrgetter": ("from operator import attrgetter\nT = attrgetter('real')\n" + _EXIT, "from the module operator"),
    "imported collections.namedtuple": ("from collections import namedtuple\nP = namedtuple('P', 'a')\n" + _EXIT, "from the module collections"),
    "imported typing.NamedTuple": ("from typing import NamedTuple\nP = NamedTuple('P', [('a', str)])\n" + _EXIT, "from the module typing"),
    "imported enum.Enum": ("from enum import Enum\nE = Enum('E', 'a b')\n" + _EXIT, "from the module enum"),
    # assigned aliases
    "assigned alias of type": ("make = type\nZ = make('Z', (str,), {})\n" + _EXIT, "uses the name type"),
    "assigned alias of eval": ("ev = eval\nx = ev('1')\n" + _EXIT, "uses the name eval"),
    "assigned alias of a repository function": ("from durationkit import parse_duration\nf = parse_duration\nx = f('1')\n" + _EXIT, "bound by an assignment"),
    "reassigned imported repository name": ("from durationkit import parse_duration\nparse_duration = str\nx = parse_duration('1')\n" + _EXIT, "bound by"),
    "alias held in a container": ("fs = {'f': str}\nx = fs['f']('a')\n" + _EXIT, "computed value (Subscript)"),
    # indirect factories and indirect calls
    "type through a dunder chain": ("T = (0).__class__.__class__\nZ = T('Z', (str,), {})\n" + _EXIT, "__class__"),
    "type through a call result": ("Z = str('x').__class__('Z', (str,), {})\n" + _EXIT, "__class__"),
    "builtins through a generator frame": ("g = (v for v in [1])\nb = g.gi_frame.f_builtins\n" + _EXIT, "gi_frame"),
    "builtins through sys.modules": ("import sys\nb = sys.modules['builtins']\n" + _EXIT, "sys.modules"),
    "getattr": ("t = getattr(str, 'mro')\n" + _EXIT, "calls getattr"),
    "vars": ("v = vars()\n" + _EXIT, "calls vars"),
    "__builtins__": ("t = __builtins__\n" + _EXIT, "uses the name __builtins__"),
    "__import__": ("b = __import__('builtins')\n" + _EXIT, "calls __import__"),
    "map over a value-held callable": ("f = str\nx = list(map(f, ['a']))\n" + _EXIT, "passes to builtins.map"),
    "sorted with a lambda key": ("x = sorted([1], key=lambda v: v)\n" + _EXIT, "computed callable (Lambda)"),
    # definitions
    "class definition (a str subclass)": ("class Z(str):\n    pass\nx = Z('a')\n" + _EXIT, "defines a class"),
    "function definition": ("def f():\n    return 1\nx = f()\n" + _EXIT, "defines a function"),
}
SYNTHETIC_REPOSITORY = {
    "pkg/__init__.py": b"from .core import *\n",
    "pkg/core.py": (b"from typing import NamedTuple\nimport collections\n\n\ndef good(x):\n    return x\n\n\nmake = type\n\n\ndef get_factory():\n"
                    b"    return type\n\n\nif True:\n    def maybe(x):\n        return x\n"),
}
REPOSITORY_ORIGIN_CASES = {
    "re-export of typing.NamedTuple": ("from pkg import NamedTuple\n" + _EXIT, "re-exported"),
    "re-export of the collections module": ("from pkg.core import collections\n" + _EXIT, "not part of the frozen repository"),
    "repository alias of type": ("from pkg import make\nZ = make('Z', (str,), {})\n" + _EXIT, "does not resolve"),
    "conditionally defined repository name": ("from pkg import maybe\n" + _EXIT, "conditionally"),
    "factory returned by the repository, called": ("from pkg import get_factory\nZ = get_factory()('Z', (str,), {})\n" + _EXIT, "computed value (Call)"),
    "factory returned by the repository, passed to map": ("from pkg import get_factory\nf = get_factory()\nZ = list(map(f, ['Z'], [(str,)], [{}]))\n" + _EXIT,
                                                           "passes to builtins.map"),
}
LITERAL_WITNESSES = {
    "the fake auditor's grounded witness": (WITNESS_DEMONSTRATES, "durationkit"),
    "standard library, comprehensions, try/except and value methods": (
        "import sys\nfrom itertools import groupby\nfrom durationkit import parse_duration\n\ncases = ['90', '1h', '2m']\nseen = []\n"
        "for text in cases:\n    try:\n        seen.append(parse_duration(text))\n    except ValueError as exc:\n        print('NOT DEMONSTRATED: ' + repr(exc))\n"
        "        sys.exit(0)\nruns = ''.join(k + str(sum(1 for _ in g)) for k, g in groupby('aab'))\nkey, sep, rest = str.partition('a=b', '=')\n"
        "names = sorted({t.lower() for t in cases}, key=str.lower)\nif seen and runs == 'a2b1' and sep:\n"
        "    print(f'CONTRADICTION TC1: {names[0]!r} gives {seen[0]!r}')\n    sys.exit(3)\nsys.exit(0)\n", "durationkit"),
}


def _durationkit() -> "Repository":
    from attest.core.witness import Repository
    return Repository.from_snapshot(snapshot_repo(TaskSpec.load(TASK).repo_dir))


class R61WitnessLanguage(unittest.TestCase):
    """Mechanical enforcement of the witness language: every bypass is outside it, every literal-input witness is inside it, and
    the pipeline and the offline checker both act on the analysis, never on a spelling or a recorded flag."""

    def test_every_bypass_program_is_outside_the_language_with_a_named_reason(self):
        from attest.core.witness import analyze_witness
        for name, (source, needle) in BYPASS_PROGRAMS.items():
            analysis = analyze_witness(source, _durationkit())
            self.assertFalse(analysis["conforms"], name)
            self.assertTrue(any(needle in problem for problem in analysis["problems"]), (name, analysis["problems"]))

    def test_repository_names_resolve_only_to_definitions_of_the_repository(self):
        from attest.core.witness import Repository, analyze_witness
        for name, (source, needle) in REPOSITORY_ORIGIN_CASES.items():
            analysis = analyze_witness(source, Repository.from_snapshot(SYNTHETIC_REPOSITORY))
            self.assertFalse(analysis["conforms"], name)
            self.assertTrue(any(needle in problem for problem in analysis["problems"]), (name, analysis["problems"]))
        resolved = analyze_witness("from pkg import good\nx = good('a')\n" + _EXIT, Repository.from_snapshot(SYNTHETIC_REPOSITORY))
        self.assertTrue(resolved["conforms"], resolved["problems"])
        self.assertEqual([o.get("file") for o in resolved["origins"] if o["origin"].startswith("repository")], ["pkg/core.py"])
        self.assertEqual(sorted(resolved["repository_files"]), ["pkg/__init__.py", "pkg/core.py"])
        shadowed = analyze_witness("import json\nx = json.loads('1')\n" + _EXIT, Repository.from_snapshot({"json.py": b"def loads(s):\n    return s\n"}))
        self.assertFalse(shadowed["conforms"])
        self.assertIn("shadows the standard-library module", shadowed["problems"][0])
        # origins, not spellings: a name that spells type but is bound to itertools.groupby is analysed as groupby
        spelled = analyze_witness("from itertools import groupby as type\nx = list(type('aab'))\n" + _EXIT, None)
        self.assertTrue(spelled["conforms"], spelled["problems"])

    def test_literal_input_witnesses_conform_and_record_their_origins(self):
        from attest.core.witness import analyze_witness
        for name, (source, package) in LITERAL_WITNESSES.items():
            analysis = analyze_witness(source, _durationkit())
            self.assertTrue(analysis["conforms"], (name, analysis["problems"]))
            origins = [o for o in analysis["origins"] if o["origin"] == "repository function"]
            self.assertEqual([(o["file"], o["via"]) for o in origins], [("durationkit/parse.py", ["durationkit/__init__.py"])], name)

    def _audit(self, witness: str, ids: list[str]) -> dict:
        from types import SimpleNamespace
        from attest.sandbox.base import RunResult, StepResult

        class WitnessExecutor(FakeExecutor):
            def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
                step = steps[0]
                stdout = f"CONTRADICTION {','.join(ids)}: executed by the controlled fake\n"
                return RunResult(stage=stage, operation_uuid="op-w", status="SUCCESS", exit_code=0, timed_out=False, signal=None, duration_s=0.1,
                                 image_uuid=image, result_image_uuid=None, steps=[StepResult(step["name"], step["cmd"], 3, False, 0.1, stdout, "")])
        tmp = Path(tempfile.mkdtemp(prefix="attest-r61-audit-"))
        try:
            ledger = Ledger()
            pipeline = Pipeline(task=TaskSpec.load(TASK), provider=FakeProvider(ledger, "honest"), executor=WitnessExecutor(ledger, "honest"),
                                ledger=ledger, out_dir=tmp, max_turns=2, tavily=None, profile_label="t")
            pipeline.ask = lambda *args: SimpleNamespace(json={"consistent": False, "notes": "", "conflicts": [
                {"requirement_ids": ids, "summary": "controlled", "witness": witness}]}, call=SimpleNamespace(requested_model="fake"))
            with contextlib.redirect_stdout(io.StringIO()):
                record = pipeline.contract_audit({"acceptance_criteria": ["one", "two"], "restated_task": "r", "interface_contract": []},
                                                 snapshot_repo(TaskSpec.load(TASK).repo_dir), "ckpt")
            copies = sorted(str(p.relative_to(pipeline.out_dir)) for p in (pipeline.out_dir / "contract_audit/repository").rglob("*") if p.is_file()) \
                if (pipeline.out_dir / "contract_audit/repository").is_dir() else []
            return record, copies
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_contract_audit_holds_every_bypass_and_grounds_only_the_literal_witness(self):
        for name, (source, _) in BYPASS_PROGRAMS.items():
            record, _ = self._audit(source, ["TC1"])
            conflict = record["conflicts"][0]
            self.assertTrue(conflict["demonstrated"], name)
            self.assertEqual(conflict["provenance"], "task", name)
            self.assertFalse(conflict["witness_constrained"], name)
            self.assertFalse(conflict["grounded"], name)
            self.assertIn("outside the constrained witness language", conflict["status"], name)
            self.assertNotEqual(record["outcome"], "contradiction demonstrated", name)
        record, copies = self._audit(WITNESS_DEMONSTRATES, ["TC1", "TC2"])
        conflict = record["conflicts"][0]
        self.assertTrue(conflict["grounded"] and conflict["witness_constrained"], conflict["status"])
        self.assertEqual(record["outcome"], "contradiction demonstrated")
        self.assertEqual(copies, ["contract_audit/repository/durationkit/__init__.py", "contract_audit/repository/durationkit/parse.py"])

    def test_the_reviews_program_end_to_end_is_held_and_never_checks_as_infeasible(self):
        bundle, run_dir, tmp = kept_run("contract_conflict_alias_bypass")
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "NEEDS HUMAN")
            conflict = bundle["contract_audit"]["conflicts"][0]
            self.assertEqual((conflict["provenance"], conflict["demonstrated"], conflict["witness_constrained"], conflict["grounded"]),
                             ("task", True, False, False))
            self.assertIn("witness outside attest-witness/1", bundle["verdict"]["reasons"][0])
            decision = exhibits_module.decision(bundle)
            self.assertEqual(decision["reason_class"], "contract_conflict_held")
            self.assertIn("attest-witness/1", decision["explanation"])
            report = check_bundle(run_dir)
            self.assertTrue(report["ok"] and report["fully_verified"], failed_checks(report))
            # a forger who flips the verdict and the flags still fails: the checker repeats the analysis from the witness file
            rewrite_bundle(run_dir, lambda b: (b["verdict"].update({"verdict": "INFEASIBLE"}),
                                               b["contract_audit"]["conflicts"][0].update({"grounded": True, "witness_constrained": True}),
                                               b["contract_audit"]["conflicts"][0]["witness_language"].update({"conforms": True, "problems": []})))
            forged = check_bundle(run_dir)
            self.assertFalse(forged["ok"])
            self.assertIn("outside the constrained witness language attest-witness/1", failed_checks(forged).get("required_evidence", ""))
            self.assertIn("witness_language_rederived", failed_checks(forged))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_checker_re_derives_grounding_from_the_witness_and_the_repository_copies(self):
        bundle, run_dir, tmp = kept_run("contract_conflict")
        try:
            self.assertEqual(bundle["verdict"]["verdict"], "INFEASIBLE")
            self.assertTrue(check_bundle(run_dir)["fully_verified"], "positive control")
            copy = _copy_run(run_dir)
            try:  # (a) the witness file swapped for the review's program, every record left claiming conformance
                (copy / "contract_audit/witness_1.py").write_text(WITNESS_ALIAS_BYPASS, encoding="utf-8")
                import hashlib
                rewrite_bundle(copy, lambda b: b["contract_audit"]["conflicts"][0].update(
                    {"witness_sha256": hashlib.sha256(WITNESS_ALIAS_BYPASS.encode("utf-8")).hexdigest()}))
                report = check_bundle(copy)
                self.assertFalse(report["ok"])
                self.assertIn("outside the constrained witness language", failed_checks(report).get("required_evidence", ""))
                self.assertIn("witness_language_rederived", failed_checks(report))
                # (d) the same bypass in a copy downgraded to protocol 3 is refused as well
                rewrite_bundle(copy, lambda b: b["evidence_protocol"].update({"version": 3}))
                self.assertIn("outside the constrained witness language", failed_checks(check_bundle(copy)).get("required_evidence", ""))
            finally:
                shutil.rmtree(copy.parent, ignore_errors=True)
            copy = _copy_run(run_dir)
            try:  # (b) a repository copy that differs from the frozen file cannot be read by the resolution
                parse = copy / "contract_audit/repository/durationkit/parse.py"
                parse.write_text(parse.read_text(encoding="utf-8") + "\nparse_duration = type\n", encoding="utf-8")
                rewrite_bundle(copy, lambda b: None)
                report = check_bundle(copy)
                self.assertFalse(report["ok"])
                self.assertIn("is not available", failed_checks(report).get("required_evidence", ""))
            finally:
                shutil.rmtree(copy.parent, ignore_errors=True)
            copy = _copy_run(run_dir)
            try:  # (c) without the copies the repository import cannot be resolved offline
                shutil.rmtree(copy / "contract_audit/repository")
                rewrite_bundle(copy, lambda b: None)
                report = check_bundle(copy)
                self.assertFalse(report["ok"])
                self.assertIn("outside the constrained witness language", failed_checks(report).get("required_evidence", ""))
            finally:
                shutil.rmtree(copy.parent, ignore_errors=True)
            copy = _copy_run(run_dir)
            try:  # (e) a recorded file list that hides a file the resolution reads
                rewrite_bundle(copy, lambda b: b["contract_audit"]["conflicts"][0]["witness_language"]["repository_files"].pop("durationkit/__init__.py"))
                report = check_bundle(copy)
                self.assertFalse(report["ok"])
                self.assertIn("recorded repository files differ", failed_checks(report).get("required_evidence", ""))
            finally:
                shutil.rmtree(copy.parent, ignore_errors=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
