# Deployment of 0.10.3 (the task picker) to yungou, 21 Oct 2026, 07:01 UTC

What was deployed: version 0.10.3, the package of code commit `5359880` (published as `13574c89ea60`; `FREEZE.md`, "The 0.10.3 pin"),
built from a clean worktree of the pin record `794b3f8`, which carries that package unchanged. The owner asked for a more refined task
menu. 0.10.3 replaces the native select with a listbox that shows each task's short title and qualifier, its facts as chips
(repository, issue, runner, held-out tests), its latest Attest verdict and its recorded runs. Browsing a task now opens its latest
Attest verdict rather than an infrastructure error (`latest_evidence_*` in `/api/tasks`). The labels are derived from the task files
without changing them. Asset stamp `20261021b`. A clean checkout of `5359880` passes all 503 tests offline on macOS (0 skipped;
`suites/`).

Scope and method as before:
- Only the Attest service changed. `install.sh`, `rollback.sh`, `snapshot.sh`, `decommission.sh`, the unit and the vhost are
  byte-identical to the 0.10.2 deployment, and nginx was not reloaded.
- The other services were untouched. The before and after snapshots differ only in the time, memory, swap and load lines and in the
  release list.
- Afterwards, only read-only checks ran: GET requests, a browser that aborts every other request, and read-only SSH.

## Build and procedure (UTC; `deploy-0103-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` ran from a clean worktree of `794b3f8`. It produced `app.tar.gz` (sha256
  `4dfd0e7f0a8135b0d4c9f9f67013ea22247009564b89ed2e1a13f033c273324f`) and `RELEASE.json` with 4,758 entries (version 0.10.3, label
  `0.10.3-c002ef609d9c`).
- The nine files went up as one ustar archive, and `sha256sum -c upload.sha256` passed on the host for all nine.

| Time | Step | Result |
| --- | --- | --- |
| 07:01:09 | digests; `snapshot.sh before-20261021c`; idle check | all `OK`; version 0.10.2, busy false, queue 0, no current run, 0 holds |
| 07:01 | store backup | `/var/lib/attest/attest.db.bak-20261021c-full` (74 rows, 0 holds; sha256 `5f2fd04a…`, byte-identical to the backup before 0.10.2 because no row changed in between) and `/var/backups/attest-data-20261021c.tgz` (554,635 bytes; sha256 `e8e2589e…`) |
| 07:01 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261021c.log`) | install complete; 4,758 entries verified in place; **memory limit in force**: systemd `MemoryLimit=209715200`, cgroup memory and memory-plus-swap limits 209,715,200, main PID 32680, started 07:01:29; vhost unchanged, nginx not reloaded; keep-3 pruned `0.10.0-7e72364f135c` and kept `0.10.1`, `0.10.2`, `0.10.3` |
| 07:01:33 | `snapshot.sh after-20261021c`; health | `app -> releases/0.10.3-c002ef609d9c`, `app.prev -> releases/0.10.2-6104fd89f66a`; version 0.10.3, worker alive, idle, queue 0; 0 holds, accepting runs, not failed closed |
| 08:29 | rollback readiness (read-only, nothing switched) | the 0.10.2 release in place: all 4,742 `RELEASE.json` entries equal on disk (version 0.10.2, digest `6104fd89…`); its interpreter imports the package and its dependencies |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback (`readback-after-deploy-20261021c.txt`) | unit active, MainPID 32680; package 0.10.3, digest `c002ef609d9c…` over 37 files; the memory limit in force, fail counters 0, `oom_kill 0`, resident 52,356 kB; 74 store rows, none queued or running; 0 open reconciliation holds; the other services active; `nginx -t` successful; disk 3,303,518,208 bytes free of 14,483,959,808 (22.81 %) |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261021b`, `styles.css?v=20261021b` byte-identical to the release; `/api/health` version 0.10.3, 0 holds, accepting runs; the public Nemotron profile only; 74 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; a recorded run's page served; the gateway's name in none of the responses. The first attempt of the script stopped on a transient TLS error at its last request (`SSLEOFError`); the second attempt passed every check. |
| Real Chrome on the public URL (`browser-production-headless-5-widths.json`, finished 08:28:21; `scripts/console_layout_audit.py --base`, every request that is not a GET aborted inside the browser) | 320, 390, 768, 1024 and 1440 px over the home page, the task picker open (new in 0.10.3; at every width on the home page, and in the case file's rail where the rail shows), and the case file of the recorded runs on every tab: 552 states, no element or text wider than the viewport, no clipped control, no page that scrolls sideways; 1,558 GET requests and no other request; in live mode the Run button opened the confirmation at every width and sent nothing |

The owner-approved live run of the demonstration film ran on this release, between these checks (07:03 to 07:09 UTC):
`reports/attest-demo-run-2026-10-21/README.md`.

## Rollback, and the limitation that now needs a fix

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.10.2-6104fd89f66a`, checked in place. `attest.db.bak-20261021c-full`
and `/var/backups/attest-data-20261021c.tgz` hold the state before this deployment.

The 34 runs imported by 0.10.1 still name folders inside `/opt/attest/releases/0.10.1-53a9b7c39a96/`
(`reports/attest-deployment-2026-10-21/README.md`). That release is now the oldest of the three kept, so **the next install would prune
it, and those runs would lose their downloadable bundles.** Before another release, either re-point those rows to `/opt/attest/app/…`,
where every release carries the same reports, or store imported folders unresolved. This deployment changes neither.

## Files

`deploy-0103-server.sh` (the 0.10.2 script with the new stamp), `readback.sh` (unchanged), `public_readonly_checks.py` (the asset stamp
updated) and `public-readonly-checks.json`, `before-20261021c-20261021T070109Z.txt`, `after-20261021c-20261021T070133Z.txt`,
`health-before-20261021c.json`, `health-after-20261021c.json`, `deploy-0103-server.log`, `install-20261021c.log`,
`readback-after-deploy-20261021c.txt`, `browser-production-headless-5-widths.json`, `suites/` (the clean macOS run of `5359880` and its
driver).
