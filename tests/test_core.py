"""Harness tests: offline checks for the parser, workspace policy, task freezing and schemas."""

import json
import unittest
from pathlib import Path

from attest.core.prompts import ACTION_SCHEMA, DRIFT_SCHEMA, SEAL_SCHEMA, SPEC_SCHEMA
from attest.core.sealed import static_test_ids
from attest.core.task import TaskSpec
from attest.core.testparse import parse_unittest
from attest.core.workspace import PolicyViolation, Workspace, snapshot_repo
from attest.models.base import validate_json

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "examples" / "durationkit-task" / "task.json"


class ParseUnittestOutput(unittest.TestCase):
    def test_mixed_outcomes(self):
        stderr = ("test_plain (test_sealed.T.test_plain) ... ok\n"
                  "test_units (test_sealed.T.test_units) ... FAIL\n"
                  "test_err (test_sealed.T.test_err) ... ERROR\n\n"
                  "Ran 3 tests in 0.001s\n\nFAILED (failures=1, errors=1)\n")
        parsed = parse_unittest("", stderr, 1)
        self.assertEqual((parsed["ran"], parsed["passed"], parsed["failing"]), (3, 1, 2))
        self.assertFalse(parsed["all_passed"])

    def test_docstring_on_next_line(self):
        stderr = "test_a (m.T.test_a)\nChecks something ... ok\n\nRan 1 test in 0.000s\n\nOK\n"
        parsed = parse_unittest("", stderr, 0)
        self.assertTrue(parsed["all_passed"])
        self.assertEqual(parsed["tests"][0]["outcome"], "ok")

    def test_module_error(self):
        parsed = parse_unittest("", "Traceback\nModuleNotFoundError: No module named 'x'\n", 1)
        self.assertTrue(parsed["module_error"])
        self.assertFalse(parsed["all_passed"])


class WorkspacePolicy(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace({"pkg/a.py": b"x", "tests/test_a.py": b"t", "README.md": b"r"}, ["pkg/**"], ["tests/**", "README.md"])

    def test_rejects_protected_and_outside_paths(self):
        for bad in ["tests/test_a.py", "README.md", "../x.py", "/tmp/x", "other/x.py", "pkg/../tests/t.py"]:
            with self.subTest(path=bad), self.assertRaises(PolicyViolation):
                self.ws.write(bad, "z")

    def test_replace_in_file_requires_unique_snippet(self):
        self.ws.files["pkg/a.py"] = b"def f():\n    return 1\n\ndef g():\n    return 1\n"
        with self.assertRaises(PolicyViolation):
            self.ws.replace("pkg/a.py", "    return 1\n", "    return 2\n")  # ambiguous
        with self.assertRaises(PolicyViolation):
            self.ws.replace("pkg/a.py", "missing", "x")
        self.ws.replace("pkg/a.py", "def g():\n    return 1\n", "def g():\n    return 2\n")
        self.assertIn(b"return 2", self.ws.files["pkg/a.py"])
        with self.assertRaises(PolicyViolation):
            self.ws.replace("tests/test_a.py", "t", "u")

    def test_ranged_read(self):
        self.ws.files["pkg/a.py"] = b"l1\nl2\nl3\nl4\n"
        self.assertTrue(self.ws.read("pkg/a.py", start_line=2, end_line=3).startswith("[lines 2-3 of 4]\nl2\nl3\n"))
        self.assertTrue(self.ws.read("pkg/a.py").startswith("[4 lines]\n"))

    def test_undo_reverts_last_edit(self):
        self.ws.write("pkg/a.py", "v1")
        self.ws.write("pkg/a.py", "v2")
        self.ws.write("pkg/new.py", "created")
        self.assertEqual(self.ws.undo(), "pkg/new.py")           # created file is removed by undo
        self.assertNotIn("pkg/new.py", self.ws.files)
        self.assertEqual(self.ws.undo(), "pkg/a.py")             # revert v2 -> v1
        self.assertEqual(self.ws.files["pkg/a.py"], b"v1")
        self.ws.undo()                                           # revert v1 -> original
        self.assertEqual(self.ws.files["pkg/a.py"], b"x")
        self.assertIsNone(self.ws.undo())                        # nothing left to undo

    def test_changed_and_diff(self):
        self.ws.write("pkg/a.py", "y")
        self.ws.write("pkg/new.py", "n")
        self.assertEqual(set(self.ws.changed()), {"pkg/a.py", "pkg/new.py"})
        self.assertTrue(self.ws.scope_report()["ok"])
        diff = self.ws.unified_diff()
        self.assertIn("--- a/pkg/a.py", diff)
        self.assertIn("+++ b/pkg/new.py", diff)


class TaskFreezing(unittest.TestCase):
    def test_frozen_digest_is_stable(self):
        task = TaskSpec.load(TASK)
        snapshot = snapshot_repo(task.repo_dir)
        first, second = task.frozen(snapshot), task.frozen(snapshot)
        self.assertEqual(first["spec_sha256"], second["spec_sha256"])
        self.assertIn("durationkit/parse.py", first["repo_files_sha256"])


class Schemas(unittest.TestCase):
    def test_action_schema_accepts_and_rejects(self):
        good = {"action": "finish", "path": None, "content": None, "find": None, "replace": None, "start_line": None,
                "end_line": None, "code": None, "reason": "done", "summary": "ok"}
        self.assertIsNone(validate_json(good, ACTION_SCHEMA))
        self.assertIsNotNone(validate_json({"action": "fly"}, ACTION_SCHEMA))

    def test_static_test_discovery(self):
        src = "import unittest\nclass A(unittest.TestCase):\n    def test_x(self): pass\n    def helper(self): pass\nclass NotATest:\n    def test_y(self): pass\nclass B(A):\n    def test_z(self): pass\n"
        self.assertEqual(static_test_ids(src), ["test_sealed.A.test_x"])  # subclass-of-subclass is not discovered statically

    def test_schemas_are_strict_objects(self):
        for schema in (SPEC_SCHEMA, SEAL_SCHEMA, ACTION_SCHEMA, DRIFT_SCHEMA):
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["required"]), set(schema["properties"]))
            json.dumps(schema)


if __name__ == "__main__":
    unittest.main()
