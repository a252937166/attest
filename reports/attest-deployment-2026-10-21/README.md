# Deployment of 0.10.1 (the console release after the Nemotron validation) to yungou, 21 Oct 2026, 03:56 UTC

What was deployed: version 0.10.1, the package of code commit `2ac80fb` (published as `c38e9c110e21`; `FREEZE.md`, "The 0.10.1 pin and
the published history"), built from a clean worktree of the pin record `73abb06`, which carries that package unchanged. It changes no server code. The console page's evaluation section now reports the Nemotron re-evaluation of
21 October 2026 (`reports/attest-evaluation-2026-10-21-nebius-r10/README.md`) and keeps the frozen evaluation of 17 October inside a
collapsed section. The unit's `ATTEST_IMPORT_DIRS` also lists that evaluation's 32 runs and the 2 smoke-test runs
(`reports/attest-validation-2026-10-21-nebius-r10/smoke/`), so the console serves them. `attest/__init__.py` and `pyproject.toml` say
0.10.1. Package `53a9b7c39a96…` (37 sources). Asset stamp `20261020b`, unchanged: `app.js` and `styles.css` did not change. Clean
checkouts of `2ac80fb` pass all 498 tests offline on macOS (0 skipped) and on Linux (30 skipped; `suites/`), with credentials absent, a
new empty HOME and the network blocked. The Linux suite ran in a container on the Aliyun host, which has no part in the deployment.

Scope and method as before:
- Only the Attest service changed. `install.sh`, `rollback.sh`, `snapshot.sh`, `decommission.sh` and the vhost are byte-identical to the
  0.10.0 deployment, and nginx was not reloaded. The unit template differs only in the import list.
- The other services were untouched. The before and after snapshots differ only in the time, memory, swap, disk and load lines and in
  the release list.
- Afterwards, only read-only checks ran: GET requests, a browser that aborts every other request, and read-only SSH. No inference call.

## Build and procedure (UTC; `deploy-0101-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` ran from a clean worktree of `73abb06` (detached, no local change). It produced `app.tar.gz` (sha256
  `3d1347d7ba29d2b408f939bcfb2919fced56d9e242f2e5e81fb77b19b2ecfa63`) and `RELEASE.json` with 4,716 entries (version 0.10.1, label
  `0.10.1-53a9b7c39a96`).
- The nine files (the bundle, the four deployment scripts, the unit, the vhost, `deploy-0101-server.sh` and `readback.sh`) went up as
  one ustar archive. `sha256sum -c upload.sha256` passed on the host for all nine.

| Time | Step | Result |
| --- | --- | --- |
| 03:56:26 | digests; `snapshot.sh before-20261021`; idle check | all `OK`; version 0.10.0, busy false, queue 0, no current run, 0 holds |
| 03:56 | store backup | `/var/lib/attest/attest.db.bak-20261021-full` (40 rows, 0 holds; sha256 `cba1f32a…`) and `/var/backups/attest-data-20261021.tgz` (491,227 bytes; sha256 `489cb257…`) |
| 03:56:31 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261021.log`) | install complete; 4,716 entries verified in place; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 30025 in `/system.slice/attest.service`, started 03:56:54; vhost unchanged, nginx not reloaded; keep-3 kept `0.9.0`, `0.10.0`, `0.10.1` |
| 03:56:57 | `snapshot.sh after-20261021`; health | `app -> releases/0.10.1-53a9b7c39a96`, `app.prev -> releases/0.10.0-7e72364f135c`; version 0.10.1, worker alive, idle, queue 0; `reconciliation` {0 holds, accepting runs, not failed closed}; `startup` {0 reconciled, 0 deduplicated, 0 holds repaired, recovery not failed} |
| after the install | rollback readiness (read-only, nothing switched) | the 0.10.0 release in place: all 4,076 `RELEASE.json` entries equal on disk (version 0.10.0, digest `7e72364f…`) |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261021.txt`, 03:57:00) | unit active, MainPID 30025; package 0.10.1, digest `53a9b7c39a96…` over 37 files; systemd `MemoryAccounting=yes`, `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, both fail counters 0, `oom_kill 0`, resident 49,872 kB; 74 store rows, none queued or running; **0 open reconciliation holds**, accepting runs, not failed closed; the other services active; `nginx -t` successful |
| Store (the backup and the live store compared read-only, 04:18) | 40 rows before. After start-up the store holds 74: the 40 rows of the backup, identical in every column, and the 34 recorded runs the unit now imports (32 evaluation cells and 2 smoke-test runs), all finished, $1.503242 committed between them. The installer does not modify the store, and an import never touches an existing row |
| Queue, reservations, budget | queue 0, 0 active reservations; **$1.4319 committed on this UTC day, $0.5681 of the $2.00 cap remaining** (see below) |
| Disk | 3,336,491,008 bytes free of 14,483,959,808 (23.04 %); the low-disk threshold (7 %, 500 MB) unchanged. Before this day's work the free share was 9.17 %; the Docker pruning is recorded in `reports/attest-validation-2026-10-21-nebius-r10/README.md` |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261020b`, `styles.css?v=20261020b` byte-identical to the release; `/api/health` version 0.10.1 with `reconciliation` {0 holds open, accepting runs, `fail_closed` false}; the public Nemotron profile only; 74 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; a recorded run's page served; the gateway's name in none of the responses |
| Real Chrome on the public URL (`browser-production-headless-5-widths.json`, finished 04:13:59; `scripts/console_layout_audit.py --base`, every request that is not a GET aborted inside the browser) | headless sweep at 320, 390, 768, 1024 and 1440 px over the home page (every panel open, live mode selected, the confirmation open, the replay finished) and the case file of the recorded runs on every tab with every detail open, a missing run and a simulated API failure: 515 states, no element or text wider than the viewport, no clipped control, no page that scrolls sideways; 1,458 GET requests and no other request; in live mode the Run button opened the confirmation at every width and sent nothing |

### The budget after the import

The console's cap is conservative on purpose (`BUDGET_POLICY` in `attest/app/db.py`): a run counts against every UTC day on which it was
queued, started, ran or finished. The 33 imported runs from 21 October are real Nemotron spending on the same account: $1.387089 for the
evaluation and $0.044771 for the second smoke test, $1.431860 in all (the health endpoint shows $1.4319). The first smoke test finished
on 20 October and counts there. A queued or running run reserves the full per-run cap of $0.50, so until 00:00 UTC on 22 October the
public console runs one job at a time and starts none once the day's committed cost passes $1.50. After that the full $2.00 is
available again. This is the policy working as written, not a fault: a cap that ignored recorded runs would understate what
the account spent that day.

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.10.0-7e72364f135c`. The target was checked in place; nothing was
switched. The rollback restarts only `attest.service` and leaves the unit as it is.
- 0.10.0 runs the same server code, so it reads the store as 0.10.1 left it.
- The two new import folders do not exist in the 0.10.0 tree. `attest/app/server.py` skips a missing import directory, so 0.10.0 starts
  and imports nothing from them.
- The 34 rows already imported stay in the store with their artifacts. Their stored folders are inside the 0.10.1 release directory
  (see below), which a rollback keeps.

`attest.db.bak-20261021-full` and `/var/backups/attest-data-20261021.tgz` hold the state before this deployment. The rollback was not
exercised, because switching would restart the public service twice.

## Known limitation: imported folders are stored inside the release that imported them

The server resolves each import directory before it stores a run's folder, and `/opt/attest/app` is a link to the active release.
So the 34 rows imported by 0.10.1 name folders under `/opt/attest/releases/0.10.1-53a9b7c39a96/`, not under `/opt/attest/app/`. The
35 rows imported earlier name `/opt/attest/app/…` and follow whichever release is active. The installer
keeps three releases. After three more installs it would remove the 0.10.1 directory, and those 34 rows would lose their artifacts:
the console would list them without a downloadable bundle. Nothing is affected today. The fix is to store the unresolved path, or to
re-point imported rows at start-up; this release does not change it.

## Files

`deploy-0101-server.sh` (the server-side steps; the 0.10.0 script with the new stamp), `readback.sh` (read-only, unchanged),
`public_readonly_checks.py` and `public-readonly-checks.json`, `before-20261021-20261021T035626Z.txt`,
`after-20261021-20261021T035657Z.txt`, `health-before-20261021.json`, `health-after-20261021.json`, `deploy-0101-server.log`,
`install-20261021.log`, `readback-after-deploy-20261021.txt`, `browser-production-headless-5-widths.json`, and `suites/` (the clean
macOS and Linux runs of `2ac80fb` with their drivers).
