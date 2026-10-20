# Deployment of 0.9.0 (revision 9, stop for reconciliation) to yungou, 20 Oct 2026, 08:22 UTC

What was deployed: version 0.9.0 (`reports/attest-revision9-repairs-2026-10-20/README.md`): a run stops at the first operation whose
outcome is uncertain, at every stage; HTTP answers are classified (4xx refused, 5xx uncertain); sandbox operations are journaled durably
before dispatch and before polling; the console holds new runs while a stopped run awaits reconciliation (`/api/health` reports
`reconciliation`, admission answers 503 during a hold, the case file shows "Held for reconciliation"). Asset stamp `20261020a`. Package
`ab5b1705ae2b…` (37 sources). Built from a clean checkout of the pin record `65d81f7`, which names code commit `7664742` (`FREEZE.md`);
clean checkouts of both pass all 458 tests offline (credentials absent, network blocked). The store gains a `holds` table at start-up
(created if missing); 0.8.3 ignores it, so a rollback needs nothing else.

Scope and method as before: the Attest service only, unit and vhost byte-identical to the earlier deployments (nginx not reloaded), the
other services untouched (the snapshots differ only in the timestamp, memory, swap and load lines and in the release links), nothing on the
Aliyun host, read-only checks only (GET requests, a browser that aborts every other request, read-only SSH), no inference call.

## Build and procedure (UTC; `deploy-090-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` from the clean worktree of `65d81f7`: `app.tar.gz`, sha256
  `4a2cae099623022bb317fe0c47db7650b2b24374eb286311afda7cf68e738d88`, `RELEASE.json` with 3,997 entries (version 0.9.0, label
  `0.9.0-ab5b1705ae2b`); `install.sh`, `rollback.sh`, `snapshot.sh`, `decommission.sh`, the unit and the vhost byte-identical to the 0.8.3
  deployment. The first upload (a tar stream over SSH) was refused by the host's GNU tar 1.26 before anything was extracted; nothing ran.
  The files were then sent as one ustar archive, and `sha256sum -c upload.sha256` passed on the host for all nine files.

| Time | Step | Result |
| --- | --- | --- |
| 08:21:41 | digests; `snapshot.sh before-20261020a`; idle check | all `OK`; version 0.8.3, busy false, queue 0, no current run |
| 08:21 | store backup | `/var/lib/attest/attest.db.bak-20261020a-full` (40 rows) and `/var/backups/attest-data-20261020a.tgz` (462,388 bytes) |
| 08:21:45 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261020a.log`) | install complete; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 11278 in `/system.slice/attest.service`; vhost unchanged, nginx not touched; the keep-3 policy pruned `0.8.1-3c0cbfcaa9d6` (releases now `0.8.2-ed1ac3bad3ec`, `0.8.3-35b264adcd08`, `0.9.0-ab5b1705ae2b`) |
| 08:22:08 | `snapshot.sh after-20261020a`; health | `app -> releases/0.9.0-ab5b1705ae2b`, `app.prev -> releases/0.8.3-35b264adcd08`; version 0.9.0, worker alive, idle, queue 0 |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261020a.txt`, 08:22:12) | unit active, MainPID 11278; package 0.9.0, digest `ab5b1705ae2b…` over 37 files; systemd `MemoryAccounting=yes`, `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, usage 40.3 MB, peak 41.0 MB, both fail counters 0, `oom_kill 0`; 51.8 MB resident, no swap; 40 store rows, none queued or running; **0 open reconciliation holds** (the table exists); the other services active; `nginx -t` successful |
| Queue, reservations, budget | queue 0, 0 active reservations; $0.0000 committed on this UTC day, $2.00 of the $2.00 cap remaining; disk 1,031 MB free (7.47 %), not low |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261020a`, `styles.css?v=20261020a` byte-identical to the commit's files; `/api/health` version 0.9.0 with `reconciliation` {0 holds open, accepting runs}; the public Nemotron profile only; 40 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; the gateway's name in none of the responses |
| Real Chrome on the public URL (`browser-production-headless-5-widths.json`; every request that is not a GET aborted inside the browser) | headless sweep at 320, 390, 768, 1024 and 1440 px over the home page (with every panel open, live mode selected, the confirmation open and the replay finished), the case file of one run per verdict on every tab with every detail open, a missing run and a simulated API failure: 215 states, no element or text wider than the viewport, no clipped control, no page error, no click blocked by an overlay, the Guide opening by itself only at 1440 px; 643 GET requests and no other request; in live mode the Run button opened the confirmation at every width and sent nothing |
| The held run's case file (the new state; no run is held in production) | checked before the deployment in the same Chrome against a local console with no credential: `reports/attest-revision9-repairs-2026-10-20/console/held-run-check-7664742.json` (1440 and 390 px: nothing wider than the viewport, "Held for reconciliation" instead of "Start a new run", the decision naming the operation's stage) |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.8.3-35b264adcd08`; `--to 0.8.2-ed1ac3bad3ec` reaches 0.8.2. 0.8.1 was pruned by the
keep-3 policy during this deployment; it can be rebuilt from code commit `d15046a` (pinned in `ab8c445`) and installed with `install.sh`. The unit is the
same for all, so the memory limit stays in force after a rollback, and the `holds` table that 0.9.0 created is ignored by earlier versions.
`attest.db.bak-20261020a-full` and `/var/backups/attest-data-20261020a.tgz` hold the state before this deployment. The rollback was not
exercised in this deployment.

## Files

`deploy-090-server.sh` (the server-side steps), `readback.sh` (read-only; revision 8's plus the reconciliation holds),
`public_readonly_checks.py` and `public-readonly-checks.json`, `held_run_check.py` (the held run's case file, run before the deployment),
`before-20261020a-20261020T082141Z.txt`, `after-20261020a-20261020T082208Z.txt`, `health-before-20261020a.json`, `health-after-20261020a.json`,
`deploy-090-server.log`, `install-20261020a.log`, `readback-after-deploy-20261020a.txt`, `browser-production-headless-5-widths.json`,
`screens/` (the home page at 1440 and 390 px; kept privately, not exported).
