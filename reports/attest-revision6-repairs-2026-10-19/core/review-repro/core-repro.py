"""Bounded offline review only: no network/provider/Sandbox/production use."""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
ROOT = Path(__import__('os').environ.get('ATTEST_REPRO_ROOT') or OUT.parents[1])  # re-run copy (19 Oct 2026): this copy sits two levels deeper than the original, so the project root comes from the environment
sys.path.insert(0, str(ROOT))
from attest.core.check import check_bundle
from attest.core.manifest import build_manifest
from attest.core.pipeline import Pipeline, witness_constraint_problems
from attest.core.proof import render_markdown
from attest.core.task import TaskSpec
from attest.ledger import Ledger
from tests.test_verification import FakeExecutor, TASK

SOURCE = """from builtins import type as make_type
import sys
Z = make_type('Z', (str,), {'__len__': (0).__int__})
x = Z('a=b')
print('CONTRADICTION TC1: this value is a custom str subclass')
sys.exit(3)
"""


def main():
    namespace = {}
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(SOURCE, namespace)
        except SystemExit as error:
            exit_code = error.code
    p = Pipeline.__new__(Pipeline)
    p.task = TaskSpec.load(TASK)
    p.executor = FakeExecutor(Ledger())
    p.save = lambda *args: None
    p.log = lambda *args: None
    p.ask = lambda *args: SimpleNamespace(call=SimpleNamespace(requested_model="OFFLINE-FAKE"), json={
        "consistent": False, "notes": "offline mechanical-constraint review", "conflicts": [
            {"requirement_ids": ["TC1"], "summary": "offline fake claim", "witness": SOURCE}]})
    spec = {"restated_task": "offline review", "interface_contract": [], "acceptance_criteria": ["derived criterion"], "out_of_scope": []}
    audit = p.contract_audit(spec, {}, "offline-checkpoint")
    conflict = audit["conflicts"][0]
    bypass = {"source": SOURCE, "local_toy_exit": exit_code, "constraint_problems": witness_constraint_problems(SOURCE),
              "actual_type_is_str": type(namespace["x"]) is str, "isinstance_str": isinstance(namespace["x"], str), "len": len(namespace["x"]),
              "actual_audit": {k: conflict.get(k) for k in ("provenance", "witness_constrained", "demonstrated", "grounded", "status")},
              "execution_evidence": "FakeExecutor only; no model or real sandbox call. The small local class construction is auditor-authored."}
    src = next((ROOT / "reports/attest-revision5-repairs-2026-10-19/evaluation-codex/runs").glob("durationkit*"))
    positive = check_bundle(src)
    with tempfile.TemporaryDirectory(prefix="attest-r6-review-") as temp:
        dst = Path(temp) / "synthetic"
        shutil.copytree(src, dst)
        bundle = json.loads((dst / "proof_bundle.json").read_text())
        raw = json.loads((dst / "verify_raw.json").read_text())
        bundle["verification"].pop("existing")
        raw.pop("existing")
        (dst / "proof_bundle.json").write_text(json.dumps(bundle))
        (dst / "verify_raw.json").write_text(json.dumps(raw))
        (dst / "PROOF.md").write_text(render_markdown(bundle))
        (dst / "manifest.json").write_text(json.dumps(build_manifest(dst, bundle["run_id"])))
        stripped = check_bundle(dst)
    fields = ("ok", "fully_verified", "evidence_complete", "manifest_verified", "protocol", "errors", "warnings")
    results = {"r502_positive": {k: positive.get(k) for k in fields}, "r502_joint_deletion": {k: stripped.get(k) for k in fields},
               "r502_errors": [c for c in stripped["checks"] if c["ok"] is False], "r503_alias_bypass": bypass,
               "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                 for name in ("attest/core/pipeline.py", "attest/core/check.py")}}
    (OUT / "core-repro-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
