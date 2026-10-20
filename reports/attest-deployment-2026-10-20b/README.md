# Deployment of 0.10.0 (revision 10) to yungou, 20 Oct 2026, 16:02 UTC

What was deployed: version 0.10.0 (`reports/attest-revision10-repairs-2026-10-20/README.md`): a run held for reconciliation keeps its hold
across restarts, the held state and its hold are written in one transaction and the service fails closed when that fails, start-up repairs a
missing hold and never reopens a cleared one, a resumed batch cannot bypass unresolved operations, an unreadable upstream answer stops the
run, and the console page shows when runs are paused. Asset stamp `20261020b`. Package `7e72364f135c…` (37 sources). Built from a clean
checkout of the pin record `f0c28c2`, which names code commit `775248c` (`FREEZE.md`); clean checkouts of `775248c` pass all 491 tests
offline (credentials absent, a new empty HOME, network blocked). A clean run of `f0c28c2` itself after the deployment failed one inventory
test that did not yet know the live run the record added; `c0ddb48` fixes that test (tests only) and is now the pin; the deployed package
is the pinned package. The store gains the one-hold-per-run index at start-up (created when no
earlier duplicate prevents it; production had no hold at all); 0.9.0 tolerates it, so a rollback needs nothing else.

Scope and method as before: the Attest service only; the unit template and the vhost byte-identical to the 0.9.0 deployment (nginx not
reloaded); the other services untouched (the snapshots differ only in the time, memory, swap, disk and load lines and in the release
list); nothing deployed on the Aliyun host (it ran the offline Linux suite in a container); read-only checks only afterwards (GET requests,
a browser that aborts every other request, read-only SSH); no inference call.

## Build and procedure (UTC; `deploy-0100-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` from the clean worktree of `f0c28c2`: `app.tar.gz`, sha256 `8dd8bbcca77bed87d1d2ddfa8e35c51fd5211bb6f09ce7f26fb07ce5fd0b53e3`,
  `RELEASE.json` with 4,076 entries (version 0.10.0, label `0.10.0-7e72364f135c`); `install.sh`, `rollback.sh`, `snapshot.sh`, `decommission.sh`,
  the unit template and the vhost byte-identical to the 0.9.0 deployment. The ten files went up as one ustar archive and `sha256sum -c
  upload.sha256` passed on the host for all ten.

| Time | Step | Result |
| --- | --- | --- |
| 16:01:40 | digests; `snapshot.sh before-20261020b`; idle check | all `OK`; version 0.9.0, busy false, queue 0, no current run, 0 holds |
| 16:01 | store backup | `/var/lib/attest/attest.db.bak-20261020b-full` (40 rows, 0 holds; sha256 `08bad681…`) and `/var/backups/attest-data-20261020b.tgz` (476,602 bytes; sha256 `7d972327…`) |
| 16:01:44 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261020b.log`) | install complete; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 19705 in `/system.slice/attest.service`; 4,076 entries verified in place; vhost unchanged, nginx not reloaded; keep-3 kept `0.8.3`, `0.9.0`, `0.10.0` |
| 16:02:06 | `snapshot.sh after-20261020b`; health | `app -> releases/0.10.0-7e72364f135c`, `app.prev -> releases/0.9.0-ab5b1705ae2b`; version 0.10.0, worker alive, idle, queue 0; `reconciliation` {0 holds, accepting runs, not failed closed}; `startup` {0 reconciled, 0 deduplicated, 0 holds repaired, recovery not failed} |
| 16:04 | rollback readiness (read-only, nothing switched) | the 0.9.0 release in place: version 0.9.0, digest `ab5b1705…`, all 3,997 `RELEASE.json` entries equal on disk, its interpreter imports the package and its dependencies |
| 16:05 | pruning for disk headroom | release `0.8.3-35b264adcd08` (neither active nor the rollback target) removed after its manifest was archived and the archive's hash compared equal on both sides (`6d996601…`) |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261020b.txt`, 16:02:10; `readback-after-prune.txt`, 16:06:25) | unit active, MainPID 19705; package 0.10.0, digest `7e72364f135c…` over 37 files; systemd `MemoryAccounting=yes`, `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, both fail counters 0, `oom_kill 0`; 40 store rows, none queued or running; **0 open reconciliation holds**, accepting runs, not failed closed; the other services active; `nginx -t` successful |
| Queue, reservations, budget | queue 0, 0 active reservations; $0.0000 committed on this UTC day, $2.00 of the $2.00 cap remaining |
| Accounting across the deployment (the backup taken before it against the live store, both opened read-only) | identical: 40 rows (39 finished, 1 error), $1.557558 committed and $1.557558 known cost (all of it the recorded Nemotron runs), 0 holds; the only schema change is the `holds_one_per_run` index |
| Disk | 1,328,570,368 bytes free of 14,483,959,808 (9.17 %) after the deployment and the pruning; 7.41 % before this pass's pruning; the low-disk threshold (7 %, 500 MB) unchanged |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261020b`, `styles.css?v=20261020b` byte-identical to the release; `/api/health` version 0.10.0 with `reconciliation` {0 holds open, accepting runs, `fail_closed` false}; the public Nemotron profile only; 40 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; the gateway's name in none of the responses |
| Real Chrome on the public URL (`browser-production-headless-5-widths.json`; `scripts/console_layout_audit.py --base`, every request that is not a GET aborted inside the browser) | headless sweep at 320, 390, 768, 1024 and 1440 px over the home page (every panel open, live mode selected, the confirmation open, the replay finished) and the case file of the recorded runs on every tab with every detail open, a missing run and a simulated API failure: 455 states, no element or text wider than the viewport, no clipped control, no page that scrolls sideways; the Guide opens by itself only in the case file at 1440 px, as before; 1,288 GET requests and no other request; in live mode the Run button opened the confirmation at every width and sent nothing |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.9.0-ab5b1705ae2b` (checked in place before the pruning, nothing switched). 0.8.3
was pruned for disk headroom; it can be rebuilt from code commit `459fe8d` (pinned in `5f479a8`) and installed with `install.sh`, like 0.8.2
(`4d37dbb`) and 0.8.1 (`d15046a`). The unit is the same for all, so the memory limit stays in force after a rollback; the one-hold-per-run
index that 0.10.0 creates is compatible with 0.9.0 (which opens at most one hold per run) and ignored by earlier versions.
`attest.db.bak-20261020b-full` and `/var/backups/attest-data-20261020b.tgz` hold the state before this deployment. The rollback was not
exercised (switching would restart the public service twice); its target was verified in place.

## Files

`deploy-0100-server.sh` (the server-side steps), `readback.sh` (read-only; revision 9's plus the fail-closed state and the disk),
`disk-inventory.sh` (read-only; its outputs stay in the private record because they name the host's other services and projects),
`public_readonly_checks.py` and `public-readonly-checks.json`, `before-20261020b-20261020T160140Z.txt`, `after-20261020b-20261020T160206Z.txt`,
`health-before-20261020b.json`, `health-after-20261020b.json`, `deploy-0100-server.log`, `install-20261020b.log`,
`readback-after-deploy-20261020b.txt`, `readback-after-prune.txt`, `browser-production-headless-5-widths.json`.
