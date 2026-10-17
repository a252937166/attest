#!/usr/bin/env python3
"""Deterministic real-sandbox validation of arbitration: a correct candidate (f(x)=x+1) is falsified by a GENERATED
test that is simply wrong (asserts f(1)==3). The real arbiter must classify it a test_defect and return a corrected
module that PASSES on the candidate and still FAILS on the base. Exercises the real arbiter model and the real
re-run machinery. Writes a JSON report; no secrets printed."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.core.pipeline import Pipeline  # noqa: E402
from attest.core.task import GUEST_SEALED_DIR, TaskSpec  # noqa: E402
from attest.ledger import Ledger  # noqa: E402
from attest.models.codex_gateway import CodexGateway  # noqa: E402
from attest.sandbox.tf_sandboxes import TokenFactorySandboxes  # noqa: E402
from attest.secrets import load_secret, project_id  # noqa: E402

BASE = "def f(x):\n    raise NotImplementedError\n"
CANDIDATE = "def f(x):\n    return x + 1\n"
DEFECTIVE = textwrap.dedent('''
    import unittest
    from pkg import f
    class T(unittest.TestCase):
        def test_one(self): self.assertEqual(f(1), 2)
        def test_two(self): self.assertEqual(f(10), 11)
        def test_three(self): self.assertEqual(f(0), 1)
        def test_four(self): self.assertEqual(f(5), 6)
        def test_defect(self): self.assertEqual(f(1), 3)  # WRONG: contract says f(x) == x + 1, so f(1) == 2
''')
SPEC = {"restated_task": "Implement pkg.f(x) so that it returns x + 1 for any integer x.",
        "interface_contract": [{"name": "f", "signature": "f(x: int) -> int", "behavior": "return x + 1", "error_cases": []}],
        "acceptance_criteria": ["f(1) == 2", "f(0) == 1", "f(10) == 11", "f returns x + 1 for every integer x"],
        "out_of_scope": ["anything other than pkg.f"]}


def main() -> int:
    ledger = Ledger()
    executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)
    provider = CodexGateway(load_secret("CODEX_API_KEY"), ledger)
    tmp = Path(tempfile.mkdtemp(prefix="arb-check-"))
    repo = tmp / "repo" / "pkg"
    repo.mkdir(parents=True)
    (repo / "__init__.py").write_text(BASE, encoding="utf-8")
    (tmp / "task.json").write_text(json.dumps({
        "id": "arb-check", "title": "arb check", "statement": "f(x) = x + 1", "repo_dir": "repo",
        "allowed_write_globs": ["pkg/**"], "protected_globs": [], "import_hint": "from pkg import f",
        "test_command": ["/usr/local/bin/python", "-c", "print('noop')"]}), encoding="utf-8")
    task = TaskSpec.load(tmp / "task.json")
    pipeline = Pipeline(task=task, provider=provider, executor=executor, ledger=ledger, out_dir=tmp / "out",
                        profile_label="arb-check", arbitrate=True)
    image = executor.resolve_image("python:3.12-slim")
    checkpoint = executor.create_checkpoint(image, {"/tmp/w/pkg/__init__.py": BASE.encode()},
                                            [{"name": "noop", "cmd": ["/usr/local/bin/python", "-c", "print('ok')"], "cwd": "/tmp/w", "timeout": 10}],
                                            stage="arb-checkpoint", timeout=60)
    if not checkpoint.ok or not checkpoint.result_image_uuid:
        print("checkpoint failed:", checkpoint.runner_error)
        return 1
    changed = {"pkg/__init__.py": CANDIDATE.encode()}
    failing = [{"id": "test_sealed.T.test_defect", "outcome": "FAIL", "captured_tail": "AssertionError: 2 != 3"}]
    result = pipeline.arbitrate_module("sealed", "test_sealed", GUEST_SEALED_DIR, DEFECTIVE, failing, SPEC,
                                       "--- a/pkg/__init__.py\n+++ b/pkg/__init__.py\n+def f(x):\n+    return x + 1\n",
                                       checkpoint.result_image_uuid, changed, [], base_check=True)
    report = {"classifications": result["classifications"], "corrected_notes": result["corrected_notes"],
              "candidate_rerun": result["candidate_rerun"], "base_rerun": result["base_rerun"],
              "cleared_module": result["cleared_module"], "error": result["error"],
              "arbiter_classified_test_defect": all(c["classification"] == "test_defect" for c in result["classifications"]) and bool(result["classifications"])}
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/attest-hardening-2026-10-16/arbitration-sandbox-check.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    ok = report["arbiter_classified_test_defect"] and report["cleared_module"]
    print("\nARBITRATION REAL-SANDBOX CHECK:", "PASS" if ok else "FAIL", "->", out)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
