# Deployment of revision 8 (version 0.8.0) to yungou, 19 Oct 2026, 20:42 to 20:43 UTC

What was deployed: revision 8 (`reports/attest-revision7-repairs-2026-10-19/README.md`): the memory limit made effective on the
host's systemd 219 (`MemoryLimit=` and a memory-plus-swap limit, read back from systemd and the kernel after the restart),
phase-aware transport (bounded resends of requests that never left this machine, no replay of uncertain ones, accepted operation
ids kept, runs stopped for reconciliation), the explicit start (`X-Attest-Confirm: start-run`, the console's confirmation step, and
its refusal in an automated browser on the public host), inference costs labelled by service, the phone layout and the export
privacy repair, with the updated documentation and the new evidence folders. The release was built from a clean checkout
(`git worktree add --detach`) of the review repository at `3be63fa`, the revision-8 pin record (code commit `5177cf4`, package
digest `ed41f4c95bd1…` over 37 sources; `FREEZE.md`).

Scope: the Attest service only (`attest.service`, its unit, `/opt/attest`). The unit changed (the memory directives); the vhost did
not, so nginx was not reloaded. The other services on the host were not touched: the before and after snapshots differ only in
the timestamp, memory, swap, disk and load lines and in the release links. No Docker component was needed; nothing was changed on
the Aliyun host. Every check of production was read-only (GET requests, a browser that blocked every other request before it was
sent, read-only commands over SSH); the memory drill ran in a temporary unit of its own with a scratch store. No POST, PUT or
DELETE request was sent to production, and neither the deployment nor its verification made an inference call.

## The host before the deployment

yungou was unreachable twice in the hour and a half before the deployment. Nothing had been installed yet; the events are
recorded because they bear on the console's availability. From `/var/log/messages` and the nginx access logs, read-only:

- **19:02:11 to 19:18:28 UTC, network.** The host kept running, but its own outbound connections failed with `No route to host`
  (the `codex-api-relay` unit's SSH to the Aliyun host, restarted every 5 to 6 s, logged it 160 times), and nginx logged no
  inbound request from 19:03 to 19:17. The cause is not established. The host's hourly subscription refresh finished at 19:00:19,
  104 s before the first failure; it downloads a file with curl and writes under its own directory (`ProtectSystem=full`), runs no
  proxy and changes no route, and the host has no proxy process or tunnel device. The memory drill of this pass ran from 18:50 to
  18:52 UTC in its own memory cgroup, and the kernel killed only the drill process (`CONSTRAINT_MEMCG`). No link was found.
- **19:56:29 UTC, power-off from outside the guest.** The QEMU guest agent logged `guest-ping` and `guest-shutdown` (a request
  from the hypervisor side, i.e. the provider or its control panel; nothing inside the guest initiated it), and systemd powered
  the host off. It booted again at 20:35:01 UTC. DHCPv6 renewals had gone unanswered since 19:43 UTC (IPv6 only; the IPv4 address
  is static). journald keeps the current boot only; `/var/log/messages` holds the shutdown.
- After the boot every service came back by itself (`attest` 0.7.0 healthy, nginx, the relay, Docker, fail2ban, firewalld, sshd,
  crond). `auditd` (no `/var/log/audit` directory) and `kdump` (no memory reserved for a crash kernel) failed to start, exactly as
  on the boot of 7 Oct; they are not related to Attest.

The deployment was started after the host had been up for seven minutes, from a detached shell on the host (`nohup setsid`), so
that a dropped SSH session could not interrupt it.

## Build

- `deploy/yungou/build_bundle.sh` from the clean worktree of `3be63fa` (`build-20261019e.log`): `app.tar.gz`, 8,476,725 bytes,
  4,350 members, sha256 `474cd4d97c697597eee83c372d061ca8eb4c5684f34afa1d7734f6ecda8633a2`; `RELEASE.json` with 3,862 entries
  (version 0.8.0, package digest `ed41f4c95bd1708d47aa8af46421acf4e82a27f31bbb612fe60bb7ab2738ea98`, label `0.8.0-ed41f4c95bd1`);
  no secret-like path, screenshot, snapshot or AppleDouble file.
- Uploaded over SSH with the installer, the rollback, decommission and snapshot scripts, the unit, the vhost and the server-side
  steps (`deploy-r8-server.sh`); `sha256sum -c upload-20261019e.sha256` passed on the host for all eight files, and the scripts,
  unit and vhost are identical to the commit's files.

## Procedure (UTC; `deploy-r8-server.log` is the complete output)

| Time | Step | Result |
| --- | --- | --- |
| 20:42:29 | digests; `snapshot.sh before-20261019e`; idle check | all eight files `OK`; `before-20261019e-20261019T204229Z.txt`; version 0.7.0, busy false, queue 0, no current run (`health-before-20261019e.json`) |
| 20:42 | store backup | `/var/lib/attest/attest.db.bak-20261019e-full` through the SQLite backup API (40 rows) and `/var/backups/attest-data-20261019e.tgz` (409,139 bytes, the whole data directory) |
| 20:42:34 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019e.log`) | steps 01 to 16 all ok: preflight; extraction and verification of all 3,862 `RELEASE.json` entries (no unlisted file, no env file); release directory `releases/0.8.0-ed41f4c95bd1` with its own virtualenv; compile, dependency and package checks with the release's interpreter (version 0.8.0, digest equal to `RELEASE.json`); unit rendered with `MemoryLimit` and `MemoryMax` 200M and the memory-plus-swap limit 209,715,200 bytes; vhost unchanged; switch; daemon-reload; restart; strict health (HTTP 200, version 0.8.0, worker alive); **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 2241 in `/system.slice/attest.service`; readback of the 3,862 entries and of the digest through `/opt/attest/app`; nginx reload not needed; the keep-3 policy pruned `legacy-0.4.0-b27a1c070a85` |
| 20:42:50 | `snapshot.sh after-20261019e` | `after-20261019e-20261019T204250Z.txt`; `app -> releases/0.8.0-ed41f4c95bd1`, `app.prev -> releases/0.7.0-f836cfd0154f` |
| 20:42:57 | health after (`health-after-20261019e.json`) | ok, version 0.8.0, worker alive, ready, idle, queue 0, startup reconciled 0, "$0.0552 committed + 0 active reservation(s) within $2.00" |

The installer installs `/etc/attest/attest.env` from the staged copy. The two files have the same sha256 (compared by digest; the
contents were not read), so the service's configuration did not change.

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback on the host, 20:49 UTC (`reports/attest-revision7-repairs-2026-10-19/memory/readback-after-deploy.txt`) | unit active, MainPID 2241; `app -> releases/0.8.0-ed41f4c95bd1`, `app.prev -> releases/0.7.0-f836cfd0154f`; package 0.8.0, digest `ed41f4c95bd1…` over 37 files; systemd `MemoryAccounting=yes MemoryLimit=209715200`; cgroup `memory.limit_in_bytes` and `memory.memsw.limit_in_bytes` 209,715,200, usage 41.8 MB, peak 43.5 MB, failcnt 0, `oom_kill 0`; the main process in `/system.slice/attest.service`, 48.9 MB resident, no swap; 40 store rows, none queued or running; the other services active; `nginx -t` ok; host memory 265 MB available |
| Application OOM drill on the deployed release, 20:50:53 UTC (`reports/attest-revision7-repairs-2026-10-19/memory/drill-app-run-1.txt`) | the deployed interpreter and code (`/opt/attest/app`) in a temporary unit with the same mechanism at 128M, a scratch store and no credentials: the process recorded a Nemotron-profile run in flight (an open $0.0175 reservation and an accepted Sandboxes operation in its ledger journal; nothing sent anywhere) and allocated until the kernel's memory-cgroup OOM killer ended it at the memory-plus-swap limit (`memory+swap: usage 131072kB, limit 131072kB`, `CONSTRAINT_MEMCG`, only the drill's process); systemd restarted it after 3 s; the new process settled the run as `interrupted`, kept $0.0175 committed and named the operation `…d311` as accepted but never read. `attest.service` kept MainPID 2241 throughout; the temporary unit and its files were removed |
| Budget state | `/api/health`: daily cap $2.00, per-run cap $0.50; $0.0552 committed on this UTC day (the unapproved run started by a verification probe on 19 Oct, $0.055226 across 16 model calls; `reports/attest-deployment-2026-10-19c/README.md`), 0 active reservations, $0.00 reserved, 0 active runs, $1.9448 remaining |
| Public GET checks (`public-readonly-checks.json`) | `/`, `/static/app.js?v=20261019e` and `/static/styles.css?v=20261019e` 200 and byte-identical to the commit's files; `/api/health` version 0.8.0, worker alive, ready, idle, queue 0, no `data_dir`; `/api/profiles` the public Nemotron profile only, `team: false`; `/api/runs?limit=200` 40 rows, no `requester`, `out_dir`, `error` or `error_detail` key; `/api/openapi.json`: `RunRequest.additionalProperties` false, `required` [`provider`, `task_id`], no provider default, and the `X-Attest-Confirm` header documented on `POST /api/runs`; a run page served as the console page; the gateway's name in none of the responses |
| Real Chrome on the public URL (Playwright with the installed Chrome; every request that is not a GET is aborted inside the browser before it is sent, service workers blocked; `browser-production-*.json`) | **Phone and desktop widths, every state.** A visible Chrome window at 390 px (mobile emulation: mobile viewport, touch, scale 3) and 1440 px, and headless sweeps at 320, 360, 375, 390, 414, 768, 1024 and 1440 px: 14 runs (up to three per verdict, longest identifiers first), 91 states per width: the home page, every disclosure open, live mode, the confirmation open and pressed; every tab of every run with every disclosure open; a run that does not exist; the case file with every API call answered 503 inside the browser. **No element or text wider than the viewport, no sideways-scrolling document and no page error at any width** (182 states in the window, 726 in the full sweep). **No request other than GET left the browser**: 521 in the window and 2,051 in the full sweep, and the guard had nothing to abort; in live mode the Run button opened the confirmation and sent nothing, and the confirmation's button was refused by the page itself ("Live runs are not started from an automated browser on this host. Open the console in a regular browser to start one.") before any request existed |
| What the browser checks found | **At 1024 px the case file's Activity and Files tabs could not be pressed** (in the full sweep 2 of the 70 tab presses at 1024 px, both on `durationkit-units-001-20261019T110551450266Z`; the presses on the other runs' tabs succeeded): the Guide, which opened by itself on windows wider than 900 px, lay over them (panel at x 640 to 1000, y 599 to 876 in a 1024 x 900 window; tabs at y 632 to 676), and scrolling far enough to clear it made the compact decision bar cover the tabs instead; closing the Guide was the only way through. The first headless sweep had stopped on the same press (the audit then raised instead of recording; repeats at 414 px, alone and after 390 px, and the full sweep located it at 1024 px). Two short-lived "clipped" readings of a seal at 390 px came from its 0.55 s stamp animation (the audit now waits for it). Screenshots of the same pages at 1024 px also showed the decision card's text squeezed to about 80 px between its seal and its buttons and the overview's evidence table in a sideways scroll, and two error states were wrong: with every API call failing the start form said "No sample tasks are configured", and on phones the collapsed workspace rail stretched into an empty band on short pages. All five are repaired in 0.8.1 (`reports/attest-deployment-2026-10-19f/`) |
| Screenshots (`screens/`, viewport captures; `shots.json` lists them, produced by `evidence_shots.py` with the same guard, no request other than GET) | `home-1440.png`; `confirm-1440.png` and `confirm-390.png` (the confirmation: Nemotron inference up to $0.50 reserved against the $2.00 cap, Sandboxes and Tavily metered separately); `confirm-refused-390.png` (the refusal in an automated browser); `hold-1440.png` (a NEEDS HUMAN case file, recorded 15 Oct); `hold-tests-open-390.png` (its counterexample with every disclosure open); `api-failure-1440.png` (every API call failing: "This run could not be loaded" and "Service unreachable", next to the start form's wrong "No sample tasks are configured"); `missing-run-390.png` (the empty band under the rail) |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `/opt/attest/app.prev` (`releases/0.7.0-f836cfd0154f`, version 0.7.0, package
`f836cfd0…`, with its own virtualenv), restarts only `attest.service`, waits for strict health with version 0.7.0 and reads the
digest back; `bash rollback.sh --list` shows the installed releases (`0.6.0-b11ec0658845`, `0.7.0-f836cfd0154f`,
`0.8.0-ed41f4c95bd1`). The rollback keeps the revision-8 unit, so the memory limit stays in force under 0.7.0 as well. The store
schema did not change in this release (`attest/app/db.py` has no new table or column since 0.7.0), so 0.7.0 reads the same store;
`attest.db.bak-20261019e-full` and `/var/backups/attest-data-20261019e.tgz` hold the state before this deployment. The rollback
was rehearsed under shims, not run on this host.

## Files

`before-20261019e-20261019T204229Z.txt`, `after-20261019e-20261019T204250Z.txt`, `health-before-20261019e.json`,
`health-after-20261019e.json`, `build-20261019e.log`, `upload-20261019e.sha256`, `deploy-r8-server.log`, `install-20261019e.log`,
`public_readonly_checks.py` and its output `public-readonly-checks.json`, `browser-production-headed-390-1440.json`, `browser-production-headless-all-widths.json`, `browser-production-headless-414-alone.json`, `browser-production-headless-390-414-rerun.json`, `browser-headless-run1-crashed.log` (the first sweep, stopped by the unpressable tab), `evidence_shots.py`, `screens/` (eight viewport screenshots and `shots.json`).
