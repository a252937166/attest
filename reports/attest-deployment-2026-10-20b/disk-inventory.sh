#!/bin/bash
# Read-only disk inventory of yungou (revision 10, item 6): filesystem and inode use, the Attest-owned trees, the largest other
# consumers (named by top-level directory only), Docker's own accounting, journald and the processes that wrote most since boot.
set -u
echo "time_utc $(date -u +%FT%TZ)"
echo "== filesystem /"; df -B1 / | tail -1 | awk '{printf "size %d used %d available %d (%.2f%% free)\n", $2, $3, $4, 100*$4/$2}'
echo "== inodes /"; df -i / | tail -1 | awk '{print "inodes", $2, "used", $3, "free", $4, "use", $5}'
echo "== Attest-owned (MB)"; du -sm /opt/attest/releases/* /opt/attest/python /opt/attest/venv /var/lib/attest /var/tmp/attest-deploy /var/tmp/attest-disk-archive-20261020* /var/backups/attest-data-* 2>/dev/null
echo "== the Attest data directory (MB)"; du -sm /var/lib/attest/runs /var/lib/attest/attest.db* 2>/dev/null | awk '{s+=$1} END {print "total", s}'
echo "== top-level consumers (MB)"; du -xsm /opt /var/lib/docker /var/log /usr /root /swapfile2 2>/dev/null
echo "== under /opt (MB, largest 8)"; du -xsm /opt/* 2>/dev/null | sort -rn | head -8
echo "== under /root (MB, largest 6)"; du -xsm /root/* /root/.[!.]* 2>/dev/null | sort -rn | head -6
echo "== docker (own accounting)"; docker system df 2>/dev/null
echo "== journald"; journalctl --disk-usage 2>/dev/null
echo "== writers since boot (MB written, over 10 MB)"; for p in /proc/[0-9]*; do w=$(awk '/^write_bytes/ {print $2}' $p/io 2>/dev/null); [ -n "$w" ] && [ "$w" -gt 10000000 ] && echo "$((w/1048576)) $(cat $p/comm)"; done 2>/dev/null | sort -rn | head -8
echo "== releases"; echo "app -> $(readlink /opt/attest/app); app.prev -> $(readlink /opt/attest/app.prev)"; ls -1 /opt/attest/releases
echo "== services"; for s in attest nginx codex-api-relay docker containerd fail2ban firewalld sshd crond; do printf '%s=%s ' $s $(systemctl is-active $s 2>/dev/null); done; echo
