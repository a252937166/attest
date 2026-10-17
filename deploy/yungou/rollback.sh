#!/bin/bash
# Scoped rollback: stop and disable only attest.service, remove only its vhost, reload nginx. Keeps data, code and interpreter.
set -u
systemctl disable --now attest.service 2>/dev/null; systemctl is-active attest.service || true
rm -f /etc/nginx/conf.d/attest.axiqo.xyz.conf
/usr/local/sbin/nginx-modern -t && systemctl reload nginx
echo "attest service stopped and vhost removed; /opt/attest and /var/lib/attest preserved"
