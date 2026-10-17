#!/usr/bin/env python3
"""Probe Nebius Sandboxes privilege model: can an operation run as uid 0, drop to other uids per child process,
and do file permissions, kill() and ptrace boundaries hold between those uids? Writes a JSON report; no secrets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.ledger import Ledger, utcnow  # noqa: E402
from attest.sandbox.tf_sandboxes import TokenFactorySandboxes  # noqa: E402
from attest.secrets import load_secret, project_id  # noqa: E402

PROBE = r'''
import json, os, subprocess, sys, time
out = {"uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid()}
def read(path):
    try:
        return open(path).read().strip()[:300]
    except Exception as e:
        return "ERR %s" % type(e).__name__
out["ptrace_scope"] = read("/proc/sys/kernel/yama/ptrace_scope")
out["uid_map"] = read("/proc/self/uid_map")
out["status_caps"] = [l for l in read("/proc/self/status").splitlines()] if False else read("/proc/self/status").count("Cap")
caps = {}
for line in open("/proc/self/status"):
    if line.startswith("Cap"):
        k, v = line.split(":", 1)
        caps[k] = v.strip()
out["caps"] = caps
out["kernel"] = read("/proc/version")
out["mounts_tmp"] = [l for l in read("/proc/mounts").splitlines() if " /tmp " in l or " / " in l][:4] if False else None
try:
    out["mounts"] = [l.split()[1] + " " + l.split()[2] + " " + l.split()[3][:60] for l in open("/proc/mounts")][:12]
except Exception as e:
    out["mounts"] = str(e)
os.makedirs("/tmp/v", exist_ok=True)
with open("/tmp/v/secret.txt", "w") as h:
    h.write("verifier")
os.chmod("/tmp/v", 0o755)
os.chmod("/tmp/v/secret.txt", 0o644)
child = r"""
import os, sys, json, signal
r = {"uid": os.getuid(), "euid": os.geteuid(), "groups": os.getgroups()}
try:
    open("/tmp/v/secret.txt", "a").write("x"); r["write_verifier_file"] = "ALLOWED"
except Exception as e:
    r["write_verifier_file"] = "denied %s" % type(e).__name__
try:
    open("/tmp/v/new.txt", "w").write("x"); r["create_in_verifier_dir"] = "ALLOWED"
except Exception as e:
    r["create_in_verifier_dir"] = "denied %s" % type(e).__name__
try:
    os.kill(int(sys.argv[1]), 0); r["signal_root_parent"] = "ALLOWED"
except Exception as e:
    r["signal_root_parent"] = "denied %s" % type(e).__name__
try:
    open("/proc/%s/mem" % sys.argv[1], "rb").read(1); r["read_parent_mem"] = "ALLOWED"
except Exception as e:
    r["read_parent_mem"] = "denied %s" % type(e).__name__
try:
    open("/proc/%s/environ" % sys.argv[1], "rb").read(10); r["read_parent_environ"] = "ALLOWED"
except Exception as e:
    r["read_parent_environ"] = "denied %s" % type(e).__name__
try:
    os.setuid(0); r["regain_root"] = "ALLOWED"
except Exception as e:
    r["regain_root"] = "denied %s" % type(e).__name__
try:
    open("/tmp/child-%d.txt" % os.getuid(), "w").write("x"); r["write_tmp"] = "ok"
except Exception as e:
    r["write_tmp"] = "denied %s" % type(e).__name__
print(json.dumps(r))
"""
results = {}
for uid in (65534, 20001, 3000000):
    try:
        p = subprocess.run([sys.executable, "-c", child, str(os.getpid())], user=uid, group=uid, extra_groups=[],
                           capture_output=True, timeout=20)
        results[str(uid)] = {"exit": p.returncode, "out": p.stdout.decode()[-800:], "err": p.stderr.decode()[-400:]}
    except Exception as e:
        results[str(uid)] = {"spawn_error": "%s: %s" % (type(e).__name__, str(e)[:200])}
out["children"] = results
# cross-uid: can uid 20002 signal a process of uid 20001?
try:
    victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], user=20001, group=20001, extra_groups=[])
    time.sleep(0.3)
    p = subprocess.run([sys.executable, "-c", "import os,sys\ntry:\n    os.kill(int(sys.argv[1]), 9); print('ALLOWED')\nexcept Exception as e:\n    print('denied', type(e).__name__)", str(victim.pid)],
                       user=20002, group=20002, extra_groups=[], capture_output=True, timeout=10)
    out["cross_uid_kill"] = p.stdout.decode().strip() or p.stderr.decode()[-200:]
    victim.kill()
except Exception as e:
    out["cross_uid_kill"] = "error %s" % e
# leftover process sweep: can root enumerate and kill a daemon left by a uid?
try:
    subprocess.run([sys.executable, "-c", "import os, time\nif os.fork() == 0:\n    os.setsid()\n    time.sleep(60)\n"], user=20003, group=20003, extra_groups=[], timeout=10)
    time.sleep(0.3)
    found = []
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                st = os.stat("/proc/" + pid)
                if st.st_uid == 20003:
                    found.append(int(pid))
            except FileNotFoundError:
                pass
    for pid in found:
        os.kill(pid, 9)
    out["daemon_sweep"] = {"found": len(found)}
except Exception as e:
    out["daemon_sweep"] = "error %s" % e
print(json.dumps(out))
'''


def main() -> int:
    ledger = Ledger()
    executor = TokenFactorySandboxes(load_secret("NEBIUS_API_KEY"), project_id(), ledger, uid=0, gid=0)
    image = executor.resolve_image("python:3.12-slim")
    run = executor.run_branch(image, {"/tmp/probe/probe.py": PROBE.encode()},
                              [{"name": "probe", "cmd": ["/usr/local/bin/python", "/tmp/probe/probe.py"], "cwd": "/tmp", "timeout": 60}],
                              stage="privilege-probe", timeout=120)
    step = run.step("probe")
    report = {"at_utc": utcnow(), "operation_uuid": run.operation_uuid, "status": run.status, "runner_error": run.runner_error,
              "exit_code": step.exit_code if step else None, "stderr_tail": (step.stderr[-1500:] if step else run.raw_stderr_excerpt[-1500:])}
    try:
        report["probe"] = json.loads(step.stdout.strip().splitlines()[-1]) if step and step.stdout.strip() else None
    except Exception as error:  # noqa: BLE001
        report["probe_parse_error"] = str(error)
        report["stdout_tail"] = step.stdout[-1500:] if step else ""
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "reports/attest-hardening-2026-10-16/sandbox-privilege-probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
