# Revision 10 (20 Oct 2026, version 0.10.0): holds that survive restarts, atomic hold records, a resume gate tied to item ids, and a stop on malformed answers

Scope: the four defects named in the revision-10 instruction, the reconciliation of the two VERIFIED development runs of 17 Oct that
went on after an uncertain spawn, and the disk headroom on yungou. Every defect was reproduced on the frozen 0.9.0 tree before the repair
(`repro/`), and the same script was run on the repaired tree. Code commit `775248c` of the review repository, pinned as `c0ddb48` (one test
of the evidence inventory added, see the clean-checkout results); package digest `7e72364f135c…` (37 sources). Nothing was published or pushed, no paid Nebius call was made, and no video was touched.

## The issues, their causes and the repairs

### 1. A held run lost its hold on restart when its proof bundle existed

*Cause.* `Store.finalize_interrupted` (the restart recovery of every row left queued or running) finalized a run from its proof bundle
as `finished` whenever the bundle existed, without reading the bundle's reconciliation record or the ledger journal. A process that died
after `Pipeline.finish` wrote the bundle and before the worker recorded the hold left a run that had stopped for reconciliation recorded
as finished, with no hold, and the console admitted runs again.

*Repair.* `read_run_reconciliation` reads both the bundle's record and the journal (an unreadable bundle falls back to the journal) and
`finalize_interrupted` holds the run when either requires reconciliation, whether or not the bundle exists. The console's own run
directory is imported with `hold_if_required` (a run found there without a row, after a store restored from an older backup, is held
too); imported evidence from other directories is never held for its history. `repair_holds` (below) also repairs rows that 0.9.0's
recovery had finalized as finished from a bundle that requires reconciliation.

### 2. The held state and the hold were two writes

*Cause.* The worker recorded the run as `reconciliation_required` (one autocommitted write), then its event, then the hold (another).
A refused insert or a process that stopped between them left the run recorded as held with no hold; the worker then started the next
queued run, and no restart ever created the hold (the recovery only looked at queued and running rows).

*Repair.* `Store.record_reconciliation` writes the row, its event and the hold in one SQLite transaction (`BEGIN IMMEDIATE ... COMMIT`,
rolled back on any failure). A run has at most one hold, ever: a partial unique index enforces it where no earlier duplicate prevents
the index, and the code checks too; recording a run that already has a hold, open or cleared, returns that hold and opens nothing. When
the transaction fails the worker fails closed: it starts nothing (queued runs end `paused_for_reconciliation`), admission answers 503,
`/api/health` reports `reconciliation.fail_closed`, the run's row is left queued or running for the restart recovery, and the record is
retried at every housekeeping pass (once written, the hold keeps runs paused until an operator clears it). Start-up runs
`Store.startup_recovery`: the orphaned rows are settled (item 1), then `repair_holds` gives every run recorded as
`reconciliation_required` without a hold row its hold. It acts only on runs that have no hold row at all, so a hold an operator cleared
is never reopened, and it never holds imported evidence or replay fixtures. A failure of the start-up recovery fails the worker closed
the same way. The console page now shows "paused for reconciliation" and offers no start while runs are paused (revision 9 left the
chip at "accepted" and the button enabled, and a click met a 503).

### 3. A resumed batch could bypass unresolved operations

*Cause.* `--resume` looked only at run directories that no persisted row owned. Completed rows whose run had halted, their bundles' reconciliation
records and the judge's journals were never read, so a resume over a halted cell started every remaining cell. `--reconciled NOTE`
approved whatever the interrupted directories listed without naming anything, and its note lived only in that process's report, so the
next restart asked for nothing or accepted the same note again.

*Repair.* Before anything is built, read from a provider or recorded as a resumption, the harness collects every unresolved item of the
batch: each persisted row's reconciliation list and halt record (a halted row whose records name nothing else becomes an item itself,
except a `batch_stop`, whose cause is another run's item; a row an earlier harness marked uncertain without saying what becomes one too),
each row's run directory (the bundle's reconciliation record, the run journal, the judge's journal) and every run directory no row owns.
Each item has a stable id (`u-` and 12 hex digits of its run and record key). While any item is not acknowledged the batch starts nothing:
it writes `reconciliation-pending.json`, prints each item with the read-only check that settles it, and exits 4. `--resume` alone is never
an approval. An acknowledgement is `--reconciled NOTE --items ID[,ID...]`; a note without ids, ids without a note, or an id the batch does
not list refuses everything (exit 2) and records nothing. The record is appended to `reconciliations.jsonl` in the report directory,
fsynced and read back (a line cut short by a crash is skipped, so its items count as unacknowledged again), and every later restart honours
it; an item that appears afterwards needs its own acknowledgement. A fresh batch over a report directory whose `runs/` holds unresolved
directories is gated the same way, and a batch whose gateway status answer cannot be read does not start.

### 4. Malformed upstream answers were read without checks

*Cause.* The adapters read fields of success answers directly (`(body or {}).get("uuid")`, `choices[0].get("message")`, `"/operations/" +
uuid`). A spawn answered with a JSON string or number raised a raw `AttributeError` and left the operation PENDING with no halt; an id that
was a path was polled (`GET /operations/../../instances`); an id that was a number raised `TypeError` after the operation was journaled
ACCEPTED; invalid UTF-8 raised a raw `UnicodeDecodeError` past the transport wrapper; a poll without a status, with an undocumented status or
an array body polled on until the deadline and sent a cancel; a record of another operation was taken as this one's result; a model answer
that was an array or lacked its output was a definite schema failure, so the pipeline sent a repair request; a Token Factory answer without
choices was settled and followed by another paid request.

*Repair.* `attest.http.decode_json` decodes every success body strictly before anything reads it: UTF-8 only, no unpaired surrogate escape,
standard JSON (no NaN or Infinity), nesting within the parser's bounds, the expected top-level type, an empty body only where the caller
allows one. The adapters check the fields they need: the spawn's operation id must be a UUID (`accepted_uuid`; a malformed id is kept,
escaped, in the operation's note and never used in a request path; the documented `Location` header's id is kept too); a poll must be an
object about this operation with a documented status and, for a terminal state, result fields of the documented types and valid base64
streams (`operation_record`); the gateway's run answer, its catalog and the Token Factory's completion have their own checks
(`run_answer_problem`, `catalog_problem`, `completion_problem`), and so do Tavily's search answers (`search_problem`). Every failure is a
`MalformedResponse`, never retried (a cut body stays a transport failure with its bounded read retries): an unreadable spawn answer is
UNCERTAIN, an unreadable poll leaves the operation ACCEPTED_UNREAD with its id, an unreadable model answer is an uncertain call (the Token
Factory reservation stays committed), a malformed read halts the run as `malformed_response`, and nothing is sent afterwards. Texts derived
from answers are ASCII-safe, so no undecodable character reaches a journal, a log line or the diagnostics sidecar.

## Reproduction and regression tests

`repro/reproduce_r10.py --tree <checkout>` runs 63 checks with interfaces both versions have (the store, the worker, the console's start-up
path, the harness, the adapters), with faults injected from outside the code: SQLite triggers on `holds` (a refused insert; a process that
dies inside the statement) and a local HTTP server answering malformed bodies to the real HTTP client and adapters.

| Tree | A restart with a bundle | B atomic hold | C resume gate | D malformed answers | Total |
| --- | --- | --- | --- | --- | --- |
| 0.9.0, frozen `2d831cc` (`repro/repro-before-0.9.0-2d831cc.json`) | 2 of 5 | 1 of 9 | 1 of 6 | 9 of 43 | **13 of 63** |
| 0.10.0, clean checkout of `775248c` (`repro/repro-after-0.10.0-775248c.json`) | 5 of 5 | 9 of 9 | 6 of 6 | 43 of 43 | **63 of 63** |

The checks 0.9.0 passes are the controls and the cases revision 9 already covered (a journal-only interrupted run is held; a cut body and a
body that is not JSON are uncertain; an empty object is an answer without an id).

`tests/test_revision10.py` (32 tests) is the regression suite: restart after a crash at each point between bundle creation, row update and
hold creation; an unreadable bundle; the journal read when the bundle needs nothing; imported evidence never held; a refused hold insert
that changes nothing; a process killed inside the transaction (a trigger calling a function that exits) leaving nothing half-written; repeated
recovery with one hold; a cleared hold never reopened; the worker failing closed until its record is written; a failed start-up recovery
failing the service closed (health and a 503); the resume gate over completed, halted and unowned directories with their bundles and run and
judge journals, notes with and without ids, unknown ids, a cut acknowledgement line, restarts that honour an acknowledgement and a new item
that blocks again, and a refused resume that builds and reads nothing; arrays, scalars, null, empty and non-UTF-8 bodies, unpaired surrogates,
NaN, deep nesting, missing fields, path-shaped and numeric ids and cut bodies through the real HTTP client and the Sandboxes, gateway, Token
Factory and Tavily adapters, each checking the state, the halt and that no request leaves afterwards (`ledger.admit` refuses); and two
pipeline runs that stop at a malformed spawn answer and a malformed gateway answer with nothing sent afterwards. Tests that fed the adapters
ids such as `op-1`, or the undocumented status `RUNNING`, now use UUIDs and `EXECUTING`; the accounting tests of the resume follow the new
acknowledgement rule; the console tests know the two new start-up counters.

## Clean-checkout test results

| Run | Set-up | Result |
| --- | --- | --- |
| `suites/suite-1-clean-775248c-macos.log` | clean `git worktree` of `775248c`, `env -i` (no credential, no private configuration), HOME a new empty directory, `sandbox-exec` denying every outbound connection except loopback | **491 tests, OK, 0 skipped**; HOME empty afterwards; checkout unchanged |
| `suites/suite-2-clean-775248c-linux.log` | `git archive` of `775248c` in a container on the Aliyun host with no network interface (`--network none`, 384 MB, 1 CPU, uid 65534, all capabilities dropped), dependencies from an offline wheelhouse | **491 tests, OK, 26 skipped** (the image has no bash, git or node); container removed; the host's services unaffected |
| `suites/suite-3-clean-f0c28c2-macos-one-failure.log` | the pin record `f0c28c2` (the deployed tree), after the deployment, the macOS set-up | **490 of 491 pass, 1 failure**: `RecordedCorpusInventory` found the live run's directory, which the record had added, unclassified |
| `suites/suite-4-clean-c0ddb48-macos.log` | `c0ddb48` (the inventory classifies the folder under protocol 5; tests only), the macOS set-up | **491 tests, OK, 0 skipped**; HOME empty afterwards; checkout unchanged |
| `suites/suite-5-clean-c0ddb48-linux.log` | `c0ddb48`, the Linux container set-up | **491 tests, OK, 26 skipped**; container removed |

Finding: the pin had been recorded from the clean checkouts of `775248c`, before the live run's directory existed; the final-tree rule asks the
suite to pass with the evidence in place, and the clean checkout of the record that added the directory did not. The pin now names `c0ddb48`
(the same package, harness, METHOD and examples); the deployed package is the pinned package, and the deployed tree's one stale test is never
run by the service.

## The two VERIFIED runs of 17 Oct, reconciled

`historical/` (`reconcile_historical.py`, `analyze_executed_mutants.py`, `match_gateway_calls.py`; seven GET requests to the Sandboxes API in
two passes, no other request, nothing replayed, no run started). Both uncertain mutant spawns executed: `mutant-m01-2f645511c4` of
`balanced-brackets-attest-a1-20261017T121900586528Z` as operation `01a149d2-b1df-75ba-8f8e-8d5e25a6c0b6`, created 101 s after the spawn was sent,
and `mutant-m08-64e9d487f1` of `semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z` as `01a14a0a-3364-7402-aa67-e3e5818d7df1`, created
262 s after its spawn and 78 s after its run had ended. Each operation's recorded job wrote exactly the mutant the run kept and the run's sealed
module, its result carries the job's nonce, and under the pipeline's own rule each mutant was killed (18 and 4 sealed tests failed with
authentic child results). With them the mutation scores are 9 of 9 and 12 of 12 (1.0, threshold 0.5); the other gates are unaffected, so both
verdicts stand and neither case is unresolved historical evidence. Positive control: every operation each run recorded (15 and 19) and its judge
operation are in the account's listing. The development gateway's ingress log (`gateway-ingress-2026-10-17.txt`, client addresses removed)
holds every model call the two runs recorded (9 and 10, all HTTP 200), and every `/v1/run` request of their windows belongs to a recorded call.
A first pass of the listing script looked only two minutes past each spawn and found no candidate for the semver spawn; the operation-by-operation
attribution showed the later one, and the window was widened before any conclusion was recorded. The correction is appended to
`reports/attest-reliability-2026-10-17/README.md`; the bundles are unchanged, so `attest check` still warns about the unknown mutant in each.

## Bundles, export provenance, accounting

- `checker/checker-0.9.0-vs-0.10.0.json`: all 182 proof bundles of the exported tree pass `attest check` with the 0.9.0 checker and with the
  0.10.0 checker; 486 warnings with both; no bundle's result changed. The reconciliation items gain a `note` field (what an answer said); the
  checker compares item keys, so older and newer checkers agree on every bundle.
- `checker/provenance-0.10.0-export.json`: 182 bundles OK, 25 fully verified (protocols 2, 3, 4 and 5: 7, 3, 14 and 1, the revision-9 live run),
  157 historical, 131 redacted copies, the same batch digest and profile figures as revision 9, nothing failed.
- Accounting: the budget and accounting tests pass; the committed figures of every scenario are unchanged. A malformed Token Factory answer
  keeps its reservation committed (unsettled), never a known zero. The pinned Nemotron profile computed offline from `775248c` equals the
  revision-7 registration (`nemotron-effective-profile-775248c.json`).

## A live development run of the pinned code

`live-codex/`: one run of the clean checkout of `775248c` on the team's gateway with real Sandboxes (`python -m attest run --task
examples/durationkit-task/task.json --provider codex --no-grounding --max-mutants 6`), to check the new answer checks against the real
services. Every answer was read and accepted: 12 gateway calls (one failed while its connection was set up, before any byte of it was
written, and was sent again, as revision 8 provides; the 11 others answered), the gateway's status and catalog reads, the image lookup and 8
Sandboxes operations (checkpoint, red check, two implementer tool runs, verification, the repository suite and two arbitration re-runs), each
journaled PENDING, ACCEPTED and SUCCESS; nothing halted and nothing was left to reconcile. The verdict is NEEDS HUMAN: one of the 18 sealed
tests failed on the candidate, the arbiter classified it as a test defect and validated a correction, and a sealed test that failed by
assertion is never overridden, so the hold stands (a verdict about the model's patch, not about the request paths). `attest check`: OK,
evidence complete for NEEDS HUMAN under protocol 5, no warning. Like the revision-9 live run, the bundle's provenance names the scratch
directory it ran from, which carries the local account name (see the owner decisions below).

## The console's paused state in a real browser

`console/paused_state_check.py` (`console/paused-state-check-775248c.json`): a local console with no credential over a store with an open hold,
and over a store whose start-up recovery fails (a run left running with a halted bundle, a database that refuses the hold insert), at 320,
390, 768, 1024 and 1440 px in Chrome with live mode selected: the runs chip reads "paused for reconciliation", the live start is disabled and
the estimate says why, nothing is wider than the viewport, and only GET requests were made (every other request is aborted in the browser).
Health reported `holds_open 1, accepting_runs false` and `holds_open 0, accepting_runs false, fail_closed true`.

## Disk headroom on yungou

Inventory first (read-only: `df`, inodes, the Attest trees, the largest other consumers, Docker's own accounting, journald, the processes
that wrote most since boot); the raw inventories stay in the private record because they name the host's other services and projects.
Before: 1,073,942,528 bytes free of 14,483,959,808 (7.41 %), 13 % of inodes used. Four Attest-owned items were obsolete and unreferenced (no
unit, cron job, symlink, open file or process used them): the CPython upload of 15 Oct (installed long since at `/opt/attest/python`),
the application upload of 19 Oct, release `0.8.2-ed1ac3bad3ec` (neither the active release nor the rollback target) and the shared venv of
the first layout (no release uses it). Before anything was removed, an archive of the deployment evidence in `/var/tmp/attest-deploy` (83
logs, snapshots, health answers and server-side scripts; the credential file excluded) and file-by-file sha256 manifests of the release and
the venv was made, copied to this machine with both uploads, and every hash compared equal on both sides (archive `c17d52e5…`). After the
pruning: 1,337,348,096 bytes free (9.23 %), about 9,400 files fewer; the service healthy and idle, the rollback target 0.8.3 importing, every
other service active. Kept: the active release and the rollback target, the interpreter, the store and its 18 backups, the data archives,
the run directories, the deployment evidence and the credential file. The rest of the deployment is recorded in
`reports/attest-deployment-2026-10-20b/README.md`.

Capacity limitation: 15 % free (2.17 GB) cannot be reached by removing what Attest owns. After this pruning Attest's whole footprint on the host is
about 380 MB (two releases, the interpreter, the data); the remaining space is held by the other services and projects on the host (Docker
images about 2.05 GB, of which Docker reports 1.6 GB as not used by a running container; application trees under `/opt` and `/root`; a 1 GB
swap file). Removing any of those is their owner's decision and was not done; the low-disk threshold (7 %, 500 MB) was not changed.

## Deployment

0.10.0, built from a clean checkout of the pin record `f0c28c2`, was deployed to yungou on 20 Oct at 16:02 UTC
(`reports/attest-deployment-2026-10-20b/README.md`): the store backed up first, the transactional installer, the memory limit read back in force
(200M for memory and for memory plus swap, no fail count, no OOM kill), the rollback target 0.9.0 verified in place, 0 holds, the start-up
recovery clean (nothing settled, nothing repaired), the public GET checks byte-identical to the release, and then release 0.8.3 pruned for
headroom. Free disk afterwards: 1,328,570,368 bytes (9.17 %); the new release took the place of the pruned one.

## Usage in this pass, per service

| Service | Use |
| --- | --- |
| Nebius Token Factory inference (Nemotron) | none: no paid call, smoke test, evaluation or demo run; the $10 proposal stays unapproved |
| Development gateway (team allowance, not USD) | 12 calls of the one live development run (11 answered, 1 never sent and sent again), plus its status and catalog reads |
| Token Factory Sandboxes | 8 operations of the live run (63.9 s of guest time; raw cost diagnostics 0.172, currency unconfirmed); 7 read-only GET requests for the reconciliation of 17 Oct (first pass: two account listings and one operation record; second pass, with the wider window: two listings and two operation records) |
| Tavily | none |
| Production console (yungou) | read-only inventory and checks over SSH, a read-only copy of the store for the start-up dry run, the pruning of four obsolete Attest-owned items after their archive was verified; no request to `POST /api/runs` |
| Aliyun Docker host | one offline suite run in a container with no network interface, removed afterwards |

## Open owner decisions and limitations (as of this record)

- Publication: who publishes the publication repository, under which author identity (most commits carry the local account name), and
  whether the scratch paths recorded in bundles since 17 Oct, which carry the account name, are redacted first. Nothing was pushed.
- The low-disk threshold is met with room (9.23 % free after the pruning), but 15 % needs space that other services and projects hold.
- The macOS sandbox profile cannot exclude the machine's loopback proxy route (the suite's own guard refuses it in the process); the Linux
  container run has no such path but skips the 26 tests that need bash, git or node.
- The paid Nemotron validation remains unapproved and unrun; the M5 results are historical.
