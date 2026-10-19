#!/bin/bash
# Read-only host snapshot: services, listeners, containers, memory, disk, the Attest release links. Usage: snapshot.sh <label>
# Host commands and paths are environment variables with the production defaults (the deployment scripts share them).
set -u
label=${1:-snapshot}
SNAPSHOT_DIR=${SNAPSHOT_DIR:-/var/tmp/attest-deploy}
SYSTEMCTL=${SYSTEMCTL:-systemctl}
NGINX_BIN=${NGINX_BIN:-/usr/local/sbin/nginx-modern}
NGINX_CONF_DIR=${NGINX_CONF_DIR:-/etc/nginx/conf.d}
ATTEST_ROOT=${ATTEST_ROOT:-/opt/attest}
out=$SNAPSHOT_DIR/${label}-$(date -u +%Y%m%dT%H%M%SZ).txt
mkdir -p "$SNAPSHOT_DIR"
{
  echo "=== $(date -u +%FT%TZ) host=$(hostname) label=$label ==="
  echo "--- running services ---"; $SYSTEMCTL list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}' | sort
  echo "--- failed services ---"; $SYSTEMCTL list-units --type=service --state=failed --no-pager --no-legend | awk '{print $1}' | sort
  echo "--- listeners ---"; ss -ltnp | awk 'NR>1{print $4}' | sort -u
  echo "--- containers ---"; docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null
  echo "--- memory ---"; free -m
  echo "--- disk ---"; df -h / | tail -1
  echo "--- load ---"; cat /proc/loadavg
  echo "--- nginx ---"; "$NGINX_BIN" -t 2>&1 | tail -1; ls "$NGINX_CONF_DIR"
  echo "--- attest releases ---"
  for l in app app.prev; do
    if [ -L "$ATTEST_ROOT/$l" ]; then echo "$l -> $(readlink "$ATTEST_ROOT/$l")"; elif [ -d "$ATTEST_ROOT/$l" ]; then echo "$l is a real directory (pre-release layout)"; else echo "$l absent"; fi
  done
  ls "$ATTEST_ROOT/releases" 2>/dev/null
  echo "--- health endpoints ---"
  for u in https://axiqo.xyz/ https://faktura.axiqo.xyz/api/meta https://recart.axiqo.xyz/api/health https://development-gateway.invalid/health; do
    printf "%s " "$u"; curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 "$u"
  done
} > "$out" 2>&1
echo "$out"
