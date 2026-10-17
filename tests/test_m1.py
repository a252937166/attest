"""Milestone M1 unit tests: static repository discovery, module binding, the tamper scan, and the real guest
supervisor and child programs executed locally (no sandbox, no root: privilege separation is recorded as inactive and
every other check is exercised for real, including the canaries and the start-up hook scan)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from attest.core.sealed import (CANARY_FAIL_ID, CANARY_PASS_ID, CHILD_FILE, JOB_FILE, SUPERVISOR_SRC, SUPERVISOR_VERSION,
                                bind_modules, bind_verification, guest_files_for, is_supervisor_step, module_name_for,
                                new_nonce, repo_suite_files, sealed_steps, sha256_text, static_repo_tests, static_test_ids,
                                summarize, unittest_discover_args)
from attest.core.tamper import scan_diff

SNAPSHOT = {
    "pkg/__init__.py": b"def f(x):\n    return x + 1\n",
    "tests/__init__.py": b"",
    "tests/test_a.py": b"import unittest\nfrom pkg import f\nclass A(unittest.TestCase):\n    def test_one(self): self.assertEqual(f(1), 2)\n    def test_two(self): self.assertEqual(f(2), 3)\n",
    "tests/helper.py": b"import unittest\nclass NotCollected(unittest.TestCase):\n    def test_x(self): pass\n",
    "tests/sub_no_init/test_b.py": b"import unittest\nclass B(unittest.TestCase):\n    def test_y(self): pass\n",
    "tests/subpkg/__init__.py": b"",
    "tests/subpkg/test_c.py": b"import unittest\nclass C(unittest.TestCase):\n    def test_z(self): pass\n",
}
DISCOVER = ["/usr/local/bin/python", "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]
SEALED = "import unittest\nfrom pkg import f\n\nclass T(unittest.TestCase):\n    def test_one(self): self.assertEqual(f(1), 2)\n    def test_two(self): self.assertEqual(f(2), 3)\n"
FORGING_PKG = ("import unittest\n"
               "def _run(self, result=None):\n    result.startTest(self); result.addSuccess(self); result.stopTest(self)\n"
               "unittest.TestCase.run = _run\n"
               "def f(x):\n    return x + 2\n")


class StaticDiscovery(unittest.TestCase):
    def test_discover_args(self):
        self.assertEqual(unittest_discover_args(DISCOVER), {"start": "tests", "top": ".", "pattern": "test*.py"})
        self.assertEqual(unittest_discover_args(["python", "-m", "unittest", "-v"]), {"start": ".", "top": ".", "pattern": "test*.py"})
        self.assertEqual(unittest_discover_args(["python", "-m", "unittest", "discover", "-p", "check_*.py"])["pattern"], "check_*.py")
        self.assertIsNone(unittest_discover_args(["python", "-m", "pytest", "-q", "tests"]))
        self.assertIsNone(unittest_discover_args(["python", "-m", "unittest", "tests.test_a"]))

    def test_static_repo_tests_mirrors_discovery_rules(self):
        plan = static_repo_tests(SNAPSHOT, DISCOVER)
        names = [m["name"] for m in plan["modules"]]
        self.assertEqual(names, ["tests.subpkg.test_c", "tests.test_a"])  # helper.py (pattern) and sub_no_init (no package) excluded
        self.assertEqual(plan["ids"], ["tests.subpkg.test_c.C.test_z", "tests.test_a.A.test_one", "tests.test_a.A.test_two"])
        self.assertEqual(plan["modules"][1]["sha256"], sha256_text(SNAPSHOT["tests/test_a.py"].decode()))
        self.assertIsNone(static_repo_tests(SNAPSHOT, ["python", "-m", "pytest"]))

    def test_module_name_for(self):
        self.assertEqual(module_name_for("tests/test_heldout.py", "."), "tests.test_heldout")
        self.assertEqual(module_name_for("tests/test_heldout.py", ""), "tests.test_heldout")
        self.assertIsNone(module_name_for("tests/data.txt", "."))
        self.assertEqual(module_name_for("src/tests/test_x.py", "src"), "tests.test_x")


class ModuleBinding(unittest.TestCase):
    def _result(self, nonce, sha, ids, **over):
        result = {"supervisor": SUPERVISOR_VERSION, "nonce": nonce, "completed": True, "privilege_separation": True,
                  "modules": [{"name": "tests.test_a", "path": "/tmp/w/tests/test_a.py", "sha256_before": sha, "sha256_after": sha,
                               "expected_ids": ids, "discovery_error": None}],
                  "expected_ids": ids, "sealed_sha256_before": sha, "sealed_sha256_after": sha, "discovery_error": None,
                  "tests": [{"id": i, "exit_code": 0, "signal": None, "timed_out": False, "outcome": "ok"} for i in ids],
                  "canaries": [{"id": CANARY_PASS_ID, "exit_code": 0, "outcome": "ok"}, {"id": CANARY_FAIL_ID, "exit_code": 1, "outcome": "FAIL"}],
                  "canary_ok": True, "startup_hooks_before": [], "startup_hooks_after": []}
        result.update(over)
        return result

    def test_bind_modules_ok_and_digest_mismatch(self):
        ids = ["tests.test_a.A.test_one", "tests.test_a.A.test_two"]
        expected = [{"name": "tests.test_a", "sha256": "ab" * 32, "ids": ids}]
        ok = bind_modules(self._result("n", "ab" * 32, ids), expected, "n")
        self.assertTrue(ok["ok"], ok)
        bad = bind_modules(self._result("n", "cd" * 32, ids), expected, "n")
        self.assertFalse(bad["ok"])
        self.assertFalse(bad["checks"]["module_digests_unchanged"])
        self.assertTrue(any("integrity" in r for r in bad["reasons"]))
        other = bind_modules(self._result("n", "ab" * 32, ids), [{"name": "tests.test_b", "sha256": "ab" * 32, "ids": ids}], "n")
        self.assertFalse(other["checks"]["module_set_matches"])

    def test_startup_hook_and_missing_canaries_block(self):
        ids = ["tests.test_a.A.test_one"]
        expected = [{"name": "tests.test_a", "sha256": "ab" * 32, "ids": ids}]
        hooked = bind_modules(self._result("n", "ab" * 32, ids, startup_hooks_after=["/tmp/w/sitecustomize.py"]), expected, "n")
        self.assertFalse(hooked["checks"]["no_startup_hooks_on_import_path"])
        self.assertTrue(any("start-up hook" in r for r in hooked["reasons"]), hooked)
        no_canary = bind_verification(self._result("n", "ab" * 32, ids, canaries=[], canary_ok=None), ids, "ab" * 32, "n")
        self.assertFalse(no_canary["ok"])
        self.assertTrue(any("canaries did not run" in r for r in no_canary["reasons"]), no_canary)
        without = bind_verification(self._result("n", "ab" * 32, ids, canaries=[], canary_ok=None), ids, "ab" * 32, "n", canary=False)
        self.assertTrue(without["ok"], "mutant runs are bound without canaries by design")


class TamperScan(unittest.TestCase):
    def test_flags_suspicious_added_lines_only(self):
        diff = ("--- a/pkg/core.py\n+++ b/pkg/core.py\n@@ -1,3 +1,6 @@\n import os\n-old = 1\n+import sys\n+# sys.modules comment is ignored\n"
                "+sys.modules['x'] = None\n+open('/tmp/deps/sitecustomize.py', 'w').write('x')\n+def f(x):\n+    return x + 1\n")
        scan = scan_diff(diff)
        self.assertEqual(scan["added_lines"], 6)
        self.assertEqual([f["line"] for f in scan["flagged"]], [4, 5])  # context line 1, then added lines 2..7; comment on 3 ignored
        self.assertEqual(scan["flagged"][0]["path"], "pkg/core.py")
        self.assertIn("sys.modules manipulation", scan["labels"])
        self.assertIn("interpreter start-up hook", scan["labels"])
        clean = scan_diff("--- a/p.py\n+++ b/p.py\n@@ -1 +1,2 @@\n+def g(y):\n+    return y * 2\n")
        self.assertEqual(clean["flagged"], [])
        self.assertEqual(scan_diff("")["added_lines"], 0)


@unittest.skipIf(sys.platform.startswith("win"), "the guest programs are POSIX")
class RealSupervisorLocally(unittest.TestCase):
    """Run the actual SUPERVISOR_SRC and CHILD_SRC with the local interpreter (not root, no sandbox)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-m1-"))
        self.repo = self.tmp / "w"
        for rel, data in SNAPSHOT.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def _write(self, files: dict[str, bytes]) -> None:
        for path, data in files.items():
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

    def _run_steps(self, steps, env):
        outputs = {}
        for step in steps:
            proc = subprocess.run(step["cmd"], cwd=step["cwd"], env={**os.environ, **env}, capture_output=True, timeout=120)
            outputs[step["name"]] = (proc.returncode, proc.stdout.decode(), proc.stderr.decode())
        return outputs

    def test_sealed_module_with_canaries_honest_and_forging(self):
        self.assertIn(CANARY_FAIL_ID, SUPERVISOR_SRC)
        for scenario, pkg in (("honest", SNAPSHOT["pkg/__init__.py"]), ("forging", FORGING_PKG.encode())):
            with self.subTest(scenario=scenario):
                sealed_dir = self.tmp / f"sealed-{scenario}"
                (self.repo / "pkg" / "__init__.py").write_bytes(pkg)
                files = guest_files_for(str(sealed_dir), "test_sealed", SEALED, repo_dir=str(self.repo), extra_paths=[], canary=True)
                self._write(files)
                self.assertIn(f"{sealed_dir}/{JOB_FILE}", files)
                self.assertIn(f"{sealed_dir}/{CHILD_FILE}", files)
                nonce = new_nonce()
                steps = sealed_steps(sys.executable, str(self.repo), str(sealed_dir), nonce, [], {"PYTHONPATH": str(self.repo)},
                                     timeout=120, per_test_timeout=30)
                self.assertTrue(is_supervisor_step(steps[0]))
                out = self._run_steps(steps, {"PYTHONPATH": str(self.repo)})
                self.assertIn("SEALED-RESULT-WRITTEN", out["sealed"][1], out["sealed"])
                result = json.loads(out["sealed_result"][1])
                self.assertEqual(result["supervisor"], SUPERVISOR_VERSION)
                self.assertEqual(result["nonce"], nonce)
                self.assertEqual(sorted(result["expected_ids"]), sorted(static_test_ids(SEALED)))
                self.assertEqual(result["startup_hooks_before"], [])
                summary = summarize(result)
                binding = bind_verification(result, static_test_ids(SEALED), sha256_text(SEALED), nonce)
                outcomes = {c["id"].split(".")[-1]: (c["outcome"], c["exit_code"]) for c in result["canaries"]}
                if scenario == "honest":
                    self.assertEqual([t["outcome"] for t in result["tests"]], ["ok", "ok"])
                    self.assertTrue(result["canary_ok"], result["canaries"])
                    self.assertEqual(outcomes, {"test_must_pass": ("ok", 0), "test_must_fail": ("FAIL", 1)})
                    failed = [k for k, v in binding["checks"].items() if not v]
                    self.assertEqual(failed, [] if os.getuid() == 0 else ["verifier_isolation_active"], binding)
                    self.assertTrue(summary["all_passed"])
                else:
                    # every real test is reported as passing by the forgery, but the must-fail canary flips
                    self.assertEqual([t["outcome"] for t in result["tests"]], ["ok", "ok"])
                    self.assertFalse(result["canary_ok"], result["canaries"])
                    self.assertEqual(outcomes["test_must_fail"], ("ok", 0))
                    self.assertFalse(binding["checks"]["canary_must_fail_failed"])
                    self.assertTrue(any("canary flipped" in r for r in binding["reasons"]), binding)
                    self.assertIn("CANARY FLIPPED", summary["summary_line"])

    def test_repository_suite_bound_through_the_supervisor(self):
        suite_dir = self.tmp / "attest_suite"
        plan = static_repo_tests(SNAPSHOT, DISCOVER)
        modules = [{"name": m["name"], "path": f"{self.repo}/{m['rel']}", "sha256": m["sha256"], "ids": m["ids"]} for m in plan["modules"]]
        self._write(repo_suite_files(str(suite_dir), modules, str(self.repo), [], canary=True))
        nonce = new_nonce()
        steps = sealed_steps(sys.executable, str(self.repo), str(suite_dir), nonce, env={"PYTHONPATH": str(self.repo)},
                             timeout=120, per_test_timeout=30, step_prefix="existing")
        out = self._run_steps(steps, {"PYTHONPATH": str(self.repo)})
        result = json.loads(out["existing_result"][1])
        self.assertEqual([m["name"] for m in result["modules"]], ["tests.subpkg.test_c", "tests.test_a"])
        self.assertEqual([t["outcome"] for t in result["tests"]], ["ok", "ok", "ok"])
        self.assertTrue(result["canary_ok"])
        binding = bind_modules(result, modules, nonce)
        failed = [k for k, v in binding["checks"].items() if not v]
        self.assertEqual(failed, [] if os.getuid() == 0 else ["verifier_isolation_active"], binding)
        self.assertTrue(binding["checks"]["module_digests_unchanged"])
        self.assertTrue(binding["checks"]["static_ids_match_expected"])

    def test_startup_hook_on_import_path_is_reported(self):
        (self.repo / "sitecustomize.py").write_text("import unittest\n", encoding="utf-8")
        sealed_dir = self.tmp / "sealed-hook"
        self._write(guest_files_for(str(sealed_dir), "test_sealed", SEALED, repo_dir=str(self.repo), extra_paths=[], canary=True))
        nonce = new_nonce()
        steps = sealed_steps(sys.executable, str(self.repo), str(sealed_dir), nonce, [], {"PYTHONPATH": str(self.repo)}, timeout=120, per_test_timeout=30)
        out = self._run_steps(steps, {"PYTHONPATH": str(self.repo)})
        result = json.loads(out["sealed_result"][1])
        self.assertEqual(result["startup_hooks_before"], [str(self.repo / "sitecustomize.py")])
        binding = bind_verification(result, static_test_ids(SEALED), sha256_text(SEALED), nonce)
        self.assertFalse(binding["checks"]["no_startup_hooks_on_import_path"])
        self.assertTrue(any("start-up hook" in r for r in binding["reasons"]), binding)


class RunDirectories(unittest.TestCase):
    def test_same_second_runs_get_distinct_directories(self):
        from attest.core.pipeline import Pipeline
        from attest.core.task import TaskSpec
        root = Path(__file__).resolve().parent.parent
        task = TaskSpec.load(root / "examples" / "durationkit-task" / "task.json")
        out = Path(tempfile.mkdtemp(prefix="attest-dirs-"))

        class Stub:
            name = "stub"

            def describe(self):
                return {"provider": "stub", "executor": "stub"}

        from attest.ledger import Ledger
        a = Pipeline(task=task, provider=Stub(), executor=Stub(), ledger=Ledger(), out_dir=out)
        b = Pipeline(task=task, provider=Stub(), executor=Stub(), ledger=Ledger(), out_dir=out)
        self.assertNotEqual(a.out_dir, b.out_dir)
        self.assertTrue(a.out_dir.is_dir() and b.out_dir.is_dir())
        self.assertEqual(b.run_id, b.out_dir.name)
        with self.assertRaises(FileExistsError):
            Pipeline(task=task, provider=Stub(), executor=Stub(), ledger=Ledger(), out_dir=out, run_id=a.run_id)


if __name__ == "__main__":
    unittest.main()
