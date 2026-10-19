# Deployment of revision 5 (version 0.5.0) to yungou, 19 Oct 2026, 08:46 to 08:48 UTC

What was deployed: the repaired revision (`reports/attest-audit-repairs-2026-10-19/README.md`: the 35 audit findings, evidence
protocol 2, supervisor v7, strict `attest check`, console admission and publication repairs, host boundaries, release and
rollback safeguards), the console copy and client changes that go with it (asset stamp `20261019b`), the updated documentation
(README, FREEZE with the revision-5 pin, TESTING, PILOT, console notes) and the new evidence folders
`reports/attest-audit-2026-10-19/` (the audit, without its synthetic bundles) and `reports/attest-audit-repairs-2026-10-19/`
(repairs, suite logs, the two development-gateway batches). The package digest recorded in every new bundle on the server is the
pinned revision `1e12d46217fb6b8a…` (35 sources, review commit `320651d3…`). No Nebius inference call was made by the
deployment; the store was not changed by the installer (39 rows before and after; the service added its new columns at start:
`visibility`, `error_code`, `error_ref`, `error_detail`).

This was the first deployment with the transactional installer (OPS-02) and the first on the release layout: the real
directory `/opt/attest/app` (0.4.0) became `/opt/attest/releases/legacy-0.4.0-b27a1c070a85` (keeping the shared
`/opt/attest/venv` through a symlink), `/opt/attest/app.prev` (0.3.0) became `releases/legacy-0.3.0-166cdcbd46a7`, the new
release got its own virtualenv, and `/opt/attest/app` is now a symlink the unit follows (`ExecStart=/opt/attest/app/venv/bin/python`).

Scope: the Attest service only (`attest.service`, its unit, its vhost, `/opt/attest`). The vhost changed in one line per
location block (`proxy_set_header X-Forwarded-For $remote_addr`, API-01); `nginx -t` ran with the new file in place before the
switch and nginx was reloaded once after the health check. The other sites on the host were not touched; the before/after
snapshots below show the same services, listeners and nginx configuration. Memory limit unchanged at `MemoryMax=200M`;
measured 38.8 MB resident after start.

## Build

- `python3 scripts/export_public.py --out dist/public --force` (08:38 UTC): staged export, 164 exported bundles verified with
  `attest check` (the seven new batch bundles with complete evidence under protocol 2, the rest as historical bundles), 0 failed,
  0 scan hits, 4 evidence archives excluded by policy; the exported `attest/` digest equals the working tree's (`1e12d462…`).
  Review commits: code `bf14b7f`, export fix `320651d` (the pinned code commit), pin `7c1c734`.
- `deploy/yungou/build_bundle.sh /tmp/attest-app.tar.gz` run from `dist/public`: `app.tar.gz`, 7,501,684 bytes, 3,798 members,
  sha256 `3c617f0c621c7451388d70ac6e68a0ac26b417b7381e67ac6d4e0997348cbfb3`, `RELEASE.json` with 3,387 entries (version 0.5.0,
  package digest `1e12d462…`, label `0.5.0-1e12d46217fb`), verified again on the server with `sha256sum -c`.

## Procedure (UTC)

| Time | Step | Result |
| --- | --- | --- |
| 08:45 | upload of `app.tar.gz`, `install.sh`, `rollback.sh`, `decommission.sh`, `snapshot.sh`, `attest.service`, `attest.axiqo.xyz.conf` to `/var/tmp/attest-deploy/` | bundle digest matches; the staged `attest.env` is identical to `/etc/attest/attest.env` |
| 08:46 | store backup | `/var/lib/attest/attest.db.bak-20261019b-full` via the SQLite backup API from `/opt/attest/venv/bin/python` (39 rows) |
| 08:46 | health before | version 0.4.0, worker alive, "$0.0000 committed + 0 active reservation(s) within $2.00" (`health-before-20261019b.json`) |
| 08:46:45 | `snapshot.sh before-20261019b` | `before-20261019b-20261019T084645Z.txt` |
| 08:47:05 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019b.log`) | steps 01 to 15 all ok: preflight; extraction into a staging directory; every `RELEASE.json` entry verified; release directory; per-release venv with the pins; `compileall`, dependency import, `import attest` with version 0.5.0 and digest equal to `RELEASE.json`; unit and https vhost rendered; `nginx -t` with the new vhost in place; switch with the legacy migration; unit written, daemon-reload, enabled; restart; strict health (HTTP 200, version 0.5.0, worker alive, 1,206 MB free); 3,387 entries read back in place and the digest read back through `/opt/attest/app`; nginx reloaded; releases kept: `0.5.0-1e12d46217fb`, `legacy-0.4.0-b27a1c070a85`, `legacy-0.3.0-166cdcbd46a7`; `install complete` |
| 08:47:22 | `INSTALLED.json` | label `0.5.0-1e12d46217fb`, bundle sha256 `3c617f0c…`, previous `legacy-0.4.0-b27a1c070a85` |
| 08:47:38 | `snapshot.sh after-20261019b` | `after-20261019b-20261019T084738Z.txt`; diff against before: the timestamp, memory, swap, disk-free (1.3 GB to 1.2 GB, the new venv) and load lines, plus the new `app -> releases/...` lines of the release layout |

## Verification after the install

| Check | Result |
| --- | --- |
| `GET /api/health` (local) | ok, version 0.5.0, worker alive, `ready` true, `busy` false, queue 0, "$0.0000 committed + 0 active reservation(s) within $2.00", `budget.policy` names the UTC-day rule, `startup {reconciled 0, deduplicated 0}`, no `data_dir` field (API-04) |
| `readlink /opt/attest/app`, `/opt/attest/app.prev` | `releases/0.5.0-1e12d46217fb`, `releases/legacy-0.4.0-b27a1c070a85` |
| `attest_revision()` through `/opt/attest/app/venv/bin/python` | `1e12d46217fb6b8a27a08b4463f42f361e7309257b211103c08777c91cb10ce5` over 35 files (the revision-5 pin) |
| Server runtime (API-03 readback) | Python 3.12.15, SQLite 3.53.1 (the audit reproduced the cursor fault on 3.12.0 / 3.42.0; the repair materialises every query under the lock regardless) |
| `find /opt/attest/app/ -name '._*' \| wc -l` | 0 |
| served `index.html`, `styles.css`, `app.js` | sha256 `7627446fd1ef8078…`, `d7d84d52469e6ff3…`, `c9f972bd0b5ed6d9…`; stamp `20261019b` |
| `/api/runs?limit=200` | 39 rows; the public row keys carry `visibility`, `has_artifacts`, `error_code`, `error_public` and no `requester`, `out_dir` or `error` |
| `attest.service` | active, `MemoryMax=200M`, 38.8 MB resident, `ExecStart=/opt/attest/app/venv/bin/python -m uvicorn ...` |
| `https://attest.axiqo.xyz/` | 200 |
| `/api/health` (public) | version 0.5.0, "0 active reservation(s)", `active_runs` 0, no `data_dir` |
| `/api/profiles` | the public Nemotron profile only, `team: false` |
| gateway name in `/`, the two assets, `/api/runs`, `/api/tasks` | 0 hits |
| Real browser on the public URL (headless Chrome, 1440 px and 390 px; `public-render-r5-record.json`, `screens/`) | see the record file in this folder |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `/opt/attest/app.prev` (`releases/legacy-0.4.0-b27a1c070a85`, the 0.4.0
tree with its shared venv), restarts only `attest.service`, waits for strict health with version 0.4.0 and reads the digest back;
`bash rollback.sh --list` shows the three installed releases; `bash rollback.sh --to legacy-0.3.0-166cdcbd46a7` would select the
0.3.0 tree. The store backup `attest.db.bak-20261019b-full` is the state before this deployment; the schema only grew (four
added columns), which the 0.4.0 code tolerates (`SELECT *`, dict rows). Decommissioning (stop the service, remove its vhost) is
a different command, `decommission.sh --yes`, and was not run. The rollback was rehearsed under shims on the Aliyun host and
locally (`reports/attest-audit-repairs-2026-10-19/ops/`), not on this host.

## Files

`before-20261019b-20261019T084645Z.txt`, `after-20261019b-20261019T084738Z.txt`, `health-before-20261019b.json`,
`health-after-20261019b.json`, `build-20261019b.log`, `install-20261019b.log`, `public-render-r5-record.json`,
`screens/public-home-r5-{1440,390}.png`, `screens/public-run-r5-{1440,390}.png`.
