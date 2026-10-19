# Deployment of 0.8.2 (revision 8, the hero's check claim) to yungou, 19 Oct 2026, 23:11 UTC

What was deployed: version 0.8.2, one correction found while the video was prepared. The home page's replay of the 17 Oct bundle
`slugkit-regression-001-attest-a2` said "attest check: OK, 24 of 24" and "offline check 24 of 24 OK", figures from an earlier
checker; the current checker passes that bundle as a historical bundle (28 checks, 0 errors, 2 warnings: it predates the evidence
protocol, so it is checked for internal consistency and never reported as fully verified), which the page's own Proof Bundle
section already showed. The badge now reads "attest check: OK, historical bundle" and the caption says what the check establishes.
Asset stamp `20261019g`. The `attest/` Python sources differ from 0.8.1 only by the version string (package `ed1ac3bad3ec…`). The
release was built from a clean checkout of the pin record `cb94aef`, which names code commit `4d37dbb` (`FREEZE.md`); clean
checkouts of `4d37dbb` and of the 0.8.1 records commit `17a58c5` pass all 402 tests.

Scope and method as for 0.8.0 and 0.8.1: the Attest service only, unit and vhost unchanged (nginx not reloaded), the other services
untouched (the snapshots differ only in the timestamp, memory, swap and load lines and in the release links), nothing on the Aliyun
host, read-only checks only (GET requests, a browser that aborts every other request, read-only SSH), no inference call.

## Build and procedure (UTC; `deploy-082-server.log` is the complete output)

- `deploy/yungou/build_bundle.sh` from the clean worktree of `cb94aef` (`build-20261019g.log`): `app.tar.gz`, 8,562,473 bytes, 4,388
  members, sha256 `3ab60cd8626729c242e2e4db1cb99a1fce664be4a4c67d244a47c66e7f57aae3`; `RELEASE.json` with 3,899 entries (version
  0.8.2, label `0.8.2-ed1ac3bad3ec`). Scripts, unit and vhost byte-identical to the earlier deployments of this pass;
  `sha256sum -c upload-20261019g.sha256` passed on the host.

| Time | Step | Result |
| --- | --- | --- |
| 23:11:17 | digests; `snapshot.sh before-20261019g`; idle check | all `OK`; version 0.8.1, busy false, queue 0, no current run |
| 23:11 | store backup | `/var/lib/attest/attest.db.bak-20261019g-full` (40 rows) and `/var/backups/attest-data-20261019g.tgz` (435,765 bytes) |
| 23:11:20 | `MEMORY_MAX=200M bash install.sh app.tar.gz` (`install-20261019g.log`) | steps 01 to 16 ok; version 0.8.2 verified before and after the switch; **memory limit in force**: systemd `MemoryLimit=209715200`, `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 5187 in `/system.slice/attest.service`; the keep-3 policy pruned `0.7.0-f836cfd0154f` (releases now `0.8.0-ed41f4c95bd1`, `0.8.1-3c0cbfcaa9d6`, `0.8.2-ed1ac3bad3ec`) |
| 23:11:38 | `snapshot.sh after-20261019g`; health | `app -> releases/0.8.2-ed1ac3bad3ec`, `app.prev -> releases/0.8.1-3c0cbfcaa9d6`; version 0.8.2, worker alive, idle, queue 0 |

## Verification after the install (read-only)

| Check | Result |
| --- | --- |
| Readback, 23:12 UTC (`readback-after-deploy-20261019g.txt`) | unit active, MainPID 5187; package 0.8.2, digest `ed1ac3bad3ec…` over 37 files; systemd `MemoryLimit=209715200`; cgroup memory and memory-plus-swap limits 209,715,200, usage 37.7 MB, fail counters 0, `oom_kill 0`; 48.5 MB resident, no swap; 40 store rows, none queued or running; the other services active; `nginx -t` ok |
| Queue, reservations, budget | queue 0, 0 active reservations, $0.00 reserved; $0.0552 committed on this UTC day (the unapproved probe run of 19 Oct), $1.9448 of the $2.00 cap remaining |
| Public GET checks (`public-readonly-checks.json`) | `/`, `app.js?v=20261019g`, `styles.css?v=20261019g` byte-identical to the commit's files; `/api/health` version 0.8.2, ready, idle; the public Nemotron profile only; 40 rows without private keys; strict `RunRequest` and the `X-Attest-Confirm` header in the published schema; the gateway's name in none of the responses |
| Real Chrome on the public URL (`browser-production-*.json`; every request that is not a GET aborted inside the browser) | The headless sweep at eight widths from 320 to 1440 px and the visible window at 390 and 1440 px: 728 and 182 states, no element or text wider than the viewport, no clipped control, no page error, every tab press through, the Guide opening by itself only at 1440 px; 2,044 and 518 GET requests and no other request; the confirmation refused by the page in the automated browser at every width |
| **The replay's final state: a defect introduced by 0.8.2** | Watched to its end in a 1280 x 720 window at scale 1.5 (`screens/hero-replay-finished-1280-defect.png`): the badge reads "attest check: OK, historical bundle" and the caption states the check correctly, but the longer badge leaves the "Proof Bundle" title beside it about 30 px, so the title breaks inside the word ("Proof / Bund / le") on every desktop width. The sweeps measure the page at load, while the badge still reads "pending", so they could not see it. Repaired in 0.8.3 (`reports/attest-deployment-2026-10-19h/`): a badge of at most 26 characters, "attest check: OK, partial", and the audit now measures the finished replay |

## Rollback

`bash /var/tmp/attest-deploy/rollback.sh` re-selects `releases/0.8.1-3c0cbfcaa9d6`; `--to 0.8.0-ed41f4c95bd1` reaches the first
revision-8 release. The release before revision 8 (`0.7.0-f836cfd0154f`) was pruned by the keep-3 policy at this install; it can be
rebuilt from its pin record (`fdf5099`) and installed with `install.sh`. The unit is the same for all, so the memory limit stays in
force after a rollback. `attest.db.bak-20261019g-full` and `/var/backups/attest-data-20261019g.tgz` hold the state before this
deployment.

## Files

`before-20261019g-20261019T231117Z.txt`, `after-20261019g-20261019T231138Z.txt`, `health-before-20261019g.json`,
`health-after-20261019g.json`, `build-20261019g.log`, `upload-20261019g.sha256`, `deploy-082-server.log`, `install-20261019g.log`,
`readback-after-deploy-20261019g.txt`, `public_readonly_checks.py` and `public-readonly-checks.json`, `browser-production-headless-all-widths.json`, `browser-production-headed-390-1440.json`, `evidence_shots.py`, `screens/` (four viewport screenshots with `shots.json`, and the replay's final state).
