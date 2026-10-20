# Deployment of 0.8.3 (revision 8, the hero's check badge) to yungou, 19 Oct 2026, 23:55 UTC

What was deployed: version 0.8.3. 0.8.2 had corrected the home page's replay claim ("offline check 24 of 24 OK", from an earlier
checker) but its longer badge, "attest check: OK, historical bundle", squeezed the "Proof Bundle" title beside it into a mid-word
break once the replay finished (`reports/attest-deployment-2026-10-19g/`). 0.8.3 shortens the badge to "attest check: OK, partial"
(the checker's own result reads "OK (historical bundle, partial checks)"; the caption keeps the full statement), and the layout
audit now measures the finished replay as well. Asset stamp `20261019h`. The `attest/` Python sources differ from 0.8.0 to 0.8.2
only by the version string (package `35b264adcd08…`). Built from a clean checkout of the pin record `5f479a8`, which names code
commit `459fe8d` (`FREEZE.md`); a clean checkout of `459fe8d` passes all 402 tests.

Scope and method as before: the Attest service only, unit and vhost unchanged (nginx not reloaded), the other services untouched
(the snapshots differ only in the timestamp, memory, swap and load lines and in the release links), nothing on the Aliyun host,
read-only checks only (GET requests, a browser that aborts every other request, read-only SSH), no inference call.

## Build and procedure (UTC; `deploy-083-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` from the clean worktree of `5f479a8` (`build-20261019h.log`): `app.tar.gz`, 8,588,915 bytes,
  sha256 `cc9f86d3be446a810fd4c38ec40f6c2de40b333125235a4626be62db5e531e81`; `RELEASE.json` with 3,915 entries (version 0.8.3,
  label `0.8.3-35b264adcd08`). Scripts, unit and vhost byte-identical to the earlier deployments of this pass; `sha256sum -c
  upload-20261019h.sha256` passed on the host for all eight files.

| Time | Step | Result |
| --- | --- | --- |
| 23:55:19 | digests; `snapshot.sh before-20261019h`; idle check | all `OK`; version 0.8.2, busy false, queue 0, no current run |
| 23:55 | store backup | `/var/lib/attest/attest.db.bak-20261019h-full` (40 rows) and `/var/backups/attest-data-20261019h.tgz` (449,061 bytes) |
| 23:55 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019h.log`) | steps 01 to 16 ok; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 6053 in `/system.slice/attest.service`; the keep-3 policy pruned `0.8.0-ed41f4c95bd1` (releases now `0.8.1-3c0cbfcaa9d6`, `0.8.2-ed1ac3bad3ec`, `0.8.3-35b264adcd08`) |
| 23:55:40 | `snapshot.sh after-20261019h`; health | `app -> releases/0.8.3-35b264adcd08`, `app.prev -> releases/0.8.2-ed1ac3bad3ec`; version 0.8.3, worker alive, idle, queue 0 |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261019h.txt`) | unit active, MainPID 6053; package 0.8.3, digest `35b264adcd08…` over 37 files; systemd `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, usage 39.4 MB, fail counter 0; 51.1 MB resident, no swap; 40 store rows, none queued or running; the other services active |
| Queue, reservations, budget | queue 0, 0 active reservations; $0.0552 committed on this UTC day (the unapproved probe run of 19 Oct), $1.9448 of the $2.00 cap remaining |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261019h`, `styles.css?v=20261019h` byte-identical to the commit's files; `/api/health` version 0.8.3; the public Nemotron profile only; 40 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; the gateway's name in none of the responses |
| The replay's final state (`hero-replay-finished.json`, `hero_check.py`; `screens/hero-replay-finished-1280.png`, `-390.png`) | watched to its end at 320, 390, 768, 1024, 1280 (scale 1.5), 1440 and 1920 px: the badge reads "attest check: OK, partial", the "Proof Bundle" title stays on one line from 390 px up (at 320 px the badge has its own row and the title wraps between its two words, as in every earlier version), and no width scrolls sideways |
| Real Chrome on the public URL (`browser-production-*.json`; every request that is not a GET aborted inside the browser) | The headless sweep at 320, 360, 375, 390, 414, 768, 1024 and 1440 px and the visible window at 390 and 1440 px, now with the finished replay among the states: 736 and 184 states, no element or text wider than the viewport, no clipped control, no page error, every tab press through, the Guide opening by itself only at 1440 px; 2,057 and 518 GET requests and no other request; the confirmation refused by the page in the automated browser at every width |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.8.2-ed1ac3bad3ec`; `--to 0.8.1-3c0cbfcaa9d6` reaches 0.8.1. 0.8.0
and 0.7.0 were pruned by the keep-3 policy during this pass; each can be rebuilt from its pin record (`3be63fa`, `fdf5099`) and
installed with `install.sh`. The unit is the same for all, so the memory limit stays in force after a rollback.
`attest.db.bak-20261019h-full` and `/var/backups/attest-data-20261019h.tgz` hold the state before this deployment.

## Files

`before-20261019h-20261019T235519Z.txt`, `after-20261019h-20261019T235540Z.txt`, `health-before-20261019h.json`,
`health-after-20261019h.json`, `build-20261019h.log`, `upload-20261019h.sha256`, `deploy-083-server.log`, `install-20261019h.log`,
`readback-after-deploy-20261019h.txt`, `public_readonly_checks.py` and `public-readonly-checks.json`, `hero_check.py` and
`hero-replay-finished.json`, `browser-production-headless-all-widths.json`, `browser-production-headed-390-1440.json`, `evidence_shots.py`, `screens/` (the finished replay at 1280 and 390 px, five viewport screenshots with `shots.json`).
