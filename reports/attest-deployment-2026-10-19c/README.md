# Deployment of revision 6 (version 0.6.0) to yungou, 19 Oct 2026, 10:58 to 11:04 UTC

What was deployed: revision 6 (`reports/attest-revision5-repairs-2026-10-19/README.md`: the seven findings of the revision-5
follow-up review; grounded infeasibility, evidence protocol 3, private diagnostics, journal tail repair, the 22-call cap at
every entry point, the registered provider profile, header-only team token with download tickets), the console client and
copy that go with it (asset stamp `20261019c`), the updated documentation (README, FREEZE with the revision-6 pin, TESTING,
PILOT, console notes) and the new evidence folders `reports/attest-revision5-review-2026-10-19/` (the review) and
`reports/attest-revision5-repairs-2026-10-19/` (repairs, suite log, bundle checks, the three-cell development-gateway batch). The
package digest recorded in every new bundle on the server is the pinned revision `b11ec0658845…` (36 sources, review commit
`da00f41a…`, pin commit `25dd5f6`). The deployment itself made no Nebius inference call; the verification afterwards did (see
the incident below). The store was not changed by the installer (39 rows before and after the install; the service added no
column this time).

Scope: the Attest service only (`attest.service`, its unit, its vhost, `/opt/attest`). The vhost changed in two places: a
`log_format attest_noquery` directive at the top of the file and `access_log /var/log/nginx/access.log attest_noquery;` in the
TLS server block, so that this host's access log records `$uri` without the query string (download tickets, R5-07, never sit
in it; same log file as before, this format for this host only). `nginx -t` ran with the new file in place before the switch
and nginx was reloaded once after the health check. The other sites on the host were not touched; the before and after
snapshots show the same services, listeners and nginx configuration apart from this file. Memory limit unchanged at
`MemoryMax=200M`; measured 38.8 MB resident after start.

## Build

- `python3 scripts/export_public.py --out dist/public --force` (10:54 and 10:57 UTC): staged export, 167 exported run
  directories verified with `attest check` (the three new batch bundles and the seven revision-5 batch bundles with complete
  evidence under their protocols, the rest as historical bundles), 0 failed, 0 scan hits, 4 evidence archives excluded by
  policy; the exported `attest/` digest equals the working tree's (`b11ec0658845…`). Review commits: code `da00f41`, pin `25dd5f6`.
- `deploy/yungou/build_bundle.sh` run from `dist/public` (`build-20261019c.log`): `app.tar.gz`, 7,781,197 bytes, 3,946 members,
  sha256 `d175901e886a2d4fd085627ebc5b5818edb00ad81d81dde07a6a50eb90755ff0`, `RELEASE.json` with 3,519 entries (version 0.6.0,
  package digest `b11ec0658845…`, label `0.6.0-b11ec0658845`), verified on the server with `sha256sum -c`.

## Procedure (UTC)

| Time | Step | Result |
| --- | --- | --- |
| 10:56 | health before | version 0.5.0, worker alive, ready, idle, "$0.0000 committed + 0 active reservation(s) within $2.00", 1,212 MB free (`health-before-20261019c.json`); releases `0.5.0-1e12d46217fb` (active), `legacy-0.4.0-b27a1c070a85` (previous), `legacy-0.3.0-166cdcbd46a7`; 39 store rows; `nginx -t` ok |
| 10:58 | upload of the bundle and of `install.sh`, `rollback.sh`, `decommission.sh`, `snapshot.sh`, `attest.service`, `attest.axiqo.xyz.conf` to `/var/tmp/attest-deploy/` | the first `scp` left the previous `app.tar.gz` in place (its digest check failed against the 0.5.0 archive); re-uploaded over `ssh`, after which `sha256sum -c` passed and every script and the vhost matched the local digests; the staged `attest.env` is identical to `/etc/attest/attest.env` |
| 10:58 | store backup | `/var/lib/attest/attest.db.bak-20261019c-full` via the SQLite backup API from `/opt/attest/app/venv/bin/python` (39 rows) |
| 10:58:48 | `snapshot.sh before-20261019c` | `before-20261019c-20261019T105848Z.txt` |
| 11:03 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019c.log`) | steps 01 to 15 all ok: preflight; extraction into a staging directory; every `RELEASE.json` entry verified; release directory `releases/0.6.0-b11ec0658845`; per-release venv with the pins; `compileall`, dependency import, `import attest` with version 0.6.0 and digest equal to `RELEASE.json`; `nginx -t` with the new vhost; symlink switch (`app.prev` now `0.5.0-1e12d46217fb`); unit unchanged, daemon-reload; restart; strict health (HTTP 200, version 0.6.0, worker alive, 1,086 MB free during the install); readback of 3,519 entries and of the digest through `/opt/attest/app`; nginx reloaded; the installer's keep-3 policy pruned `legacy-0.3.0-166cdcbd46a7` |
| 11:04:25 | `snapshot.sh after-20261019c` | `after-20261019c-20261019T110425Z.txt`; diff against before: the timestamp, memory, swap and load lines, `app -> releases/0.6.0-b11ec0658845`, `app.prev -> releases/0.5.0-1e12d46217fb`, the release list (0.6.0 added, legacy 0.3.0 gone) |
| 11:05 | health after | ok, version 0.6.0, worker alive, ready, idle, queue 0, "$0.0000 committed + 0 active reservation(s) within $2.00", 1,129 MB free (`health-after-20261019c.json`) |

## Verification after the install

| Check | Result |
| --- | --- |
| `readlink /opt/attest/app`, `/opt/attest/app.prev` | `releases/0.6.0-b11ec0658845`, `releases/0.5.0-1e12d46217fb` |
| `attest_revision()` through `/opt/attest/app/venv/bin/python` | `b11ec0658845e54d8917ac7a1cdbb32dddd1d16232fa0f377b08971a711837e9` over 36 files, version 0.6.0 (the revision-6 pin) |
| Server runtime | Python 3.12.15, SQLite 3.53.1 |
| `find /opt/attest/app/ -name '._*' \| wc -l` | 0 |
| `attest.service` | active, `MemoryMax=200M`, 38.8 MB resident, `ExecStart=/opt/attest/app/venv/bin/python -m uvicorn ...` |
| `/etc/attest/attest.env` | unchanged (9 lines); `ATTEST_PER_RUN_MAX_CALLS` and `ATTEST_DOWNLOAD_TICKET_SECONDS` not set, so the built-in defaults apply (22 calls, 600 s), both documented in `deploy/yungou/attest.env.example` |
| `nginx -T` | `log_format attest_noquery` defined once; the TLS server block of this host uses it; the other hosts' `access_log` lines unchanged |
| served `index.html`, `styles.css`, `app.js` | sha256 `785a8b259debc33b…`, `d7d84d52469e6ff3…` (unchanged), `033c5eafb6433666…`; stamp `20261019c` (6 references) |
| `https://attest.axiqo.xyz/` | 200 |
| `/api/health` (public) | version 0.6.0, worker alive, ready, no `data_dir` |
| `/api/profiles` | the public Nemotron profile only, `team: false` |
| `/api/runs?limit=200` | 39 rows at 11:05 (40 after the incident below); public row keys: `cost_committed_usd`, `cost_usd`, `created_at`, `error_code`, `error_public`, `finished_at`, `has_artifacts`, `model_calls`, `profile_label`, `provenance`, `provider`, `reasons`, `run_id`, `sandbox_ops`, `stage`, `started_at`, `status`, `summary`, `task_id`, `task_title`, `tokens_in`, `tokens_out`, `verdict`, `visibility`, `warnings`; no `requester`, `out_dir`, `error` or `error_detail` |
| gateway name in `/`, the two assets, the home and run DOMs | 0 hits |
| R5-07 on the public API | `POST /api/runs/{public run}/download-ticket` without the header token: 403; with `?token=junk`: 403; a public run's `bundle.zip` without any credential: 200 (73,227 bytes); `GET /api/runs?token=junk`: the same 39 public rows as anonymously (the query token is ignored); a `GET .../artifacts/PROOF.md?ticket=QUERYSTRING-PROBE-…` left no query string in `/var/log/nginx/access.log` (0 hits for the probe string; the logged line reads `GET /api/runs/.../artifacts/PROOF.md HTTP/2.0`) |
| Real browser on the public URL (headless Chrome, 1440 px and 390 px; `public-render-r6-record.json`, `screens/`) | home page renders with the hero replay, the "Built with" marks and the start panel; the run page `/runs/durationkit-units-001-20261015T185629796814Z` renders the VERIFIED seal; no gateway name, no `token=` in either DOM |

## Incident: an unapproved paid run started by a verification request (11:05:51 to 11:08:26 UTC)

One of the R5-07 verification requests was `POST /api/runs?token=junk` with the body
`{"task_id": "durationkit-units-001", "profile": "development"}`, sent to show that a query token does not open the development
profile. The request model `RunRequest` has no `profile` field (unknown fields are ignored) and its `provider` defaults to
`nebius`, so the console treated the request as what it was syntactically: an anonymous visitor starting a public Nemotron run
within the visitor quota, which is the console's documented purpose. The run `durationkit-units-001-20261019T110551450266Z`
was admitted at 11:05:51 UTC (`judge-demo` profile, provider `nebius`, public), reached the implementer stage and had made
16 model calls when it was stopped at 11:08:24 UTC by `systemctl restart attest` (only the Attest service; the restart is the
documented way to interrupt a run, and the restart reconciliation of revision 4 and 5 finalises the row from its ledger
journal). Result: row status `error`, stage `interrupted`, `error_code interrupted`, public text "the run was interrupted by a
service restart before completion; reference 0ae6d1dd195e", committed cost **$0.055226** read from the journal (16 call
records, 0 open reservations), `has_artifacts` true (the partial run directory). The daily budget line now reads "$0.0552
committed + 0 active reservation(s) within $2.00".

This spend was not approved by the owner and was caused by the verification step, not by a user or by a defect in the
deployed code. The row stays in the public history as recorded. Follow-up, not deployed in this release: make `RunRequest`
reject unknown fields (`extra = "forbid"`) and require `provider` explicitly, so that a malformed client request answers 422
instead of starting a paid run; verify admission rules offline (`tests/test_audit_console.py`) or with GET requests only.

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `/opt/attest/app.prev` (`releases/0.5.0-1e12d46217fb`, with its own venv),
restarts only `attest.service`, waits for strict health with version 0.5.0 and reads the digest back; `bash rollback.sh --list`
shows the installed releases (`0.5.0-1e12d46217fb`, `0.6.0-b11ec0658845`, `legacy-0.4.0-b27a1c070a85`). The store backup
`attest.db.bak-20261019c-full` is the state before this deployment; the schema did not change in this release. Decommissioning
is a different command (`decommission.sh --yes`) and was not run. The rollback was rehearsed under shims (revision 5), not on
this host.

## Files

`before-20261019c-20261019T105848Z.txt`, `after-20261019c-20261019T110425Z.txt`, `health-before-20261019c.json`,
`health-after-20261019c.json`, `build-20261019c.log`, `install-20261019c.log`, `public-render-r6-record.json`,
`screens/public-home-r6-{1440,390}.png`, `screens/public-run-r6-{1440,390}.png`.
