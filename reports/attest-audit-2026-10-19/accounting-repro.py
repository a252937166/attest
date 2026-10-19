#!/usr/bin/env python3
"""Offline accounting audit reproductions for the 19 Oct 2026 working tree.

Only temporary directories and SQLite databases are changed. All provider calls are
stubbed; a socket tripwire rejects accidental networking. No credentials are read.
Prints observations, not invoices or evidence of actual provider charges.
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from attest.app.db import Store  # noqa: E402
from attest.ledger import JOURNAL_FILE, Ledger, read_journal  # noqa: E402
from attest.models.nebius_tokenfactory import NebiusTokenFactory  # noqa: E402
import run_evaluation as harness  # noqa: E402


SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}},
          "required": ["x"], "additionalProperties": False}
ANSWER = {"model": "offline-fake", "choices": [
    {"message": {"content": '{"x":1}'}, "finish_reason": "stop"}]}
TODAY = "2026-10-19T00:00:00"


def block_network(*args, **kwargs):
    raise AssertionError("network forbidden in the offline accounting audit")


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


def observe() -> dict:
    results = {}
    with tempfile.TemporaryDirectory(prefix="attest-accounting-audit-") as temporary:
        temp = Path(temporary)

        # AC-01: a recovered orphan is removed from the new Budget's starting
        # committed sum on the next resume, even though it remains in the report.
        runs = temp / "harness-runs"
        orphan = runs / "orphan"
        ledger = Ledger()
        ledger.attach_sink(orphan / JOURNAL_FILE)
        ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
        first = harness.interrupted_cells(runs, [], [])
        second = harness.interrupted_cells(runs, [], first)
        first_added = sum(i["cost_usd_committed"] for i in first if not i["counted_before"])
        second_added = sum(i["cost_usd_committed"] for i in second if not i["counted_before"])
        results["AC-01"] = {"first_resume_added_usd": first_added,
                            "second_resume_added_usd": second_added,
                            "interrupted_cost_still_reported_usd": second[0]["cost_usd_committed"],
                            "reproduced": first_added == 0.25 and second_added == 0}

        # AC-02: existence of a completed bundle is mistaken for ownership by a
        # persisted row. No row owns this directory at all.
        (orphan / "proof_bundle.json").write_text("{}", encoding="utf-8")
        recovered = harness.interrupted_cells(runs, [], [])
        results["AC-02"] = {"journal_committed_usd": read_journal(orphan / JOURNAL_FILE)["cost_usd_committed"],
                            "persisted_rows": 0, "recovered_items": len(recovered),
                            "reproduced": not recovered}

        # AC-03: the sink existed before the failure, so attach_sink succeeds.
        # A later failure is swallowed by _append and reserve still returns.
        sink = temp / "failed-write" / JOURNAL_FILE
        ledger = Ledger()
        ledger.attach_sink(sink)
        with mock.patch.object(Path, "open", side_effect=OSError("offline fake disk full")):
            reservation_id = ledger.reserve("nebius_tokenfactory", "seal", "seal", "m", 0.25)
        restored = read_journal(sink)
        results["AC-03"] = {"reserve_returned": reservation_id,
                            "in_memory_committed_usd": ledger.totals()["cost_usd_committed"],
                            "journal_recovered_usd": restored["cost_usd_committed"],
                            "reproduced": reservation_id is not None and restored["cost_usd_committed"] == 0}

        # AC-04: a generated HTTP 200 answer without metering information is
        # accepted and its nonzero reservation is settled to known zero.
        ledger = Ledger()
        provider = NebiusTokenFactory("offline-fake-key", ledger, usd_cap=0.02)
        with mock.patch("attest.models.nebius_tokenfactory.request_json", return_value=(200, ANSWER, {})) as request:
            for _ in range(3):
                provider.structured("seal", "prompt", SCHEMA, "seal")
        results["AC-04"] = {"stub_requests": request.call_count, "run_cap_usd": provider.usd_cap,
                            "reservation_each_usd": ledger.model_calls[0].reserved_usd,
                            "committed_usd": ledger.totals()["cost_usd_committed"],
                            "settlements": [call.settlement for call in ledger.model_calls],
                            "reproduced": request.call_count == 3 and ledger.totals()["cost_usd_committed"] == 0}

        # AC-05: startup import retains known spend but drops the committed
        # reservation attached to an uncertain request.
        run = temp / "imported"
        run.mkdir()
        bundle = {"run_id": "uncertain-import", "task": {"id": "t"},
                  "profile": {"provider": {"provider": "nebius_tokenfactory"}},
                  "started_at_utc": "2026-10-19T12:00:00+00:00", "verdict": {"verdict": "ERROR"},
                  "ledger": {"totals": {"cost_usd": None, "cost_usd_committed": 0.5}}}
        (run / "proof_bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
        store = Store(temp / "import.sqlite")
        store.import_run_dir(run)
        remaining = store.nebius_remaining(0.5, 0.5, TODAY)
        results["AC-05"] = {"bundle_committed_usd": 0.5,
                            "stored_committed_usd": store.get_run("uncertain-import")["cost_committed_usd"],
                            "daily_remaining_usd": remaining["remaining_usd"],
                            "fits_another_run": remaining["fits_another_run"],
                            "reproduced": remaining["remaining_usd"] == 0.5 and remaining["fits_another_run"]}

        # AC-06: a run that crosses UTC midnight counts while active, then falls
        # out of today's committed total because it was created yesterday.
        store = Store(temp / "midnight.sqlite")
        store.create_run(run_id="cross-midnight", task_id="t", task_title="T", provider="nebius",
                         profile_label="judge-demo", status="running", stage="work",
                         created_at="2026-10-18T23:59:59+00:00", started_at="2026-10-19T00:01:00+00:00")
        before = store.nebius_remaining(0.5, 0.5, TODAY)
        store.update_run("cross-midnight", status="finished", finished_at="2026-10-19T00:05:00+00:00",
                         cost_usd=0.5, cost_committed_usd=0.5)
        after = store.nebius_remaining(0.5, 0.5, TODAY)
        results["AC-06"] = {"remaining_before_finish_usd": before["remaining_usd"],
                            "remaining_after_finish_usd": after["remaining_usd"],
                            "today_committed_after_finish_usd": after["committed_usd"],
                            "reproduced": before["remaining_usd"] == 0 and after["remaining_usd"] == 0.5}

        # AC-07: fake complete cells exercise real schedule/resume logic. The
        # original schedule says Nebius while the resumed runtime uses Codex and
        # has no batch USD approval. No real provider is instantiated.
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
                    "uncertain": False, "revision_digest": digests["attest_revision"]["digest"],
                    "executed_provider": provider_name}

        args = argparse.Namespace(provider="nebius", tasks="durationkit-units-001", systems="baseline,attest", attempts=1,
                                  workers=1, usd_cap=0.5, approve_usd=1.0, max_calls=20, max_turns=4, out=str(out), label="offline",
                                  suite="examples/eval/SUITE.json", resume="", snapshot_root=str(ROOT), source_root=str(ROOT),
                                  register_only=False)
        with mock.patch.object(harness, "runtime_provenance", return_value=provenance), \
             mock.patch.object(harness, "build_provider", return_value=DescriptionOnly()), \
             mock.patch.object(harness, "codex_governor", return_value=None), \
             mock.patch.object(harness, "one_system", side_effect=fake_cell):
            quiet(harness.run_batch, args)
            record = json.loads((out / "evaluation.json").read_text())
            record["rows"] = record["rows"][:1]
            record["complete"] = False
            (out / "evaluation.json").write_text(json.dumps(record), encoding="utf-8")
            args.resume, args.provider, args.approve_usd = str(out), "codex", None
            quiet(harness.run_batch, args)
        record = json.loads((out / "evaluation.json").read_text())
        results["AC-07"] = {"schedule_provider": record["schedule"]["provider"],
                            "resumed_cell_provider": record["rows"][-1]["executed_provider"],
                            "resumed_budget_approval_usd": record["budget"]["approve_usd"],
                            "invalid_tasks": record["provenance_check"]["invalid_tasks"],
                            "reproduced": record["schedule"]["provider"] == "nebius" and
                            record["rows"][-1]["executed_provider"] == "codex" and
                            record["budget"]["approve_usd"] is None and not record["provenance_check"]["invalid_tasks"]}

        # Control: retention removes artifacts, not accounting rows or spend.
        store = Store(temp / "prune.sqlite")
        prune_root = temp / "prune-runs"
        for index, cost in enumerate((0.2, 0.3)):
            directory = prune_root / str(index)
            directory.mkdir(parents=True)
            (directory / "artifact.txt").write_text("offline fixture", encoding="utf-8")
            store.create_run(run_id=f"p{index}", task_id="t", task_title="T", provider="nebius",
                             profile_label="judge-demo", status="finished", verdict="NEEDS HUMAN", stage="finished",
                             created_at=f"2026-10-19T12:00:0{index}+00:00", out_dir=str(directory),
                             cost_usd=cost, cost_committed_usd=cost)
        before_prune = store.nebius_remaining(0.5, 1.0, TODAY)["committed_usd"]
        pruned = store.prune_runs(prune_root, keep=0, protect=())
        after_prune = store.nebius_remaining(0.5, 1.0, TODAY)["committed_usd"]
        controls = {"pruning_preserves_spend": {"pruned_runs": len(pruned),
                    "committed_before_usd": before_prune, "committed_after_usd": after_prune,
                    "passed": before_prune == after_prune == 0.5}}

    files = ["attest/ledger.py", "attest/models/nebius_tokenfactory.py", "attest/app/db.py",
             "attest/app/worker.py", "scripts/run_evaluation.py"]
    return {"scope": "offline fake responses and temporary data; no evidence of actual billed loss",
            "python": sys.version.split()[0], "source_sha256": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
            "findings": results, "controls": controls,
            "all_reproduced": all(r["reproduced"] for r in results.values())}


if __name__ == "__main__":
    with mock.patch.object(socket.socket, "connect", block_network), \
         mock.patch.object(socket, "create_connection", block_network):
        print(json.dumps(observe(), indent=2))
