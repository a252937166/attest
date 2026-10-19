#!/usr/bin/env python3
"""Four threads, 120 reads per arm, synthetic SQLite database, no network.

Observed failures depend on scheduling and the Python/SQLite runtime. The retained
JSON records actual values; a zero count in one run is not evidence of safety.
"""
import concurrent.futures
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from unittest.mock import patch

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parent.parent
sys.path.insert(0, str(ROOT))
from attest.app.db import Store


def no_network(*args, **kwargs):
    raise AssertionError("Network is blocked by this offline audit")


out = {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version, "reads_per_arm": 120,
       "workers": 4, "network": "blocked"}
with patch.object(socket.socket, "connect", no_network), \
     patch.object(socket.socket, "connect_ex", no_network), \
     patch.object(socket, "create_connection", no_network), \
     tempfile.TemporaryDirectory(dir=AUDIT, prefix="sqlite-probe-") as tmp:
    store = Store(Path(tmp) / "store.db")

    def check(_):
        try:
            value = store.count_recent("synthetic-visitor", "2000-01-01")
            return {"value": value} if value != 0 else None
        except Exception as error:
            return {"error": type(error).__name__, "detail": str(error)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        out["unlocked_fetch_failures"] = [r for r in pool.map(check, range(120)) if r is not None]

    def serialized(_):
        try:
            with store._lock:
                value = store._conn.execute(
                    "SELECT COUNT(*) FROM runs WHERE requester = ? AND created_at >= ?",
                    ("synthetic-visitor", "2000-01-01"),
                ).fetchone()[0]
            return {"value": value} if value != 0 else None
        except Exception as error:
            return {"error": type(error).__name__, "detail": str(error)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        out["locked_fetch_failures"] = [r for r in pool.map(serialized, range(120)) if r is not None]
    store._conn.close()
(AUDIT / "sqlite-concurrency-probe.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in out.items()}, indent=2))
