# Deployment of revision 7 (version 0.7.0) to yungou, 19 Oct 2026, 15:28 to 15:31 UTC

What was deployed: revision 7 (`reports/attest-revision6-repairs-2026-10-19/README.md`: the constrained witness language
`attest-witness/1` and evidence protocol 4, strict admission requests, explicit recorded-evidence corpora, and the export
fixes found by the final-tree suite runs) with the updated documentation (README, FREEZE with the revision-7 pin, TESTING, PILOT,
console notes) and the new evidence folders `reports/attest-revision6-review-2026-10-19/` and
`reports/attest-revision6-repairs-2026-10-19/`. The console's static assets are unchanged since revision 6 (stamp `20261019c`). The
package digest recorded in every new bundle on the server is the pinned revision `f836cfd0154f…` (37 sources); the release was
built from a clean checkout of the review repository at commit `fdf5099` (the pin record; code commit `a95e261`).

Scope: the Attest service only (`attest.service`, its unit, its vhost, `/opt/attest`). The unit and the vhost were unchanged, so
nginx was not reloaded (`nginx -t` passed before and after). The other services on the host were not touched; the before and after
snapshots differ only in the timestamp, memory, swap and load lines and in the release links. 44.6 MB resident after start. No
Docker component was needed; nothing was changed on the Aliyun host.

Memory limit, corrected: the unit carries `MemoryMax=200M`, but this host runs systemd 219, which predates that directive and
ignores it; `systemctl show attest` reports `MemoryLimit=18446744073709551615` (no limit). So no memory limit has been enforced on
the service since the first deployment, although the deployment records of 19 Oct (`attest-deployment-2026-10-19b`, `-19c`) state
the 200M limit as if it applied. This release does not change the unit; the fix (adding `MemoryLimit=__MEMORY_MAX__` to
`deploy/yungou/attest.service`, which systemd 219 honours and newer versions accept, and checking the effective limit after the
restart) changes how the service is confined on a shared host and is left for the owner to approve.

Verification was read-only: GET requests to the public site and API, a headless browser that loads the public pages (it sends
only GET requests without a team token), and read-only commands on the host over SSH. No POST, PUT or DELETE request was sent to
production, and no inference was made by the deployment or its verification.

## Build

- The export (`python3 scripts/export_public.py --out dist/public --force`) verified all 175 exported bundles with `attest check`,
  found no scan hit and no exported file that git would ignore; a second export changed nothing.
- `deploy/yungou/build_bundle.sh` run from a clean `git worktree` of `fdf5099` (`build-20261019d.log`): `app.tar.gz`,
  8,138,948 bytes, 4,163 members, sha256 `49acef4d97595727d27d3f8a34e8ab9dd4bcb0098734a4a0a4e818c4aaa8394e`, `RELEASE.json` with
  3,705 entries (version 0.7.0, package digest `f836cfd0…`, label `0.7.0-f836cfd0154f`). The bundle, the installer, the rollback,
  decommission and snapshot scripts, the unit and the vhost were uploaded over SSH and their sha256 verified on the host.

## Procedure (UTC)

| Time | Step | Result |
| --- | --- | --- |
| 15:27 | health before (`health-before-20261019d.json`) | version 0.6.0, worker alive, idle, queue 0, "$0.0552 committed + 0 active reservation(s) within $2.00", 1,125 MB free; releases `0.6.0-b11ec0658845` (active), `0.5.0-1e12d46217fb` (previous), `legacy-0.4.0-b27a1c070a85`; 40 store rows; `nginx -t` ok |
| 15:28 | upload and digest check | `sha256sum -c` of the bundle ok; scripts, unit and vhost identical to the commit's; the staged `attest.env` identical to `/etc/attest/attest.env` |
| 15:28 | store backup | `/var/lib/attest/attest.db.bak-20261019d-full` via the SQLite backup API (40 rows) |
| 15:28:49 | `snapshot.sh before-20261019d`; idle check | `before-20261019d-20261019T152849Z.txt`; busy false, queue 0, no current run |
| 15:29 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019d.log`) | steps 01 to 15 all ok: preflight; extraction and verification of every `RELEASE.json` entry; release directory `releases/0.7.0-f836cfd0154f` with its own virtualenv; compile, dependency and package import checks (version 0.7.0, digest equal to `RELEASE.json`); `nginx -t`; symlink switch; unit unchanged; restart; strict health (HTTP 200, version 0.7.0, worker alive); readback of 3,705 entries and of the digest through `/opt/attest/app`; nginx reload not needed; the keep-3 policy pruned `0.5.0-1e12d46217fb` |
| 15:30:01 | `snapshot.sh after-20261019d` | `after-20261019d-20261019T153001Z.txt`; `app -> releases/0.7.0-f836cfd0154f`, `app.prev -> releases/0.6.0-b11ec0658845` |
| 15:30 | health after (`health-after-20261019d.json`) | ok, version 0.7.0, worker alive, ready, idle, queue 0, startup reconciled 0, "$0.0552 committed + 0 active reservation(s) within $2.00" |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| `readlink /opt/attest/app`, `/opt/attest/app.prev` | `releases/0.7.0-f836cfd0154f`, `releases/0.6.0-b11ec0658845` |
| `attest_revision()` through `/opt/attest/app/venv/bin/python` | `f836cfd0154faa878214976dab4fcc0a982dde38343e3944afceb8fc7f3336d3` over 37 files, version 0.7.0 (the revision-7 pin) |
| Runtime and store | Python 3.12.15, SQLite 3.53.1; 40 rows, 26 columns (schema unchanged); no AppleDouble file in the release; the rehearsal shims are executable in the release (export fix) |
| Public GET checks (`public-readonly-checks.json`) | `/`, `/static/app.js`, `/static/styles.css` 200 and byte-identical to the commit's files; `/api/health` version 0.7.0, worker alive, ready, idle, no `data_dir`; `/api/profiles` the public Nemotron profile only, `team: false`; `/api/runs?limit=200` 40 rows, no `requester`, `out_dir`, `error` or `error_detail` key; gateway name in none of the eight responses |
| Strict admission, as published (`/api/openapi.json`) | `RunRequest.additionalProperties` false; `required` [`provider`, `task_id`]; `provider` has no default and no enum. The rejection behaviour itself (422 without a row, queue entry, reservation or provider) is verified by the local tests only (`reports/attest-revision6-repairs-2026-10-19/console/`); no production POST was sent to test it |
| Headless Chrome on the public URL, 1440 px and 390 px (`screens/`) | home page and the run page `/runs/durationkit-units-001-20261015T185629796814Z` render; the run page shows the VERIFIED seal; no gateway name, `token=` or `ticket=` in either DOM; the service stayed idle with no new run afterwards. The 390 px home screenshot shows text running past the right edge, exactly as the revision-6 screenshot of 19 Oct 11:05 UTC does (the assets are unchanged); not investigated in this pass |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `/opt/attest/app.prev` (`releases/0.6.0-b11ec0658845`, version 0.6.0, package
`b11ec065…`, with its own virtualenv), restarts only `attest.service`, waits for strict health with version 0.6.0 and reads the
digest back; `bash rollback.sh --list` shows the installed releases (`0.6.0-b11ec0658845`, `0.7.0-f836cfd0154f`,
`legacy-0.4.0-b27a1c070a85`). The store backup `attest.db.bak-20261019d-full` is the state before this deployment; the schema did
not change in this release, and 0.6.0 reads the same store. Decommissioning is a different command (`decommission.sh --yes`) and
was not run. The rollback was rehearsed under shims (revision 5), not on this host.

## Files

`before-20261019d-20261019T152849Z.txt`, `after-20261019d-20261019T153001Z.txt`, `health-before-20261019d.json`,
`health-after-20261019d.json`, `build-20261019d.log`, `install-20261019d.log`, `public-readonly-checks.json`,
`screens/public-home-r7-{1440,390}.png`, `screens/public-run-r7-{1440,390}.png`.

## Correction, 19 Oct 2026 (revision 8)

The 390 px observation in the verification table came from the capture method, not from the page. Chrome's headless command
line (`--headless=new --window-size=390,...`) lays the page out wider than a 390 px window and crops the image, so text seemed to
run past the right edge; repeating that capture on the same version reproduces the effect. Rendered with mobile emulation
(Playwright with the installed Chrome, a 390 px mobile viewport), the public home page and run page of this version had no element
and no text wider than the viewport. The console did overflow at narrower widths and in some run views (the logo row, the start
form and the capability figures at 320 px; long error texts, counterexample names and the decision buttons at 320 to 390 px);
revision 8 repairs those (`reports/attest-revision7-repairs-2026-10-19/console/`). The memory limit this record reports as not
enforced is enforced from revision 8 on (`reports/attest-revision7-repairs-2026-10-19/memory/`).
