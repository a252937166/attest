# Deployment of revision 4 (version 0.4.0) to yungou, 19 Oct 2026, 05:41 to 05:44 UTC

What was deployed: the revised pipeline (`reports/attest-revision-2026-10-19/README.md`: contract audit with executed
witnesses, validated corrections that re-run their gate, the navigable implementer, the ledger journal, the health fix),
the console copy and stylesheet changes that go with it (asset stamp `20261019a`), the updated documentation (README,
FREEZE with the revision-4 pin, TESTING, PILOT, console notes) and the new evidence folder `reports/attest-revision-2026-10-19/`
(the development-gateway validation batches). The package digest recorded in every new bundle on the server is the
pinned revision `b27a1c070a852ae2…` (35 sources); the previous tree (0.3.0, digest `166cdcbd…`) is kept as
`/opt/attest/app.prev` for `rollback.sh`. No Nebius inference call was made by the deployment; the store was not changed
(39 rows before and after, none queued or running).

Scope: the Attest service only (`attest.service`, its tree under `/opt/attest/app`, the nginx vhost file re-installed
unchanged). The other sites on the host were not touched; the before/after snapshots below show the same services,
listeners and nginx configuration. Memory limit unchanged at `MemoryMax=200M`; measured 48.8 MB resident after start.

## Build

- `python3 scripts/export_public.py --out dist/public --force` (05:41 UTC): 155 exported bundles verified with `attest check`,
  0 failed, 0 scan hits; the exported `attest/` digest equals the working tree's (`b27a1c07…`). The stopped first batch of
  the day is excluded from the export by name (see the revision record, section 7).
- `deploy/yungou/build_bundle.sh` run from `dist/public` (`COPYFILE_DISABLE=1`): `app.tar.gz`, 6,500,223 bytes, sha256
  `3247342b726dbc0211aa7708ff5e89b18c1f347a6ca204bc59bebe85b463f2c9`, verified again on the server with `sha256sum -c`.
  macOS tar's `LIBARCHIVE.xattr` headers were reported by GNU tar as on 18 Oct (harmless).

## Procedure (UTC)

| Time | Step | Result |
| --- | --- | --- |
| 05:41 | upload of `app.tar.gz`, `install.sh`, `snapshot.sh`, `rollback.sh`, `attest.service`, `attest.axiqo.xyz.conf` to `/var/tmp/attest-deploy/` | bundle digest matches |
| 05:42 | pre-checks (earlier at 05:36: staged `attest.env` identical to `/etc/attest/attest.env`, 39 rows, none active) | health before: version 0.3.0, worker alive, queue 0, current none; budget text still "1 active reservation(s)" (the message this revision fixes) |
| 05:42 | store backup | `/var/lib/attest/attest.db.bak-20261019a-full` via the SQLite backup API from `/opt/attest/venv/bin/python` (81,920 bytes, 39 rows) |
| 05:42:23 | `snapshot.sh before-20261019a` | `before-20261019a-20261019T054223Z.txt` |
| 05:42:41 | `MEMORY_MAX=200M bash install.sh` | pinned dependencies already satisfied; service restarted (ActiveEnterTimestamp 13:42:41 CST); nginx configuration test OK (the usual deprecation warnings of other vhosts); previous tree moved to `/opt/attest/app.prev` |
| 05:42:44 | `GET /api/health` (`health-after-20261019a.json`) | ok, version 0.4.0, worker alive, queue 0, nothing reconciled or deduplicated at startup, 1,328 MB free (9.6%), budget "$0.0000 committed + 0 active reservation(s) within $2.00", `active_runs` 0 |
| 05:42:56 | `snapshot.sh after-20261019a` | `after-20261019a-20261019T054256Z.txt`; diff against before: the timestamp, memory, swap, disk-free and load lines only |

## Verification after the install

| Check | Result |
| --- | --- |
| `find /opt/attest/app -name '._*' \| wc -l` | 0 |
| `attest_revision()` on the server | `b27a1c070a852ae2f0f2776c59cebe09cea87307a014ca80a1c37f7e66e68b49` over 35 files (the revision-4 pin) |
| `attest/__init__.py` | 0.4.0 in `/opt/attest/app`, 0.3.0 in `/opt/attest/app.prev` |
| served `/`, `/static/styles.css?v=20261019a`, `/static/app.js?v=20261019a` | sha256 `0c0f27894e935f98…`, `d7d84d52469e6ff3…`, `d23088e505f2cce5…`, equal to the exported files; `index.html` carries the `20261019a` stamp 5 times |
| `https://attest.axiqo.xyz/` | 200 |
| `/api/health` (public) | version 0.4.0, "0 active reservation(s)", `active_runs` 0 |
| `/api/profiles` | the public Nemotron profile only, `team: false` |
| gateway name in `/`, the two assets, `/api/runs`, `/api/tasks`, one run detail | 0 hits |
| `/api/runs?limit=200` | 39 rows |
| `attest.service` | active, `MemoryMax=200M`, 48.8 MB resident |
| Real browser on the public URL (headless Chrome, 1440 px and 390 px; `public-render-r4-record.json`, `screens/`) | both asset stamps `20261019a`; Inter, Newsreader and Space Mono loaded; ticker "39 recorded runs, 8 VERIFIED, 11 NEEDS HUMAN, 20 other verdicts"; the verdict legend names the executed witness; the 17 Oct demo run opens with "Hold this patch."; no horizontal overflow at either width; no page or console error |

The deployment script's last loop (`grep -c` of the gateway name over the served assets) aborted the script on its first
zero count because `grep -c` exits 1 when nothing matches under `set -o pipefail`; the remaining checks and the copy of the
records were run by hand (the figures above). The script is a scratch file, not part of `deploy/yungou/`.

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` swaps `/opt/attest/app` and `/opt/attest/app.prev` (the 18 Oct 15:03 UTC tree,
version 0.3.0) and restarts the service; the store backup `attest.db.bak-20261019a-full` is the state before this
deployment. Not exercised today; exercised on 16 Oct.

## Files

`before-20261019a-20261019T054223Z.txt`, `after-20261019a-20261019T054256Z.txt`, `health-before-20261019a.json`,
`health-after-20261019a.json`, `public-render-r4-record.json`, `screens/public-home-r4-{1440,390}.png`,
`screens/public-run-r4-{1440,390}.png`.
