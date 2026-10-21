#!/bin/bash
# Server-side deployment steps of 0.10.2 (the console corrections after 0.10.1) on yungou, run as root in /var/tmp/attest-deploy. Every step prints what it did; the
# first failure stops the script. The installer itself is transactional (it restores the previous release on any failure).
set -euo pipefail
cd /var/tmp/attest-deploy
L=20261021b
echo "== 1. digests of the uploaded files"; sha256sum -c upload.sha256
echo "== 2. snapshot before"; bash snapshot.sh before-$L >/dev/null && ls -1t /var/tmp/attest-deploy/before-$L-*.txt | head -1
echo "== 3. idle check"; H=$(curl -s --max-time 10 http://127.0.0.1:4070/api/health); echo "$H" | python3 -c "import json,sys; h=json.load(sys.stdin); print('version', h['version'], 'busy', h['busy'], 'queue', h['queue'], 'current', h['current'], 'holds', h['reconciliation']['holds_open']); sys.exit(0 if (not h['busy'] and h['queue'] == 0 and not h['current']) else 3)"
echo "$H" > health-before-$L.json
echo "== 4. store backup (SQLite backup API) and a copy of the data directory"
/opt/attest/app/venv/bin/python -c "
import sqlite3
src = sqlite3.connect('file:/var/lib/attest/attest.db?mode=ro', uri=True); dst = sqlite3.connect('/var/lib/attest/attest.db.bak-$L-full')
src.backup(dst); n = dst.execute('select count(*) from runs').fetchone()[0]; h = dst.execute('select count(*) from holds').fetchone()[0]; dst.close(); src.close(); print('backup rows', n, 'holds', h)"
mkdir -p /var/backups && tar czf /var/backups/attest-data-$L.tgz -C /var/lib attest && ls -la /var/backups/attest-data-$L.tgz | awk '{print "data archive", $5, "bytes"}'
sha256sum /var/lib/attest/attest.db.bak-$L-full /var/backups/attest-data-$L.tgz
echo "== 5. install"; MEMORY_MAX=200M bash install.sh app.tar.gz 2>&1 | tee install-$L.log; test "${PIPESTATUS[0]}" = 0
echo "== 6. snapshot after"; bash snapshot.sh after-$L >/dev/null && ls -1t /var/tmp/attest-deploy/after-$L-*.txt | head -1
curl -s --max-time 10 http://127.0.0.1:4070/api/health > health-after-$L.json; head -c 700 health-after-$L.json; echo
echo "== 7. readback"; bash readback.sh > readback-after-deploy-$L.txt 2>&1; cat readback-after-deploy-$L.txt
echo "== done"
