#!/bin/bash
# Read-only host snapshot: services, listeners, containers, memory, disk. Usage: snapshot.sh <label>
set -u
label=${1:-snapshot}
out=/var/tmp/attest-deploy/${label}-$(date -u +%Y%m%dT%H%M%SZ).txt
mkdir -p /var/tmp/attest-deploy
{
  echo "=== $(date -u +%FT%TZ) host=$(hostname) label=$label ==="
  echo "--- running services ---"; systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}' | sort
  echo "--- failed services ---"; systemctl list-units --type=service --state=failed --no-pager --no-legend | awk '{print $1}' | sort
  echo "--- listeners ---"; ss -ltnp | awk 'NR>1{print $4}' | sort -u
  echo "--- containers ---"; docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null
  echo "--- memory ---"; free -m
  echo "--- disk ---"; df -h / | tail -1
  echo "--- load ---"; cat /proc/loadavg
  echo "--- nginx ---"; /usr/local/sbin/nginx-modern -t 2>&1 | tail -1; ls /etc/nginx/conf.d/
  echo "--- health endpoints ---"
  for u in https://axiqo.xyz/ https://faktura.axiqo.xyz/api/meta https://recart.axiqo.xyz/api/health https://development-gateway.invalid/health; do
    printf "%s " "$u"; curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 "$u"
  done
} > "$out" 2>&1
echo "$out"
