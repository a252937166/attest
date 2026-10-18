# Deploying the Attest console to `yungou` (DogYun, 206.237.18.80)

Files: `attest.service` (systemd, placeholder `__MEMORY_MAX__`), `attest.axiqo.xyz.conf` (nginx), `attest.env.example`,
`snapshot.sh` (read-only before/after host snapshot), `install.sh` (idempotent), `rollback.sh` (scoped).

Sequence (each step is recorded in `reports/attest-deployment-2026-10-15/`):
1. Local: measure the console's resident memory idle and during a run; choose `MEMORY_MAX` from the measurement.
2. Local: build `app.tar.gz` (package, examples, deploy files, evidence bundles to show; no `runs/`, `.venv`, secrets).
3. Local: verify the CPython tarball checksum against the release `SHA256SUMS`.
4. Server: `snapshot.sh before`; copy the three files and the unit/vhost/scripts to `/var/tmp/attest-deploy/`.
5. Server: create `/var/tmp/attest-deploy/attest.env` from the private vault values (never through chat or git).
6. Server: `MEMORY_MAX=... ./install.sh`; health check on 127.0.0.1:4070; `certbot certonly --webroot -w /var/www/letsencrypt -d attest.axiqo.xyz`; install the https vhost; `nginx -t && systemctl reload nginx`.
7. Server: one judge-style sample run through the public URL; `snapshot.sh after`; compare with `before`.
8. Rollback test: `rollback.sh`, verify other vhosts still answer, then reinstall.

## Static files and browser caches (18 Oct 2026)

Before building a bundle that changes anything under `attest/app/static/`, bump the version query on both asset links
in `index.html` (`/static/styles.css?v=<stamp>` and `/static/app.js?v=<stamp>`). The vhost sends `Cache-Control: no-cache`
on every response, so browsers revalidate against the ETag; the version query additionally defeats copies cached before
that header existed. A browser holding the previous build's assets otherwise renders the new markup with the old
stylesheet and script (seen on 18 Oct 2026, `reports/attest-deployment-2026-10-18/README.md`).

## 17 Oct 2026 procedure (reliability round, M3 console, M4 import)

1. Local: `python3 scripts/export_public.py --out dist/public --force` (allowlisted copy, gateway host and key shapes
   redacted, secret scan must pass), then `deploy/yungou/build_bundle.sh /tmp/attest-app.tar.gz` run from `dist/public`
   so the server receives exactly the public tree plus the redacted evidence reports; screenshots, snapshots, zips, run
   data and env files are excluded by the script and the listing check fails if any slips through.
2. Server: `snapshot.sh before-20261017`; copy `app.tar.gz`, `attest.service`, `attest.axiqo.xyz.conf`, `install.sh`,
   `rollback.sh` to `/var/tmp/attest-deploy/`; append `ATTEST_CODEX_BASE_URL=<private gateway URL>` to
   `/etc/attest/attest.env` (the public code carries only a placeholder default); `MEMORY_MAX=200M ./install.sh`.
3. Server: `curl 127.0.0.1:4070/api/health`, `/api/runs` (imported evidence is Nemotron-only, `ATTEST_IMPORT_PROVIDERS=nebius`),
   public `https://attest.axiqo.xyz/` and `/api/profiles` (no development profile without the token), `snapshot.sh
   after-20261017`, compare with before. Rollback: `rollback.sh` (scoped) or `mv /opt/attest/app.prev /opt/attest/app`
   and `systemctl restart attest.service`.
