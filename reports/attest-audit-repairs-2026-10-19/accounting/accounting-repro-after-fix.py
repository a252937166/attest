#!/usr/bin/env python3
"""The 19 Oct 2026 accounting reproductions (AC-01, AC-02, AC-03, AC-04, AC-07) re-run against the repaired code.

The auditor's script, reports/attest-audit-2026-10-19/accounting-repro.py, is kept unchanged. It asserts the FAULTY behaviour and
cannot run to completion against the repaired code: its AC-03 block calls Ledger.reserve under an injected disk failure, which now
raises LedgerError, and its AC-04 block sends three requests of which the second is now refused with ModelError. This copy makes
the same observations with the same fixtures, catches the repaired refusals where they occur and reports them, so the `reproduced`
flag of every finding in this change set can be printed (all are expected to be false). AC-05 and AC-06 (console store and worker)
belong to another change set and are not observed here.

Same safeguards as the original: temporary directories only, fake responses, a socket tripwire, no credentials, no network. The
output describes behaviour against fakes; it is not evidence of any actual provider charge.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import socket
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from attest.ledger import JOURNAL_FILE, Ledger, LedgerError, read_journal  # noqa: E402
from attest.models.base import ModelError  # noqa: E402
from attest.models.nebius_tokenfactory import NebiusTokenFactory  # noqa: E402
import run_evaluation as harness  # noqa: E402


SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}},
          "required": ["x"], "additionalProperties": False}
ANSWER = {"model": "offline-fake", "choices": [
    {"message": {"content": '{"x":1}'}, "finish_reason": "stop"}]}


def block_network(*args, **kwargs):
    raise AssertionError("network forbidden in the offline accounting audit")


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return function(*args, **kwargs)


def observe() -> dict:
    results = {}
    with tempfile.TemporaryDirectory(prefix="attest-accounting-repair-") as temporary:
        temp = Path(temporary)

        # AC-01: the same orphan on three process starts; the committed figure must enter every start's total.
        runs = temp / "harness-runs"
        orphan = runs / "orphan"
        ledger = Ledger()
        ledger.attach_sink(orphan / JOURNAL_FILE)
        ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
        first = harness.interrupted_cells(runs, [], [])
        second = harness.interrupted_cells(runs, [], first)
        third = harness.interrupted_cells(runs, [], second)
        counted = [sum(i["cost_usd_committed"] for i in listing if i.get("included_in_batch_total")) for listing in (first, second, third)]
        results["AC-01"] = {"counted_usd_on_three_process_starts": counted, "entries_each_time": [len(first), len(second), len(third)],
                            "interrupted_cost_reported_usd": third[0]["cost_usd_committed"],
                            "first_listed_at_utc_preserved": first[0]["first_listed_at_utc"] == third[0]["first_listed_at_utc"],
                            "reproduced": counted != [0.25, 0.25, 0.25]}

        # AC-02: a bundle appears in the unowned directory; it must now be recovered (from its journal: no ledger.json here).
        (orphan / "proof_bundle.json").write_text("{}", encoding="utf-8")
        recovered = harness.interrupted_cells(runs, [], [])
        results["AC-02"] = {"journal_committed_usd": read_journal(orphan / JOURNAL_FILE)["cost_usd_committed"], "persisted_rows": 0,
                            "recovered_items": len(recovered),
                            "recovered": [{k: i.get(k) for k in ("run_id", "kind", "source", "cost_usd_committed", "included_in_batch_total")} for i in recovered],
                            "reproduced": not recovered or recovered[0]["cost_usd_committed"] != 0.25}

        # AC-03: the auditor's injection (Path.open fails after a successful attach_sink). reserve must now raise and record nothing.
        sink = temp / "failed-write" / JOURNAL_FILE
        ledger = Ledger()
        ledger.attach_sink(sink)
        with mock.patch.object(Path, "open", side_effect=OSError("offline fake disk full")):
            try:
                reservation_id = ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
                outcome = f"reserve returned {reservation_id}"
            except LedgerError as error:
                reservation_id = None
                outcome = f"LedgerError: {str(error)[:140]}"
        restored = read_journal(sink)
        # and through the provider, with the HTTP stub watching: nothing may be dispatched
        provider_ledger = Ledger()
        provider_ledger.attach_sink(temp / "failed-write-provider" / JOURNAL_FILE)
        provider = NebiusTokenFactory("offline-fake-key", provider_ledger, usd_cap=0.5)
        with mock.patch("attest.ledger._open_journal", side_effect=OSError("offline fake disk full")), \
             mock.patch("attest.models.nebius_tokenfactory.request_json", return_value=(200, ANSWER, {})) as request:
            try:
                provider.structured("seal", "prompt", SCHEMA, "seal")
                provider_outcome = "answer returned"
            except ModelError as error:
                provider_outcome = f"ModelError(uncertain={error.uncertain}): {str(error)[:140]}"
        results["AC-03"] = {"reserve_outcome": outcome, "in_memory_committed_usd": ledger.totals()["cost_usd_committed"],
                            "journal_recovered_usd": restored["cost_usd_committed"], "provider_outcome": provider_outcome,
                            "stub_requests_after_failed_reservation": request.call_count, "provider_halted": bool(provider.halted),
                            "reproduced": reservation_id is not None and restored["cost_usd_committed"] == 0}

        # AC-04: three fake HTTP 200 answers without usage under a $0.02 per-run cap. A journal is attached because a bare ledger is
        # now refused outright (AC-03); the observation is about the metering, not the journal.
        ledger = Ledger()
        ledger.attach_sink(temp / "metering" / JOURNAL_FILE)
        provider = NebiusTokenFactory("offline-fake-key", ledger, usd_cap=0.02)
        accepted, refused = 0, []
        with mock.patch("attest.models.nebius_tokenfactory.request_json", return_value=(200, ANSWER, {})) as request:
            for _ in range(3):
                try:
                    provider.structured("seal", "prompt", SCHEMA, "seal")
                    accepted += 1
                except ModelError as error:
                    refused.append(str(error)[:140])
        results["AC-04"] = {"stub_requests": request.call_count, "answers_accepted": accepted, "refusals": refused, "run_cap_usd": provider.usd_cap,
                            "reservation_each_usd": ledger.model_calls[0].reserved_usd,
                            "committed_usd": ledger.totals()["cost_usd_committed"],
                            "settlements": [call.settlement for call in ledger.model_calls],
                            "cost_notes": [call.cost_note[:120] for call in ledger.model_calls],
                            "reproduced": request.call_count == 3 and ledger.totals()["cost_usd_committed"] == 0}

        # AC-07: the auditor's fake batch, registered as Nebius, resumed with the Codex default and no approval. The resume must now
        # be refused (exit code 2) before any runtime is constructed, and the report must still describe the Nebius execution.
        out = temp / "resume-config"
        digests = harness.snapshot_digests(ROOT)
        provenance = {"fresh_process": False, "attest_revision": digests["attest_revision"],
                      "eval_script_sha256": digests["eval_script_sha256"], "examples_digest": digests["examples"],
                      "guest_programs": {}, "note": "offline audit fake runtime"}
        executed = []

        class DescriptionOnly:
            def describe(self):
                return {"provider": "offline-fake"}

        def fake_cell(cell, provider_name, usd_cap, max_calls, out_dir, max_turns, task_root):
            executed.append(provider_name)
            return {**cell, "status": "completed", "verdict": "BASELINE" if cell["system"] == "baseline" else "VERIFIED",
                    "accepted": True, "finished": True, "changed_paths": 1, "held_out_correct": True,
                    "cost_usd": 0.01, "cost_committed_usd": 0.01, "wall_s": 0.1, "infra_error": False,
                    "uncertain": False, "revision_digest": digests["attest_revision"]["digest"]}

        args = argparse.Namespace(provider="nebius", tasks="durationkit-units-001", systems="baseline,attest", attempts=1,
                                  workers=1, usd_cap=0.5, approve_usd=1.0, max_calls=None, max_turns=4, out=str(out), label="offline",
                                  suite="examples/eval/SUITE.json", resume="", snapshot_root=str(ROOT), source_root=str(ROOT),
                                  register_only=False)
        constructed = []
        with mock.patch.object(harness, "runtime_provenance", side_effect=lambda *a, **k: constructed.append("runtime_provenance") or provenance), \
             mock.patch.object(harness, "build_provider", side_effect=lambda *a, **k: constructed.append("build_provider") or DescriptionOnly()), \
             mock.patch.object(harness, "codex_governor", side_effect=lambda: constructed.append("codex_governor")), \
             mock.patch.object(harness, "one_system", side_effect=fake_cell):
            quiet(harness.run_batch, args)
            record = json.loads((out / "evaluation.json").read_text())
            record["rows"] = record["rows"][:1]
            record["complete"] = False
            (out / "evaluation.json").write_text(json.dumps(record), encoding="utf-8")
            constructed.clear()
            args.resume, args.provider, args.approve_usd = str(out), "codex", None
            resume_exit = quiet(harness.run_batch, args)
            constructed_during_conflict = list(constructed)  # expected empty: refused before any runtime construction
            # and the same resume with nothing given on the command line keeps the registration
            args.provider = args.usd_cap = args.max_calls = args.max_turns = args.workers = args.attempts = args.systems = None
            bare_exit = quiet(harness.run_batch, args)
        record = json.loads((out / "evaluation.json").read_text())
        results["AC-07"] = {"schedule_provider": record["schedule"]["provider"], "schedule_max_calls_per_run": record["schedule"]["max_calls_per_run"],
                            "conflicting_resume_exit_code": resume_exit, "runtime_constructed_during_conflicting_resume": constructed_during_conflict,
                            "bare_resume_exit_code": bare_exit, "providers_executed": executed,
                            "resumed_cell_provider": record["rows"][-1]["executed_provider"],
                            "resumed_budget_approval_usd": record["budget"]["approve_usd"],
                            "invalid_tasks": record["provenance_check"]["invalid_tasks"],
                            "reproduced": record["schedule"]["provider"] == "nebius" and
                            record["rows"][-1]["executed_provider"] == "codex" and
                            record["budget"]["approve_usd"] is None and not record["provenance_check"]["invalid_tasks"]}

    files = ["attest/ledger.py", "attest/models/base.py", "attest/models/nebius_tokenfactory.py", "scripts/run_evaluation.py",
             "scripts/render_evaluation.py"]
    return {"scope": "offline fake responses and temporary data; no evidence of actual billed loss; AC-05 and AC-06 are another change set",
            "python": sys.version.split()[0], "source_sha256": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
            "findings": results, "any_reproduced": any(r["reproduced"] for r in results.values())}


if __name__ == "__main__":
    with mock.patch.object(socket.socket, "connect", block_network), \
         mock.patch.object(socket, "create_connection", block_network):
        print(json.dumps(observe(), indent=2))
