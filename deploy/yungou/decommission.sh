#!/bin/bash
# Decommission the Attest console on this host: stop and disable only attest.service, remove only its nginx vhost, test and
# reload nginx. Keeps /opt/attest (releases, interpreter), /var/lib/attest (store, runs), /etc/attest (secrets) and the unit
# file (disabled). This is NOT a version rollback: use rollback.sh for that. Until the 19 Oct 2026 audit (OPS-01) this
# behaviour was what rollback.sh did while the runbooks described a version swap; the two are now separate scripts.
#
#   bash decommission.sh          # prints the plan and refuses (exit 2)
#   bash decommission.sh --yes    # executes the plan
#
# Host paths and commands are environment variables with the production defaults (rehearsable under shims). bash 3.2.
set -euo pipefail

ATTEST_ROOT=${ATTEST_ROOT:-/opt/attest}
ATTEST_DATA_DIR=${ATTEST_DATA_DIR:-/var/lib/attest}
ATTEST_ENV_DIR=${ATTEST_ENV_DIR:-/etc/attest}
SYSTEMD_UNIT_DIR=${SYSTEMD_UNIT_DIR:-/etc/systemd/system}
UNIT_NAME=${UNIT_NAME:-attest.service}
NGINX_CONF_DIR=${NGINX_CONF_DIR:-/etc/nginx/conf.d}
NGINX_BIN=${NGINX_BIN:-/usr/local/sbin/nginx-modern}
VHOST_NAME=${VHOST_NAME:-attest.axiqo.xyz.conf}
SYSTEMCTL=${SYSTEMCTL:-systemctl}

plan() {
  echo "decommission.sh will:"
  echo "  1. $SYSTEMCTL disable --now $UNIT_NAME        (stop and disable only this unit; the unit file $SYSTEMD_UNIT_DIR/$UNIT_NAME stays, disabled)"
  echo "  2. rm -f $NGINX_CONF_DIR/$VHOST_NAME          (only the Attest vhost; every other vhost stays)"
  echo "  3. $NGINX_BIN -t && $SYSTEMCTL reload nginx    (reload only after the remaining configuration passes the test)"
  echo "  keep: $ATTEST_ROOT (releases, interpreter), $ATTEST_DATA_DIR (store, runs), $ATTEST_ENV_DIR (secrets)"
  echo "  not a version rollback: bash rollback.sh re-selects the previous release instead"
}

case "${1:-}" in
  --yes) ;;
  -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  "") plan; echo "refusing: pass --yes to execute (nothing was changed)"; exit 2 ;;
  *) plan; echo "unknown argument: $1 (nothing was changed)" >&2; exit 2 ;;
esac

plan
echo "executing"
if $SYSTEMCTL disable --now "$UNIT_NAME"; then
  echo "  $UNIT_NAME stopped and disabled"
else
  echo "  warning: disable --now $UNIT_NAME returned non-zero (unit missing or already stopped)"
fi
echo "  $UNIT_NAME is now: $($SYSTEMCTL is-active "$UNIT_NAME" 2>/dev/null || true)"
if [ -f "$NGINX_CONF_DIR/$VHOST_NAME" ]; then
  rm -f "$NGINX_CONF_DIR/$VHOST_NAME"
  echo "  vhost removed: $NGINX_CONF_DIR/$VHOST_NAME"
else
  echo "  no vhost at $NGINX_CONF_DIR/$VHOST_NAME"
fi
if "$NGINX_BIN" -t; then
  $SYSTEMCTL reload nginx
  echo "  nginx reloaded"
else
  echo "  nginx -t FAILED: nginx was NOT reloaded (its running configuration still includes the removed vhost); fix the configuration and reload by hand" >&2
  exit 1
fi
echo "decommissioned: $UNIT_NAME stopped and disabled, vhost removed; kept $ATTEST_ROOT, $ATTEST_DATA_DIR, $ATTEST_ENV_DIR"
