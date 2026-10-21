# Deployment of 0.10.2 (console corrections) to yungou, 21 Oct 2026, 04:57 UTC

What was deployed: version 0.10.2, the package of code commit `7c48b3f` (published as `3d3ffeab098e`; `FREEZE.md`, "The 0.10.2 pin"),
built from a clean worktree of the pin record `681f7cb`, which carries that package unchanged. It corrects the console page in three places
and changes no server code:
- The page named Nemotron 3.5 Lightning as the summary model, but no recorded run called it (`METHOD.md` lists the summary role as not
  used). The page now names Nemotron 3 Ultra and Super only.
- The architecture said `attest_revision 166cdcbd` was recorded in every bundle of "the frozen evaluation". Since 0.10.1 the page shows
  the 21 Oct evaluation first, so it now names both: `7e72364f` (21 Oct) and `166cdcbd` (17 Oct).
- The home page counted only the newest 50 runs, the list API's default page, so production's ticker read "50 recorded runs" while the
  store held 74. The page now asks for up to the server's cap of 200 rows and says "latest" if a list ever fills it.

The asset stamp moves to `20261021a` because `app.js` changed. The same commits make four console tests independent of the host's free
disk space. Clean checkouts of `7c48b3f` pass all 499 tests offline on macOS (0 skipped), normally and with `shutil.disk_usage` patched to
report 1 % free (`suites/`), with credentials absent, a new empty HOME and the network blocked. The Linux run of `2ac80fb` (0.10.1) was not
repeated.

Scope and method as for 0.10.1:
- Only the Attest service changed. `install.sh`, `rollback.sh`, `snapshot.sh`, `decommission.sh`, the unit and the vhost are byte-identical
  to the 0.10.1 deployment, and nginx was not reloaded.
- The other services were untouched. The before and after snapshots differ only in the time, memory, swap, disk and load lines and in
  the release list.
- Afterwards, only read-only checks ran: GET requests, a browser that aborts every other request, and read-only SSH. No inference call.

## Build and procedure (UTC; `deploy-0102-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` ran from a clean worktree of `681f7cb` (detached, no local change). It produced `app.tar.gz` (sha256
  `10eb7efee2ac9c82e6f7a417431c7a9240cb42f8a39e97c2f67e90cde5faddd5`) and `RELEASE.json` with 4,742 entries (version 0.10.2, label
  `0.10.2-6104fd89f66a`).
- The nine files (the bundle, the four deployment scripts, the unit, the vhost, `deploy-0102-server.sh` and `readback.sh`) went up as
  one ustar archive. `sha256sum -c upload.sha256` passed on the host for all nine.

| Time | Step | Result |
| --- | --- | --- |
| 04:57:05 | digests; `snapshot.sh before-20261021b`; idle check | all `OK`; version 0.10.1, busy false, queue 0, no current run, 0 holds |
| 04:57 | store backup | `/var/lib/attest/attest.db.bak-20261021b-full` (74 rows, 0 holds; sha256 `5f2fd04a…`) and `/var/backups/attest-data-20261021b.tgz` (535,419 bytes; sha256 `3647bdd6…`) |
| 04:57:08 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261021b.log`) | install complete; 4,742 entries verified in place; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 31076 in `/system.slice/attest.service`, started 04:57:26; vhost unchanged, nginx not reloaded; keep-3 pruned `0.9.0-ab5b1705ae2b` and kept `0.10.0`, `0.10.1`, `0.10.2` |
| 04:57:30 | `snapshot.sh after-20261021b`; health | `app -> releases/0.10.2-6104fd89f66a`, `app.prev -> releases/0.10.1-53a9b7c39a96`; version 0.10.2, worker alive, idle, queue 0; `reconciliation` {0 holds, accepting runs, not failed closed}; `startup` {0 reconciled, 0 deduplicated, 0 holds repaired, recovery not failed} |
| after the install | rollback readiness (read-only, nothing switched) | the 0.10.1 release in place: all 4,716 `RELEASE.json` entries equal on disk (version 0.10.1, digest `53a9b7c3…`); its interpreter imports the package and its dependencies |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261021b.txt`, 04:57:33) | unit active, MainPID 31076; package 0.10.2, digest `6104fd89f66a…` over 37 files; systemd `MemoryAccounting=yes`, `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, both fail counters 0, `oom_kill 0`, resident 52,292 kB; 74 store rows, none queued or running; **0 open reconciliation holds**, accepting runs, not failed closed; the other services active; `nginx -t` successful |
| Store | 74 rows before (the backup) and after; the 34 rows imported by 0.10.1 still name folders in the 0.10.1 release directory, which stays as the rollback target (the known limitation in `reports/attest-deployment-2026-10-21/README.md`: two more installs would prune it) |
| Queue, reservations, budget | queue 0, 0 active reservations; $1.4319 committed on this UTC day, $0.5681 of the $2.00 cap remaining, as after 0.10.1 |
| Disk | 3,318,849,536 bytes free of 14,483,959,808 (22.91 %); the low-disk threshold (7 %, 500 MB) unchanged |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261021a`, `styles.css?v=20261021a` byte-identical to the release; `/api/health` version 0.10.2 with `reconciliation` {0 holds open, accepting runs, `fail_closed` false}; the public Nemotron profile only; 74 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; a recorded run's page served; the gateway's name in none of the responses |
| The corrected counts | `GET /api/runs?limit=200`: 74 rows, 10 VERIFIED, 19 NEEDS HUMAN, 45 others (20 ERROR, 22 BASELINE, 2 NO CHANGE, 1 INFEASIBLE); the home page shows "74 recorded runs, 10 VERIFIED, 19 NEEDS HUMAN, 45 other verdicts" (recorded read-only for the demonstration film the same morning) |
| Real Chrome on the public URL (`browser-production-headless-5-widths.json`, finished 05:14:52; `scripts/console_layout_audit.py --base`, every request that is not a GET aborted inside the browser) | headless sweep at 320, 390, 768, 1024 and 1440 px over the home page (every panel open, live mode selected, the confirmation open, the replay finished) and the case file of the recorded runs on every tab with every detail open, a missing run and a simulated API failure: 515 states, no element or text wider than the viewport, no clipped control, no page that scrolls sideways; 1,456 GET requests and no other request; in live mode the Run button opened the confirmation at every width and sent nothing |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.10.1-53a9b7c39a96`. The target was checked in place; nothing was
switched. The rollback restarts only `attest.service` and leaves the unit as it is; 0.10.1 runs the same server code and reads the store
as 0.10.2 leaves it. `attest.db.bak-20261021b-full` and `/var/backups/attest-data-20261021b.tgz` hold the state before this deployment.
The rollback was not exercised, because switching would restart the public service twice.

## Files

`deploy-0102-server.sh` (the 0.10.1 script with the new stamp), `readback.sh` (read-only, unchanged), `public_readonly_checks.py` (the
asset stamp updated) and `public-readonly-checks.json`, `before-20261021b-20261021T045705Z.txt`, `after-20261021b-20261021T045730Z.txt`,
`health-before-20261021b.json`, `health-after-20261021b.json`, `deploy-0102-server.log`, `install-20261021b.log`,
`readback-after-deploy-20261021b.txt`, `browser-production-headless-5-widths.json`, and `suites/` (the clean macOS runs of `7c48b3f` with
their drivers and the free-space patch).
