#!/bin/bash
# Runs on yungou as root. Temporary units only: attest.service, nginx and every other service are not touched.
set -u
D=/var/lib/attest-oom-drill
cleanup() {
  systemctl stop attest-oom-drill.service attest-swap-drill.service >/dev/null 2>&1 || true
  rm -f /etc/systemd/system/attest-oom-drill.service /etc/systemd/system/attest-swap-drill.service
  systemctl daemon-reload
  systemctl reset-failed attest-oom-drill.service attest-swap-drill.service >/dev/null 2>&1 || true
}
trap cleanup EXIT
echo "== before: attest.service $(systemctl is-active attest.service), MainPID $(systemctl show attest -p MainPID | cut -d= -f2); free:"; free -m | sed -n 1,3p
mkdir -p $D/oom $D/swap && cp /var/tmp/attest-oom-drill-upload/drill.py $D/drill.py && chown -R attest:attest $D && chmod 0755 $D $D/oom $D/swap
cp /var/tmp/attest-oom-drill-upload/attest-oom-drill.service /var/tmp/attest-oom-drill-upload/attest-swap-drill.service /etc/systemd/system/
systemctl daemon-reload
T0=$(date '+%Y-%m-%d %H:%M:%S')
echo "== drill 1 (MemoryLimit=96M and memory+swap 96M, Restart=on-failure), started $(date -u +%H:%M:%SZ)"
systemctl start attest-oom-drill.service
sleep 1
CG=/sys/fs/cgroup/memory/system.slice/attest-oom-drill.service
echo "systemd MemoryLimit=$(systemctl show attest-oom-drill -p MemoryLimit | cut -d= -f2); limit_in_bytes=$(cat $CG/memory.limit_in_bytes 2>/dev/null); memsw.limit_in_bytes=$(cat $CG/memory.memsw.limit_in_bytes 2>/dev/null)"
for i in $(seq 1 40); do st=$(systemctl show attest-oom-drill -p ActiveState -p SubState -p ExecMainStatus | tr '\n' ' '); case "$st" in *"ActiveState=inactive"*|*"ActiveState=failed"*) break ;; esac; sleep 1; done
echo "final state: $(systemctl show attest-oom-drill -p ActiveState -p SubState -p Result -p ExecMainStatus -p ExecMainCode | tr '\n' ' ')"
echo "-- drill log"; cat $D/oom/drill.log
echo "-- unit journal"; journalctl -u attest-oom-drill --since "$T0" --no-pager -o short-iso | grep -v "Unknown lvalue" | tail -20
echo "-- kernel"; journalctl -k --since "$T0" --no-pager -o short-iso | grep -iE "memory cgroup|oom|killed process|memory\+swap|memory: usage" | tail -12
T1=$(date '+%Y-%m-%d %H:%M:%S')
echo "== drill 2 (contrast: MemoryLimit=96M alone, no memory+swap limit), started $(date -u +%H:%M:%SZ)"
systemctl start attest-swap-drill.service
sleep 1
CG2=/sys/fs/cgroup/memory/system.slice/attest-swap-drill.service
echo "systemd MemoryLimit=$(systemctl show attest-swap-drill -p MemoryLimit | cut -d= -f2); limit_in_bytes=$(cat $CG2/memory.limit_in_bytes 2>/dev/null); memsw.limit_in_bytes=$(cat $CG2/memory.memsw.limit_in_bytes 2>/dev/null)"
peak_memsw=0
for i in $(seq 1 90); do
  u=$(cat $CG2/memory.memsw.usage_in_bytes 2>/dev/null || echo 0); [ "$u" -gt "$peak_memsw" ] && peak_memsw=$u
  st=$(systemctl show attest-swap-drill -p ActiveState | cut -d= -f2); [ "$st" = active ] || [ "$st" = activating ] || break; sleep 1
done
echo "final state: $(systemctl show attest-swap-drill -p ActiveState -p SubState -p Result -p ExecMainStatus -p ExecMainCode | tr '\n' ' '); peak memory+swap usage seen ${peak_memsw} bytes"
echo "-- drill log"; tail -6 $D/swap/drill.log
echo "-- kernel"; journalctl -k --since "$T1" --no-pager -o short-iso | grep -iE "memory cgroup|oom|killed process" | tail -5 || true
echo "== after: attest.service $(systemctl is-active attest.service), MainPID $(systemctl show attest -p MainPID | cut -d= -f2); free:"; free -m | sed -n 1,3p
rm -rf $D /var/tmp/attest-oom-drill-upload
