# Deployment of 0.8.1 (revision 8, console repairs) to yungou, 19 Oct 2026, 22:17 to 22:18 UTC

What was deployed: version 0.8.1, the repairs of the five console defects that the browser checks of the deployed 0.8.0 found
(`reports/attest-deployment-2026-10-19e/README.md`): the Guide opens by itself only from 1320 px, where it cannot cover the case
file's tabs (at 1024 px it covered Activity and Files); below 1320 px the decision card's buttons take their own row (its text had
been squeezed to about 80 px); below 1180 px the overview's two columns stack (the evidence table had been squeezed into a sideways
scroll); a task list that failed to load says so (it said "No sample tasks are configured"); on phones the collapsed workspace rail
no longer stretches into an empty band on short pages. Asset stamp `20261019f`. The `attest/` Python sources differ from 0.8.0 only
by the version string, so the pipeline, the providers, the store and the harness are those of 0.8.0. The release was built from a
clean checkout (`git worktree add --detach`) of the review repository at `ab8c445`, the pin record that names code commit
`d15046a` (package digest `3c0cbfcaa9d6…` over 37 sources; `FREEZE.md`); a clean checkout of `d15046a` passes all 402 tests.

Scope, as for 0.8.0: the Attest service only. The unit and the vhost are unchanged (nginx was not reloaded); the other services were
not touched (the snapshots differ only in the timestamp, memory, swap and load lines and in the release links). Nothing changed on
the Aliyun host; no Docker component. Every check of production was read-only (GET requests, a browser that aborted every other
request before it was sent, read-only SSH commands); no inference call was made.

## Build and procedure (UTC; `deploy-081-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` from the clean worktree of `ab8c445` (`build-20261019f.log`): `app.tar.gz`, 4,369 members,
  sha256 `f4b11a27275888a6cd578bb5a7e34bf302f4f0e759057f7598b68571d6411d32`; `RELEASE.json` with 3,881 entries (version 0.8.1,
  label `0.8.1-3c0cbfcaa9d6`). The installer, rollback, decommission and snapshot scripts, the unit and the vhost are byte-identical
  to those of the 0.8.0 deployment; `sha256sum -c upload-20261019f.sha256` passed on the host for all eight files.

| Time | Step | Result |
| --- | --- | --- |
| 22:17:40 | digests; `snapshot.sh before-20261019f`; idle check | all `OK`; version 0.8.0, busy false, queue 0, no current run (`health-before-20261019f.json`) |
| 22:17 | store backup | `/var/lib/attest/attest.db.bak-20261019f-full` (SQLite backup API, 40 rows) and `/var/backups/attest-data-20261019f.tgz` (422,465 bytes) |
| 22:17:48 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019f.log`) | steps 01 to 16 ok: all 3,881 entries verified; own virtualenv; compile and import checks with the release's interpreter (version 0.8.1, digest equal to `RELEASE.json`); unit and vhost unchanged; switch; restart; strict health (version 0.8.1); **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 4188 in `/system.slice/attest.service`; readback through `/opt/attest/app`; nginx reload not needed; the keep-3 policy pruned `0.6.0-b11ec0658845` |
| 22:18:06 | `snapshot.sh after-20261019f` | `app -> releases/0.8.1-3c0cbfcaa9d6`, `app.prev -> releases/0.8.0-ed41f4c95bd1`; releases `0.7.0-f836cfd0154f`, `0.8.0-ed41f4c95bd1`, `0.8.1-3c0cbfcaa9d6` |
| 22:18:10 | health after (`health-after-20261019f.json`) | ok, version 0.8.1, worker alive, ready, idle, queue 0, "$0.0552 committed + 0 active reservation(s) within $2.00" |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback on the host, 22:19 UTC (`readback-after-deploy-20261019f.txt`, `reports/attest-revision7-repairs-2026-10-19/memory/readback.sh`) | unit active, MainPID 4188; `app -> releases/0.8.1-3c0cbfcaa9d6`, `app.prev -> releases/0.8.0-ed41f4c95bd1`; package 0.8.1, digest `3c0cbfcaa9d6…` over 37 files; systemd `MemoryAccounting=yes MemoryLimit=209715200`; cgroup `memory.limit_in_bytes` and `memory.memsw.limit_in_bytes` 209,715,200, usage 40.7 MB, both fail counters 0, `oom_kill 0`; the main process in `/system.slice/attest.service`, 50.9 MB resident, no swap; 40 store rows, none queued or running; the other services active; `nginx -t` ok |
| Memory behaviour | the unit and its memory directives are those of 0.8.0, and the Python code differs only by the version string; the OOM drill of the deployed 0.8.0 (`reports/attest-revision7-repairs-2026-10-19/memory/drill-app-run-1.txt`) is not repeated |
| Queue, reservations, budget | queue 0, idle; 0 active reservations, $0.00 reserved, 0 active runs; $0.0552 committed on this UTC day (the unapproved probe run of 19 Oct, `reports/attest-deployment-2026-10-19c/`), $1.9448 of the $2.00 cap remaining |
| Public GET checks (`public-readonly-checks.json`, `public_readonly_checks.py`) | `/`, `/static/app.js?v=20261019f`, `/static/styles.css?v=20261019f` 200 and byte-identical to the commit's files; `/api/health` version 0.8.1, worker alive, ready, idle, queue 0, no `data_dir`; `/api/profiles` the public Nemotron profile only; `/api/runs?limit=200` 40 rows without private keys; `/api/openapi.json` strict `RunRequest`, no provider default, the `X-Attest-Confirm` header documented; the gateway's name in none of the responses |
| Real Chrome on the public URL (`browser-production-*.json`; every request that is not a GET is aborted inside the browser before it is sent, service workers blocked) | A headless sweep at 320, 360, 375, 390, 414, 768, 1024 and 1440 px (mobile emulation up to 820 px) and a visible Chrome window at 390 and 1440 px, 14 runs (up to three per verdict, longest identifiers first), 91 states per width (the home page, every disclosure open, live mode, the confirmation open and pressed; every tab of every run with every disclosure open; a missing run; every API call answered 503 inside the browser): **728 and 182 states, no element or text wider than the viewport, no clipped control, no sideways-scrolling document, no page error, and every one of the 560 and 140 tab presses went through** (at 1024 px as well); the page saw the true viewport width at scale 1 in every state. **The Guide opened by itself only at 1440 px** (in 84 of 85 case-file states there; in none below 1320 px). **No request other than GET left the browser** (2,049 and 514 GET requests; the guard had nothing to abort): in live mode the Run button opened the confirmation and sent nothing, and the confirmation's button was refused by the page in the automated browser at every width |
| Screenshots (`screens/`, viewport captures listed in `shots.json`, made by `evidence_shots.py` with the same guard; no request other than GET) | `hold-1024.png` (the case file at 1024 px: the decision's buttons on their own row, the tabs clear, the Guide behind its launcher); `hold-tests-open-1024.png` and `hold-tests-open-390.png` (the counterexample with every disclosure open); `api-failure-1440.png` ("The sample tasks could not be loaded: the service did not answer. Reload the page in a minute."); `missing-run-390.png` (no empty band under the rail); `home-1440.png`, `confirm-1440.png`, `confirm-refused-390.png` |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `/opt/attest/app.prev` (`releases/0.8.0-ed41f4c95bd1`), restarts only
`attest.service`, waits for strict health with version 0.8.0 and reads the digest back; `--to 0.7.0-f836cfd0154f` reaches the
release before revision 8. The unit is the same for all three, so the memory limit stays in force after a rollback; the store
schema is unchanged since 0.7.0. `attest.db.bak-20261019f-full` and `/var/backups/attest-data-20261019f.tgz` hold the state before
this deployment.

## Files

`before-20261019f-20261019T221740Z.txt`, `after-20261019f-20261019T221806Z.txt`, `health-before-20261019f.json`,
`health-after-20261019f.json`, `build-20261019f.log`, `upload-20261019f.sha256`, `deploy-081-server.log`, `install-20261019f.log`,
`readback-after-deploy-20261019f.txt`, `public_readonly_checks.py` and `public-readonly-checks.json`, `browser-production-headless-all-widths.json`, `browser-production-headed-390-1440.json`, `evidence_shots.py`, `screens/` (eight viewport screenshots and `shots.json`).
