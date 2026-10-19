#!/bin/bash
# Runs on yungou as root after the deployment. A temporary unit only: attest.service, nginx and every other service are not touched.
set -u
D=/var/lib/attest-app-oom-drill
U=attest-app-oom-drill.service
cleanup() {
  systemctl stop $U >/dev/null 2>&1 || true
  rm -f /etc/systemd/system/$U
  systemctl daemon-reload
  systemctl reset-failed $U >/dev/null 2>&1 || true
  rm -rf $D /var/tmp/attest-app-oom-drill-upload
}
trap cleanup EXIT
echo "== before: attest.service $(systemctl is-active attest.service), MainPID $(systemctl show attest -p MainPID | cut -d= -f2)"
mkdir -p $D/state && cp /var/tmp/attest-app-oom-drill-upload/drill_app.py $D/ && chown -R attest:attest $D && chmod 0755 $D $D/state
cp /var/tmp/attest-app-oom-drill-upload/$U /etc/systemd/system/
systemctl daemon-reload
T0=$(date '+%Y-%m-%d %H:%M:%S')
echo "== drill started $(date -u +%H:%M:%SZ)"
systemctl start $U
for i in $(seq 1 90); do st=$(systemctl show $U -p ActiveState | cut -d= -f2); [ "$st" = inactive ] || [ "$st" = failed ] && break; sleep 1; done
echo "final state: $(systemctl show $U -p ActiveState -p SubState -p Result -p ExecMainStatus | tr '\n' ' ')"
echo "-- drill log (allocation lines shortened to the last three)"
grep -v "allocated" $D/state/drill.log; grep "allocated" $D/state/drill.log | tail -3
echo "-- unit journal"; journalctl -u $U --since "$T0" --no-pager -o short-iso | grep -E "killed|restart|Started|exited" | tail -8
echo "-- kernel"; journalctl -k --since "$T0" --no-pager -o short-iso | grep -iE "memory cgroup out of memory|memory: usage|memory\+swap: usage|oom-kill:" | tail -5
echo "== after: attest.service $(systemctl is-active attest.service), MainPID $(systemctl show attest -p MainPID | cut -d= -f2)"
