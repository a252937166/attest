"""Application OOM drill (revision 8, 19 October 2026): the deployed release under the service's memory mechanism.

Runs in a temporary unit with the deployed release's interpreter and code (/opt/attest/app), a scratch store and no secrets, at a
reduced limit. First start: imports the console application (its start-up settles rows that a previous process left running),
records a run in flight the way the worker does (a running row of the Nemotron profile whose ledger journal holds an open USD
reservation and a Sandboxes operation accepted but not yet read; no request is sent anywhere), then allocates memory until the
kernel's memory-cgroup OOM killer ends the process. Second start (systemd's Restart=on-failure): imports the application again;
its start-up must settle the run as interrupted, keep the reservation committed and name the accepted operation. Every step is
logged durably; the second start exits 0. Usage: drill_app.py <state dir>"""
import json
import os
import secrets
import sys
import time
from pathlib import Path

STATE = Path(sys.argv[1])
os.environ.update({"ATTEST_DATA_DIR": str(STATE / "data"), "ATTEST_IMPORT_DIRS": str(STATE / "data" / "runs"),
                   "ATTEST_EXAMPLES_DIR": "/opt/attest/app/examples", "ATTEST_ADMIN_TOKEN": secrets.token_hex(12)})  # a throwaway value
sys.path.insert(0, "/opt/attest/app")
RUN = "oom-drill-run-001"
MARK = STATE / "started-once"


def log(message):
    with open(STATE / "drill.log", "a") as handle:
        handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} pid={os.getpid()} {message}\n")
        handle.flush()
        os.fsync(handle.fileno())


first = not MARK.exists()
from attest import __version__  # noqa: E402
from attest.app import server  # noqa: E402  (start-up: the store, the imports, reconcile_interrupted)
from attest.ledger import Ledger, SandboxOp, utcnow  # noqa: E402

if first:
    MARK.touch()
    log(f"first start: attest {__version__}; rows settled at start-up {len(server.RECONCILED)}; {open('/proc/self/cgroup').read().split(chr(10))[0]}")
    run_dir = STATE / "data" / "runs" / RUN
    run_dir.mkdir(parents=True, exist_ok=True)
    server.store.create_run(run_id=RUN, task_id="durationkit-units-001", task_title="memory drill (no request is sent)", provider="nebius",
                            profile_label="judge-demo", status="running", created_at=utcnow(), out_dir=str(run_dir), requester="drill")
    ledger = Ledger()
    ledger.attach_sink(run_dir / "ledger.jsonl")
    ledger.reserve("nebius_tokenfactory", "implement", "implement-1", "nvidia/nemotron-3-super-120b-a12b", 0.0175)
    op = SandboxOp(stage="verify", operation_uuid=None, image_uuid="drill-image", result_image_uuid=None, disposable=True,
                   networking_enabled=False, status=None, exit_code=None, timed_out=None, signal=None, duration_s=None, raw_cost_diag=None,
                   stdout_truncated=None, started_at_utc=utcnow())
    ledger.add_op(op)
    op.operation_uuid, op.status = "00000000-0000-0000-0000-00000000d311", "ACCEPTED"
    ledger.update_op(op)
    log("a run is in flight: its row is running, its journal holds an open $0.0175 reservation and one accepted operation; allocating")
    blocks = []
    while True:
        block = bytearray(8 << 20)
        for offset in range(0, len(block), 4096):
            block[offset] = 1
        blocks.append(block)
        rss = next(line.split()[1] for line in open("/proc/self/status") if line.startswith("VmRSS"))
        log(f"allocated {len(blocks) * 8} MiB; VmRSS {rss} kB")
else:
    log(f"second start after the previous process ended: attest {__version__}; rows settled at start-up: {json.dumps(server.RECONCILED)}")
    row = server.store.get_run(RUN) or {}
    log("the run now: " + json.dumps({k: row.get(k) for k in ("status", "stage", "error_code", "cost_committed_usd", "error")}))
    sys.exit(0)
