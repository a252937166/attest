#!/bin/bash
# Read-only readback on yungou after a deployment (revision 8): version, package digest, release links, the effective memory limit,
# the service's process and cgroup, queue, reservations and budget. Nothing is changed.
set -u
U=attest.service
CG=/sys/fs/cgroup/memory/system.slice/$U
PID=$(systemctl show $U -p MainPID | cut -d= -f2)
echo "time_utc $(date -u +%FT%TZ)"
echo "unit $(systemctl is-active $U); MainPID $PID; started $(systemctl show $U -p ExecMainStartTimestamp | cut -d= -f2-)"
echo "app -> $(readlink /opt/attest/app); app.prev -> $(readlink /opt/attest/app.prev)"
/opt/attest/app/venv/bin/python -c "import sys; sys.path.insert(0, '/opt/attest/app'); import attest; from attest.core.provenance import attest_revision; from pathlib import Path; r = attest_revision(Path('/opt/attest/app/attest')); print('package', attest.__version__, r['digest'], r['files'], 'files')"
echo "systemd $(systemctl show $U -p MemoryLimit -p MemoryAccounting | tr '\n' ' ')"
for f in memory.limit_in_bytes memory.memsw.limit_in_bytes memory.usage_in_bytes memory.memsw.usage_in_bytes memory.max_usage_in_bytes memory.failcnt memory.memsw.failcnt; do echo "cgroup $f $(cat $CG/$f 2>/dev/null || echo missing)"; done
echo "cgroup oom_control $(tr '\n' ' ' < $CG/memory.oom_control 2>/dev/null)"
echo "main process memory cgroup $(grep ':memory:' /proc/$PID/cgroup 2>/dev/null | cut -d: -f3)"
echo "main process $(grep -E '^(VmRSS|VmSwap)' /proc/$PID/status 2>/dev/null | tr -s ' \t' ' ' | tr '\n' ' ')"
echo "health $(curl -s --max-time 10 http://127.0.0.1:4070/api/health)"
echo "store rows $(/opt/attest/app/venv/bin/python -c "import sqlite3; c = sqlite3.connect('file:/var/lib/attest/attest.db?mode=ro', uri=True); print(c.execute('select count(*) from runs').fetchone()[0], 'runs;', c.execute(\"select count(*) from runs where status in ('queued','running')\").fetchone()[0], 'queued or running')")"
echo "other services: $(for s in nginx codex-api-relay docker containerd fail2ban firewalld sshd crond; do printf '%s=%s ' $s $(systemctl is-active $s 2>/dev/null); done)"
echo "nginx -t: $(/usr/local/sbin/nginx-modern -t 2>&1 | tail -1)"
echo "memory: $(free -m | awk 'NR==2{print "used " $3 " MB, available " $7 " MB"} NR==3{print "; swap used " $3 " MB"}' | tr '\n' ' ')"
