# Re-deployment of the hardened Attest build to yungou (DogYun 206.237.18.80), 16 Oct 2026

This re-deploys the hardened build (phase 1 verification/budget/disk, phase 2 arbitration/efficiency, the GET-retry
sandbox client) over the live console from 2026-10-15. The first deployment record is preserved in
`reports/attest-deployment-2026-10-15/`. Nothing about the host arrangement changed: console/API/orchestration/data stay on
yungou without Docker; Nebius Sandboxes remain the executor; no Docker component was added to the Aliyun host.

## Procedure (idempotent, scoped to attest)

1. `snapshot.sh before-redeploy` (read-only).
2. `scp app.tar.gz` (2.0 MB, hardened code; secret scan clean) + the unit/vhost/scripts to `/var/tmp/attest-deploy/`.
3. `MEMORY_MAX=200M ./install.sh`: reused the standalone CPython 3.12.15 and the venv already present; swapped
   `/opt/attest/app` (previous kept as `/opt/attest/app.prev` for instant restore); reinstalled pinned deps; rewrote the unit
   (`MemoryMax=200M`); restarted **only** `attest.service`; `nginx-modern -t` then reloaded nginx. Secrets untouched
   (`/etc/attest/attest.env` already present).
4. Health check on `127.0.0.1:4070`, public check on `https://attest.axiqo.xyz`, `snapshot.sh after-redeploy`, compared.

## Verification

- **Hardened code live:** `attest/core/sealed.py` contains the privilege-separation supervisor; `attest/app/db.py` contains
  the atomic budget reservation. Service `active`, `MemoryCurrent` 44 MB under `MemoryMax=200M`.
- **New health surface** (`/api/health`): `disk {free_mb: 1386, free_frac: 0.10, low: false, accepting_runs: true}`,
  `budget {daily_cap_usd: 2.0, per_run_cap_usd: 0.5, nebius_ok: true}`, `reconciled_at_startup: []`.
- **Other services preserved.** before/after snapshot diff is only the timestamp, normal memory fluctuation (358→345 MB used;
  free 55→67 MB) and load counts. Services, listeners, containers, nginx config and the four other public endpoints are
  identical. `axiqo.xyz`, `recart`, `codex` returned 200 throughout; `faktura` returned a single transient `000` during a
  network blip and 200 on all three immediate retries (~1 s) — it was never touched (no faktura unit or vhost change).
- **Rollback readiness:** `rollback.sh` staged (scoped stop of `attest.service` + removal of its vhost only); `app.prev`
  retained for an instant code restore. The scoped rollback+reinstall cycle was fully exercised in the 2026-10-15 deployment
  and the mechanism is unchanged, so it was not repeated here (it briefly takes the console down); the restore path is in place.
- Evidence: `before-redeploy.txt`, `after-redeploy.txt`.

## Note

- On the day of deploy, imported historical evidence runs (created earlier the same UTC day) count toward the daily Nebius
  budget shown in health (`$0.75 committed`), so judges have roughly `$1.25` of the `$2.00` daily cap for fresh console runs
  on day one; this self-clears the next day (older runs no longer match "today"). The per-run `$0.50` cap is unaffected.

## Public judge-style run on the hardened console (post-redeploy)

Started from off-server with no admin token (`POST /api/runs {durationkit-units-001, nebius}` → `judge-demo` profile):
run `durationkit-units-001-20261015T185629796814Z`, **VERIFIED**, through the full hardened pipeline (spec → seal →
implement → break → audit). Binding check `verifier_isolation_active: true` — privilege separation is active on the
server's Nebius sandbox path, not just locally. Sealed 27/27 methods each in its own privilege-separated process;
mutation 9 killed / 3 survived (0.75); all five gates pass; committed cost $0.0591. Downloadable Proof Bundle fetched
from the public API: `judge-run-proof-bundle.zip`; run record `judge-run-record.json`. Other sites stayed 200 throughout.
