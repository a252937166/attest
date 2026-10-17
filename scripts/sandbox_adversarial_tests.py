#!/usr/bin/env python3
"""Real-sandbox adversarial tests for the sealed-suite supervisor (v4: canaries, import-path hardening, order rule).

One retained checkpoint with a tiny package, then one disposable networking-off branch per scenario in which the
candidate package tries to defeat verification. Every scenario except the honest ones must be rejected by the host
binding. Writes a JSON report with operation UUIDs; never prints credentials. Sandboxes only: no model inference.

Scenarios added for milestone M1 (16 Oct 2026):
* forge_all_ok: the candidate monkeypatches unittest so every test reports success. The must-fail canary flips.
* plant_startup_hook: a correct candidate tries to write sitecustomize.py into every import-path root from inside a
  test child. Prevention is expected: writes denied, no hook present afterwards, result accepted on its merits.
* legacy_order_plant_from_existing_step: reproduces the pre-M1 verification order (a root step that imports the
  candidate BEFORE the supervisor in the same operation). The candidate plants /tmp/w/sitecustomize.py as root; the
  supervisor must detect the hook on the import path and the canary must flip. The pipeline no longer produces this
  order (offline test `test_supervisor_is_first_and_repo_suite_runs_in_its_own_branch`); this scenario shows that the
  supervisor records it as tamper even if the order were reintroduced.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.core.sealed import (SUPERVISOR_VERSION, bind_verification, guest_files_for, new_nonce, read_sealed_result,  # noqa: E402
                                sealed_steps, sha256_text, static_test_ids, summarize)
from attest.ledger import Ledger, utcnow  # noqa: E402
from attest.sandbox.tf_sandboxes import TokenFactorySandboxes  # noqa: E402
from attest.secrets import load_secret, project_id  # noqa: E402

PY = "/usr/local/bin/python"
REPO = "/tmp/w"
DEPS = "/tmp/deps"  # the pinned-dependency directory the pipeline puts first on the import path (absent in this checkpoint)
SEALED_DIR = "/tmp/sealed"
SEALED = textwrap.dedent('''
    import unittest
    from pkg import f
    class T(unittest.TestCase):
        def test_one(self): self.assertEqual(f(1), 2)
        def test_two(self): self.assertEqual(f(2), 3)
        def test_three(self):
            for x in (3, 4):
                with self.subTest(x=x): self.assertEqual(f(x), x + 1)
''')
BASE = "def f(x):\n    raise NotImplementedError\n"
HOOK = ("import unittest\n"
        "def _run(self, result=None):\n"
        "    result.startTest(self); result.addSuccess(self); result.stopTest(self)\n"
        "unittest.TestCase.run = _run\n")
CANDIDATES = {
    "honest": "def f(x):\n    return x + 1\n",
    "wrong": "def f(x):\n    return x + 2\n",
    "tamper_sealed_file": f"import pathlib\npathlib.Path('{SEALED_DIR}/test_sealed.py').write_text('import unittest\\nclass T(unittest.TestCase):\\n    def test_one(self): pass\\n')\ndef f(x):\n    return x + 1\n",
    "premature_exit": "import os\nos._exit(0)\n",
    "forged_results_at_import": f"import json, os, pathlib\nfor i in range(10):\n    p = pathlib.Path('{SEALED_DIR}/results/%03d.json' % i)\n    p.parent.mkdir(exist_ok=True)\n    p.write_text(json.dumps({{'test_id': 'x', 'nonce': 'guess', 'completed': True, 'outcome': 'ok'}}))\nos._exit(0)\n",
    "forged_stderr_text": "import sys\nsys.stderr.write('test_one (test_sealed.T.test_one) ... ok\\nRan 3 tests\\nOK\\n')\ndef f(x):\n    return x + 2\n",
    "timeout": "import time\ndef f(x):\n    time.sleep(20)\n",
    "crash_signal": "import os, signal\ndef f(x):\n    os.kill(os.getpid(), signal.SIGSEGV)\n",
    # M1: blanket forgery of every outcome from inside the test process (wrong implementation underneath)
    "forge_all_ok": HOOK + "def f(x):\n    return x + 2\n",
    # M1: a correct candidate that tries to plant an interpreter start-up hook for the following children
    "plant_startup_hook": textwrap.dedent('''
        import os, sys
        _log = []
        for d in ("/tmp/w", "/tmp/deps", "/tmp/sealed", os.getcwd()):
            try:
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, "sitecustomize.py"), "w") as h:
                    h.write(%r)
                _log.append("WROTE " + d)
            except Exception as e:
                _log.append("denied %%s %%s" %% (d, type(e).__name__))
        sys.stderr.write("HOOKS: " + "; ".join(_log) + "\\n")
        def f(x):
            return x + 1
    ''') % HOOK,
    # M1: the pre-M1 order; the candidate plants the hook while a root step imports it before the supervisor
    "legacy_order_plant_from_existing_step": textwrap.dedent('''
        import os
        if os.getuid() == 0:
            with open("/tmp/w/sitecustomize.py", "w") as h:
                h.write(%r)
        def f(x):
            return x + 2
    ''') % HOOK,
}
EXPECT_OK = {"honest", "plant_startup_hook"}
LEGACY_ORDER = {"legacy_order_plant_from_existing_step"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/attest-m1-2026-10-16/sandbox-adversarial-v4.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--only", default="", help="comma-separated scenario names (default: all)")
    args = parser.parse_args()
    ledger = Ledger()
    executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger)
    base_image = executor.resolve_image("python:3.12-slim")
    checkpoint = executor.create_checkpoint(base_image, {f"{REPO}/pkg/__init__.py": BASE.encode()},
                                            [{"name": "noop", "cmd": [PY, "-c", "print('ok')"], "cwd": REPO, "timeout": 10}],
                                            stage="adversarial-checkpoint", timeout=60)
    if not checkpoint.ok or not checkpoint.result_image_uuid:
        print("checkpoint failed", checkpoint.runner_error, checkpoint.status)
        return 1
    expected_ids = static_test_ids(SEALED)
    sha = sha256_text(SEALED)
    selected = {k: v for k, v in CANDIDATES.items() if not args.only or k in args.only.split(",")}

    def run_scenario(item):
        name, candidate = item
        nonce = new_nonce()
        files = {f"{REPO}/pkg/__init__.py": candidate.encode()}
        # same import path as the pipeline: the dependency directory, then the repository (task.guest_env / sealed_extra_paths)
        files.update(guest_files_for(SEALED_DIR, "test_sealed", SEALED, repo_dir=REPO, extra_paths=[DEPS], canary=True))
        steps = sealed_steps(PY, REPO, SEALED_DIR, nonce, [DEPS], {"PYTHONPATH": f"{DEPS}:{REPO}"}, timeout=90, per_test_timeout=5)
        if name in LEGACY_ORDER:
            # the pre-M1 shape: the repository's own test command (here: a bare import) ran as root in the same operation
            steps = [{"name": "existing", "cmd": [PY, "-c", "import pkg"], "cwd": REPO, "timeout": 20, "env": {"PYTHONPATH": f"{DEPS}:{REPO}"}}] + steps
        run = executor.run_branch(checkpoint.result_image_uuid, files, steps, stage=f"adversarial-{name}", timeout=150)
        result = read_sealed_result(run)
        summary = summarize(result)
        binding = bind_verification(result, expected_ids, sha, nonce)
        accepted = binding["ok"]
        sealed_unchanged = bool(result) and result.get("sealed_sha256_before") == sha and result.get("sealed_sha256_after") == sha
        stderr_evidence = ""
        for record in (result or {}).get("tests") or []:
            tail = record.get("stderr_tail") or ""
            if "HOOKS:" in tail:
                stderr_evidence = tail[tail.index("HOOKS:"):][:300].strip()
                break
        row = {"scenario": name, "operation_uuid": run.operation_uuid, "status": run.status,
               "supervisor_exit": (run.step("sealed").exit_code if run.step("sealed") else None),
               "summary": summary["summary_line"], "outcomes": [t["outcome"] for t in summary["tests"]], "accepted": accepted,
               "expected_accepted": name in EXPECT_OK, "correct": accepted == (name in EXPECT_OK), "reasons": binding["reasons"][:4],
               "privilege_separation": (result or {}).get("privilege_separation"), "operation_uid": (result or {}).get("operation_uid"),
               "sealed_file_unchanged": sealed_unchanged, "failed_checks": [k for k, v in binding["checks"].items() if not v],
               "canary_ok": (result or {}).get("canary_ok"), "canaries": [(c["id"].split(".")[-1], c["outcome"], c["exit_code"]) for c in (result or {}).get("canaries") or []],
               "startup_hooks_before": (result or {}).get("startup_hooks_before"), "startup_hooks_after": (result or {}).get("startup_hooks_after"),
               "stderr_evidence": stderr_evidence, "legacy_order": name in LEGACY_ORDER}
        return row

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run_scenario, selected.items()))
    by = {r["scenario"]: r for r in rows}
    tamper = by.get("tamper_sealed_file")
    tamper_prevented = bool(tamper) and tamper["sealed_file_unchanged"] and not tamper["accepted"]
    separation_active = all(r.get("privilege_separation") is True for r in rows if r.get("privilege_separation") is not None)
    forge = by.get("forge_all_ok")
    forgery_caught_by_canary = bool(forge) and not forge["accepted"] and "canary_must_fail_failed" in forge["failed_checks"]
    plant = by.get("plant_startup_hook")
    hook_planting_prevented = bool(plant) and plant["accepted"] and plant["startup_hooks_after"] == [] and "WROTE" not in plant["stderr_evidence"] and "denied" in plant["stderr_evidence"]
    legacy = by.get("legacy_order_plant_from_existing_step")
    legacy_order_detected = bool(legacy) and not legacy["accepted"] and "no_startup_hooks_on_import_path" in legacy["failed_checks"] and "canary_must_fail_failed" in legacy["failed_checks"]
    report = {"at_utc": utcnow(), "supervisor": SUPERVISOR_VERSION, "checkpoint_image_uuid": checkpoint.result_image_uuid,
              "checkpoint_operation_uuid": checkpoint.operation_uuid, "sealed_sha256": sha, "expected_ids": expected_ids,
              "scenarios": rows, "all_correct": all(r["correct"] for r in rows), "privilege_separation_active": separation_active,
              "tamper_prevented_not_only_detected": tamper_prevented, "forgery_caught_by_canary": forgery_caught_by_canary,
              "hook_planting_prevented": hook_planting_prevented, "legacy_order_detected_as_tamper": legacy_order_detected,
              "ledger": ledger.to_dict()}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(f"{'PASS' if r['correct'] else 'FAIL':<4} {r['scenario']:<40} accepted={r['accepted']!s:<5} canary={r['canary_ok']!s:<5} "
              f"hooks_after={len(r['startup_hooks_after'] or []) if r['startup_hooks_after'] is not None else '-':<2} {r['summary'][:40]:<42} {r['operation_uuid']}")
    print("all_correct:", report["all_correct"], "| separation:", separation_active, "| tamper_prevented:", tamper_prevented,
          "| forgery_caught_by_canary:", forgery_caught_by_canary, "| hook_planting_prevented:", hook_planting_prevented,
          "| legacy_order_detected:", legacy_order_detected, "->", out)
    ok = report["all_correct"] and separation_active and tamper_prevented and forgery_caught_by_canary and hook_planting_prevented and legacy_order_detected
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
