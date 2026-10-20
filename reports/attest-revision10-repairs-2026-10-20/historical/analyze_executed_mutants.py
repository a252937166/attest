#!/usr/bin/env python3
"""Offline analysis of the operations the two uncertain mutant spawns of 17 Oct turned out to have created (revision 10, item 5). No
request is made: it reads the operation records retrieved by reconcile_historical.py and the run directories of the original runs.

For each it establishes (1) that the operation ran that run's mutant: the job the operation records (`metadata.stdin`, the gzip-compressed
JSON the client sent) wrote exactly the mutant source the run kept (`mutants_<id>.py`) and the run's sealed test module (by digest);
(2) that the nonce the job carried equals the nonce in the supervisor result; and (3) the mutant's status under the pipeline's own rule
(`bind_verification` + `classify_mutant_run`, the functions `attest check` uses), then the mutation score the run would have recorded
had the answer arrived."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from attest.core.pipeline import GUEST_REPO, classify_mutant_run  # noqa: E402
from attest.core.sealed import bind_verification  # noqa: E402

HERE = Path(__file__).resolve().parent
BATCH = ROOT / "reports/attest-reliability-2026-10-17/evaluation-paced-codex/runs"
CASES = (("balanced-brackets-attest-a1-20261017T121900586528Z", "m01-2f645511c4", "01a149d2-b1df-75ba-8f8e-8d5e25a6c0b6"),
         ("semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z", "m08-64e9d487f1", "01a14a0a-3364-7402-aa67-e3e5818d7df1"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def analyze(run_id: str, mutant_id: str, operation_uuid: str) -> dict:
    run_dir = BATCH / run_id
    record = json.loads((HERE / f"operation-{operation_uuid}.json").read_text(encoding="utf-8"))
    bundle = json.loads((run_dir / "proof_bundle.json").read_text(encoding="utf-8"))
    meta = record["metadata"]
    stdin = meta.get("stdin") or {}
    raw = base64.b64decode(stdin["value"]) if stdin.get("encoding") == "base64" else stdin["value"].encode()
    job = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
    written = {path: base64.b64decode(data) for path, data in job["write"].items()}
    mutant_record = next(m for m in bundle["breaker"]["mutation"]["mutants"] if m["id"] == mutant_id)
    kept_mutant = (run_dir / f"mutants_{mutant_id}.py").read_bytes()
    mutant_path = f"{GUEST_REPO}/{mutant_record['path']}" if mutant_record.get("path") else None
    sealed_sha = bundle["sealed_tests"]["sha256"]
    sealed_written = [p for p, d in written.items() if sha(d) == sealed_sha]
    patch_paths = sorted(bundle["candidate"]["changed_paths"])
    # the supervisor result is printed by the sealed_result step of the guest report
    out = meta["result"]["stdout"]
    text = base64.b64decode(out["value"]).decode("utf-8", "replace") if out.get("encoding") == "base64" else out["value"]
    begin, end = text.find("ATTEST-RESULT-BEGIN"), text.rfind("ATTEST-RESULT-END")
    report = json.loads(text[begin + len("ATTEST-RESULT-BEGIN"):end].strip())
    step = next(s for s in report["steps"] if s.get("name") == "sealed_result")
    result = json.loads(step["stdout"])
    job_text = json.dumps(job["steps"])
    expected_ids = list(bundle["sealed_tests"]["expected_ids"])
    binding = bind_verification(result, expected_ids, sealed_sha, result.get("nonce"), canary=False)
    status, evidence, killed_by = classify_mutant_run(result, binding, expected_ids)
    mutation = bundle["breaker"]["mutation"]
    killed = mutation["killed"] + (1 if status == "killed" else 0)
    evaluated = mutation["evaluated"] + (1 if status in ("killed", "survived") else 0)
    summary = {
        "operation": {k: record.get(k) for k in ("uuid", "status", "created_at", "duration", "image_uuid", "consumed_cpu")},
        "run_id": run_id, "mutant": mutant_id, "recorded_status": mutant_record.get("status"), "verdict": bundle["verdict"]["verdict"],
        "spawn_sent_at_utc": next(op["started_at_utc"] for op in bundle["ledger"]["sandbox_ops"] if op["stage"] == f"mutant-{mutant_id}"),
        "run_finished_at_utc": bundle["finished_at_utc"],
        "same_job": {
            "mutant_file": mutant_path, "mutant_source_equal": bool(mutant_path) and written.get(mutant_path) == kept_mutant,
            "kept_mutant_sha256": sha(kept_mutant), "written_mutant_sha256": sha(written[mutant_path]) if mutant_path in written else None,
            "sealed_module_written": sealed_written, "sealed_sha256": sealed_sha,
            "candidate_paths_written": sorted(p[len(GUEST_REPO) + 1:] for p in written if p.startswith(GUEST_REPO + "/") and p != mutant_path),
            "candidate_changed_paths": patch_paths,
            "nonce_in_result": result.get("nonce"), "nonce_in_job_steps": bool(result.get("nonce")) and result["nonce"] in job_text,
        },
        "supervisor": result.get("supervisor"), "completed": result.get("completed"),
        "classification": {"status": status, "evidence": evidence, "killed_by": killed_by, "binding_ok": binding.get("ok")},
        "mutation_score": {"recorded": {"killed": mutation["killed"], "evaluated": mutation["evaluated"], "unknown": mutation["unknown"],
                                        "score": mutation["score"], "threshold": mutation["threshold"]},
                           "with_the_reconciled_mutant": {"killed": killed, "evaluated": evaluated, "unknown": mutation["unknown"] - (1 if status in ("killed", "survived") else 0),
                                                          "score": round(killed / evaluated, 4) if evaluated else None, "threshold": mutation["threshold"]}},
    }
    return summary


def main() -> int:
    results = [analyze(*case) for case in CASES]
    (HERE / "executed-mutants-analysis.json").write_text(json.dumps({"note": __doc__.split("\n\n")[0], "cases": results}, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(json.dumps({k: r[k] for k in ("run_id", "mutant", "operation", "spawn_sent_at_utc", "run_finished_at_utc")}, indent=1))
        print(json.dumps({"same_job": {k: r["same_job"][k] for k in ("mutant_source_equal", "sealed_module_written", "nonce_in_job_steps")},
                          "classification": {k: r["classification"][k] for k in ("status", "evidence")}, "mutation_score": r["mutation_score"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
