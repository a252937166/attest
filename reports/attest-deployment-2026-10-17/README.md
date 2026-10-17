# Deployment of the 17 Oct 2026 build to yungou (DogYun 206.237.18.80)

Deployed: the redesigned console (M3), the reliability round (supervisor v6, pacing, provenance, terminology) and M4 (bounded
import; the CLI only). Version `0.3.0` replaced `0.1.0`-labelled hardened build of 16 Oct. The host arrangement is unchanged:
console, API, orchestration and data on yungou without Docker; Nebius Sandboxes as the executor; no Docker component on Aliyun
for Attest. The earlier deployment records (`reports/attest-deployment-2026-10-15/`, `-2026-10-16/`) are untouched.

## What was shipped, and from where

- The tarball (`app.tar.gz`, 3.0 MB, 1,720 entries, sha256 `f2a140905eb06775…`) was built with `deploy/yungou/build_bundle.sh`
  **from the public export** (`python3 scripts/export_public.py --out dist/public`), so the server runs exactly the tree that
  will be published: 1,511 files, 291 redactions in 99 text files (the development gateway's host, key shapes and local
  paths), secret scan clean. Development screenshots (`reports/attest-m3-2026-10-17/screens`, `refresh-sequence`), batch
  snapshots, bundle zips and run data are excluded; the script's listing check fails if any of them slips in. A defect in
  the old script (`--exclude='runs'` also dropped every `reports/**/runs` evidence directory) was fixed first.
- Evidence imported by the console at startup: `reports/attest-verification-2026-10-15/evidence-runs`,
  `reports/attest-first-slice-2026-10-15`, and newly `reports/attest-evaluation-2026-10-16/runs` (25 Nemotron runs, among
  them the `rle-encode` hold with the digit counterexample). Imports are restricted to the judge profile's provider
  (`ATTEST_IMPORT_PROVIDERS=nebius`), so development-profile bundles are not downloadable from the public console.
- `/etc/attest/attest.env` gained `ATTEST_CODEX_BASE_URL` (private; the public code carries only a placeholder default), so
  the team profile keeps working behind the admin token. No key was changed.

## Procedure (scoped to attest.service and its vhost)

1. `snapshot.sh before-20261017` (read-only; `before-20261017-20261017T124633Z.txt`).
2. Consistent SQLite backup of the store with the backup API (`/var/lib/attest/attest.db.bak-20261017`, 23 runs, 75 events);
   a plain copy had been taken first and discarded because the data lived in the WAL file.
3. `MEMORY_MAX=200M ./install.sh`: `/opt/attest/app` swapped (previous kept as `app.prev`), pinned dependencies reinstalled
   into the existing venv, unit rewritten, **only** `attest.service` restarted, `nginx -t` then reload. Health at
   `127.0.0.1:4070` answered `version 0.3.0`, worker alive, 1,364 MB free.
4. Store hygiene: the 8 development-profile runs imported before today (requester `import`, provider `codex`) were removed
   from the live store (their events: none), leaving 38 Nemotron runs; the startup de-duplication also removed two legacy
   duplicate rows (pre-M1 hygiene). The service was restarted once more.
5. Verification, then `snapshot.sh after-20261017` (`after-20261017-20261017T124815Z.txt`) and a diff against before.

## Verification

| Check | Result |
| --- | --- |
| `GET /api/health` (public) | `version 0.3.0`, worker alive, queue 0, disk 1,370 MB free (`health-after.json`) |
| `GET /api/runs` (public) | 38 runs, all provider `nebius`; verdicts: 10 BASELINE, 10 NEEDS HUMAN, 9 ERROR, 8 VERIFIED, 1 NO CHANGE |
| `GET /api/profiles` (public) | only the Nemotron judge profile; `team: false` |
| Page source and `app.js` | no occurrence of the development gateway's name |
| Downloaded bundle of a public Nemotron run (`public-bundle-durationkit-units-001-20261015T185629796814Z.zip`) | `attest check`: OK, 0 errors, 3 warnings (recorded before M2: no manifest, integrity not checkable) |
| Service memory | `MemoryCurrent` 38 MB under `MemoryMax=200M` |
| Other services | before/after snapshot diff: only memory (366 to 373 MB used), swap, load and the disk percentage (90% to 91%: `app.prev` plus the new tree); services, listeners, containers and nginx config identical; `axiqo.xyz`, `faktura`, `recart` and `codex` endpoints 200 before and after |

Rollback remains staged: `rollback.sh` (stop and disable `attest.service`, remove its vhost, reload nginx) or
`mv /opt/attest/app.prev /opt/attest/app && systemctl restart attest.service`; the store backup restores the 8 removed rows
if the owner wants development runs listed again (`ATTEST_IMPORT_PROVIDERS=nebius,codex` would re-import them).

## Limitations

- The disk is at 91% with 1.37 GB free; the retention guard (`ATTEST_RETENTION_KEEP`, `ATTEST_MIN_FREE_MB`) is unchanged.
- No judge-style Nemotron run was started after this deployment (no paid inference without the owner's approval); the
  redesigned console was verified in a real browser locally (`reports/attest-m3-2026-10-17/`) and through its public API here.
- The M5 redeploy (plan item 5.4) will repeat this procedure with the final build.

## Second deployment of the day (15:19 UTC): export verification, budget accounting, freeze

What changed between the two deployments of 17 Oct, and what the server now runs: the budget-accounting fixes (an errored
run keeps its committed cost; interrupted Nebius runs keep the per-run cap as committed cost; the daily budget counts errored
runs), the development gateway's URL read from the private environment only (the package carries no host), the strict-mode
arbitration schema, the register-only harness mode, and the documentation (`FREEZE.md`, `TESTING.md`, README section for
judges). The tarball (`app.tar.gz`, 4.1 MB, sha256 `0d49b046e96ea838…`) was built from the public export at review commit
`1054a63` (code identical to the pinned freeze commit `06553c83…`: package digest `36369c7b…`); the export verified all 90
exported bundles (`attest check` OK, redacted runs traced by `REDACTION.json` with derived manifests) and the privacy scan
ran last with no hits.

Procedure: consistent store backup (`attest.db.bak-20261017b`), `snapshot.sh before-20261017b`, `MEMORY_MAX=200M ./install.sh`
(only `attest.service` restarted; `app.prev` now holds the 12:47 build), `snapshot.sh after-20261017b`.

| Check | Result |
| --- | --- |
| `GET /api/health` (public) | `version 0.3.0`, worker alive, queue 0, 1,347 MB free, daily budget remaining $2.00 (`health-after-2.json`) |
| `GET /api/runs`, `GET /api/profiles` | 38 runs, all `nebius`; only the Nemotron profile; `team: false` |
| Downloaded bundles (`durationkit-units-001-20261015T185629796814Z`, VERIFIED; `rle-encode-20261015T181805Z`, NEEDS HUMAN) | `attest check` OK, 0 errors, 3 warnings each (recorded before M2: no manifest); zips kept here |
| Page source | no occurrence of the development gateway's name |
| Other services | before/after diff: memory 372 to 368 MB used, swap, load, disk 1.4 to 1.3 GB free; services, listeners, containers and nginx config identical; the four other endpoints 200 before and after |

Verified locally but exercised on the server only indirectly: the fault-injection paths (`tests/test_budget.py`) run against
fakes; the server's store now carries the new accounting rules for future runs, and no live run was started to provoke a
crash. Not deployed anywhere: nothing of this round is pending deployment; the M5 redeploy will follow the paid run.

Disk: 1.3 GB free at 91% use; `app.prev` can be removed after the owner is satisfied with this build to recover about 11 MB.
