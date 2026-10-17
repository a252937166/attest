#!/bin/bash
# Idempotent installer for the Attest console on the DogYun host (no Docker). Run as root from /var/tmp/attest-deploy.
# Expects: python tarball at ./cpython-3.12-linux-x86_64.tar.gz (checksum verified before transfer), ./app.tar.gz (project
# without runs/.venv/secrets), ./attest.env (secrets, created separately), and the unit/vhost files next to this script.
set -euo pipefail
cd "$(dirname "$0")"
MEMORY_MAX=${MEMORY_MAX:-220M}
id attest >/dev/null 2>&1 || useradd -r -s /sbin/nologin -d /var/lib/attest attest
mkdir -p /opt/attest /var/lib/attest/runs /etc/attest /var/www/letsencrypt
if [ ! -x /opt/attest/python/bin/python3.12 ]; then
  echo "[1/6] installing standalone CPython 3.12"
  rm -rf /opt/attest/python.tmp && mkdir -p /opt/attest/python.tmp
  tar -xzf cpython-3.12-linux-x86_64.tar.gz -C /opt/attest/python.tmp
  mv /opt/attest/python.tmp/python /opt/attest/python && rmdir /opt/attest/python.tmp
fi
/opt/attest/python/bin/python3.12 --version
echo "[2/6] application code"
rm -rf /opt/attest/app.new && mkdir -p /opt/attest/app.new && tar -xzf app.tar.gz -C /opt/attest/app.new
if [ -d /opt/attest/app ]; then rm -rf /opt/attest/app.prev && mv /opt/attest/app /opt/attest/app.prev; fi
mv /opt/attest/app.new /opt/attest/app
echo "[3/6] virtualenv and dependencies (pinned)"
[ -x /opt/attest/venv/bin/python ] || /opt/attest/python/bin/python3.12 -m venv /opt/attest/venv
/opt/attest/venv/bin/python -m pip install --quiet --disable-pip-version-check --upgrade pip
/opt/attest/venv/bin/python -m pip install --quiet --disable-pip-version-check "fastapi==0.115.5" "uvicorn[standard]==0.32.1" "jsonschema==4.23.0" "certifi"
echo "[4/6] secrets and permissions"
install -o root -g attest -m 0640 attest.env /etc/attest/attest.env
chown -R attest:attest /var/lib/attest
chown -R root:root /opt/attest/app && chmod -R o-w /opt/attest/app
echo "[5/6] systemd unit (MemoryMax=$MEMORY_MAX)"
sed "s/__MEMORY_MAX__/$MEMORY_MAX/" attest.service > /etc/systemd/system/attest.service
systemctl daemon-reload
systemctl enable attest.service >/dev/null
systemctl restart attest.service
sleep 3
systemctl is-active attest.service
curl -s --max-time 10 http://127.0.0.1:4070/api/health; echo
echo "[6/6] nginx vhost (http only until the certificate exists)"
if [ -f /etc/letsencrypt/live/attest.axiqo.xyz/fullchain.pem ]; then
  install -m 0644 attest.axiqo.xyz.conf /etc/nginx/conf.d/attest.axiqo.xyz.conf
else
  awk '/^server \{/{n++} n==1' attest.axiqo.xyz.conf | sed 's#return 301 https://$host$request_uri;#proxy_pass http://127.0.0.1:4070;#' > /etc/nginx/conf.d/attest.axiqo.xyz.conf
fi
/usr/local/sbin/nginx-modern -t && systemctl reload nginx
echo "install complete"
