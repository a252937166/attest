#!/usr/bin/env python3
"""Bounded offline reproduction: a partial settlement poisons the next reserve line.

Only a temporary journal is written. No credential is read and no provider or
HTTP stub is called. Socket operations are blocked as an additional guard.
"""

import hashlib
import json
import socket
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from attest.ledger import JOURNAL_FILE, Ledger, ModelCall, read_journal, utcnow  # noqa: E402


def network_forbidden(*args, **kwargs):
    raise AssertionError("network is forbidden in this offline reproduction")


def reproduce():
    with tempfile.TemporaryDirectory(prefix="attest-r5-partial-settlement-") as directory:
        path = Path(directory) / JOURNAL_FILE
        ledger = Ledger()
        ledger.attach_sink(path)
        first_id = ledger.reserve("nebius_tokenfactory", "seal", "first", "offline-model", 0.02)
        call = ModelCall(provider="nebius_tokenfactory", role="seal", stage="first", requested_model="offline-model",
                         requested_effort=None, returned_model="offline-model", returned_effort=None,
                         started_at_utc=utcnow(), elapsed_ms=1, gateway_duration_ms=None, prompt_chars=1,
                         tokens_in=1, tokens_out=1, tokens_cached=0, usage_raw={}, cost_usd=0.01,
                         cost_note="offline synthetic fixture", ok=True, reserved_usd=0.02)

        def partially_write_settlement(journal_path, lines):
            with Path(journal_path).open("a", encoding="utf-8") as handle:
                handle.write('{"event":"call","reservation_id":"r1"')
            raise OSError("offline injected partial settlement write")

        with mock.patch("attest.ledger._write_durably", side_effect=partially_write_settlement):
            ledger.add_call(call, first_id)

        # The fake disk is healthy again. The real durable append path is used.
        second_id = ledger.reserve("nebius_tokenfactory", "seal", "second", "offline-model", 0.05)
        restored = read_journal(path)
        return {"scope": "synthetic ledger only; no HTTP stub invocation or actual dispatch",
                "http_stub_calls": 0,
                "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
                    "attest/ledger.py", "attest/models/nebius_tokenfactory.py")},
                "first_reservation_usd": 0.02, "first_known_cost_usd": 0.01,
                "second_reservation_usd": 0.05, "second_reservation_returned_id": second_id,
                "in_memory_committed_usd": ledger.totals()["cost_usd_committed"],
                "journal_recovered_committed_usd": restored["cost_usd_committed"],
                "journal_recovered_open_reserved_usd": restored["open_reserved_usd"],
                "journal_unparsable_lines": restored["unparsable_lines"],
                "journal_failure_count": len(ledger.journal_failures),
                "dispatch_boundary": "reserve returned r2; the provider dispatch path proceeds after a successful reserve",
                "reproduced": second_id == "r2" and ledger.totals()["cost_usd_committed"] == 0.06 and
                restored["cost_usd_committed"] == 0.02 and restored["unparsable_lines"] == 1}


if __name__ == "__main__":
    with mock.patch.object(socket.socket, "connect", network_forbidden), \
         mock.patch.object(socket, "create_connection", network_forbidden):
        print(json.dumps(reproduce(), indent=2))
