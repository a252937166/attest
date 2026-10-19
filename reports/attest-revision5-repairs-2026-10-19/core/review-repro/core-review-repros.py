"""Two bounded, offline revision-5 review reproductions.

No provider/network/SSH/sandbox use. Product files and original audit artifacts
are read only. A synthetic bundle is modified only in a temporary directory;
the result JSON is written beside this audit script.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path(__import__('os').environ.get('ATTEST_REPRO_ROOT') or OUT.parents[1])  # re-run copy (19 Oct 2026): root taken from the environment because this copy sits two levels deeper than the original
sys.path.insert(0, str(ROOT))
from attest.core.check import check_bundle
from attest.core.manifest import build_manifest
from attest.core.proof import render_markdown


class ZeroLengthString(str):
    def __len__(self):
        return 0


def guarded_partition(line):
    """Counterexample to the witness's chosen output; not an all-subclass fix."""
    key, separator, value = str.partition(line, "=")
    if len(line) == 0:
        raise ValueError("preserve baseline for this subclass")
    key, value = key.strip(), value.strip()
    if not separator or not key:
        raise ValueError
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return key, value


def outcome(function, value):
    try:
        return {"kind": "return", "value": function(value)}
    except Exception as error:
        return {"kind": "exception", "type": type(error).__name__}


def summary(report):
    return {key: report.get(key) for key in ("ok", "fully_verified", "evidence_complete", "manifest_verified", "errors", "warnings", "protocol")}


def main():
    base = ROOT / "reports/attest-audit-repairs-2026-10-19"
    kv_run = base / "evaluation-codex-2/runs/kvparse-refactor-001-attest-a1-20261019T082112441408Z"
    task = json.loads((ROOT / "examples/eval/kvparse-refactor/task.json").read_text())
    frozen = json.loads((kv_run / "task.frozen.json").read_text())
    namespace = {}
    parser_path = ROOT / "examples/eval/kvparse-refactor/repo/kvparse/parser.py"
    exec(compile(parser_path.read_text(), str(parser_path), "exec"), namespace)
    inputs = [ZeroLengthString("a=b"), "a=b", " a = b ", "a==b", 'q = " spaced "', "novalue", " = v", ""]
    kv = {"frozen_statement_equals_current": frozen["statement"] == task["statement"],
          "frozen_statement": frozen["statement"],
          "cases": [{"input_type": type(value).__name__, "input": str(value),
                     "original": outcome(namespace["parse_line"], value),
                     "guarded_partition": outcome(guarded_partition, value)} for value in inputs],
          "proves_all_subclasses_satisfiable": False,
          "interpretation": "The witness's single chosen implementation is not forced by use of str.partition. Input-domain scope remains ambiguous."}
    src = base / "evaluation-codex-2/runs/balanced-brackets-attest-a1-20261019T082112441317Z"
    original = check_bundle(src)
    with tempfile.TemporaryDirectory(prefix="attest-review-only-") as temp:
        dst = Path(temp) / "synthetic-bundle"
        shutil.copytree(src, dst)
        bundle = json.loads((dst / "proof_bundle.json").read_text())
        raw = json.loads((dst / "verify_raw.json").read_text())
        before = {"existing_gate": bundle["gates"]["existing_suite"],
                  "existing_record_present": "existing" in bundle["verification"], "raw_existing_present": "existing" in raw}
        bundle["verification"].pop("existing")
        raw.pop("existing")
        (dst / "proof_bundle.json").write_text(json.dumps(bundle))
        (dst / "verify_raw.json").write_text(json.dumps(raw))
        (dst / "PROOF.md").write_text(render_markdown(bundle))
        (dst / "manifest.json").write_text(json.dumps(build_manifest(dst, bundle["run_id"])))
        changed = check_bundle(dst)
        completeness = {"source_run": str(src.relative_to(ROOT)), "positive_control": summary(original),
                        "before": before, "deleted_fields": ["proof_bundle.verification.existing", "verify_raw.existing"],
                        "retained_gate": bundle["gates"]["existing_suite"], "after": summary(changed),
                        "error_checks": [check for check in changed["checks"] if check["ok"] is False],
                        "regenerated_in_temporary_copy": ["proof_bundle.json", "verify_raw.json", "PROOF.md", "manifest.json"],
                        "original_run_modified": False,
                        "interpretation": "Current-protocol semantic completeness accepts a missing stage; this is not a hash forgery or proof of execution authenticity."}
    snapshots = [base / name / "snapshot/attest" for name in ("evaluation-codex", "evaluation-codex-2")]
    hashes = [{p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts} for folder in snapshots]
    changed_files = sorted(name for name in set(hashes[0]) | set(hashes[1]) if hashes[0].get(name) != hashes[1].get(name))
    results = {"kvparse_witness_counterexample": kv, "core06_missing_existing_stage": completeness,
               "batch_package_snapshot_difference": changed_files,
               "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                 for name in ("attest/core/check.py", "attest/core/pipeline.py", "attest/core/sealed.py", "attest/core/manifest.py", "attest/core/verdict.py")}}
    (OUT / "core-review-repro-results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"kvparse_cases": len(kv["cases"]), "frozen_statement_equals_current": kv["frozen_statement_equals_current"],
                      "core06_before": completeness["positive_control"], "core06_after": completeness["after"],
                      "batch_package_snapshot_difference": changed_files}, indent=2))


if __name__ == "__main__":
    main()
