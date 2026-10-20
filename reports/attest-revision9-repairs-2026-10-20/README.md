# Revision 9: stop for reconciliation (20 October 2026, version 0.9.0)

This pass repairs the six issues of the review of revision 8. Each one was reproduced on the code as deployed (version 0.8.3, commit
`a4a1f19` of the review repository) before it was changed, and the same reproduction then ran against the repaired code
(`repro/repro_revision9.py`, below). Video work was set aside for this pass.

No paid Nebius inference, smoke test or evaluation was started. Development stayed on the team's Codex gateway; Sandboxes and Tavily
usage is reported separately from inference below, and nothing was pushed or published.

## The issues, their causes and the repairs

### 1. Work went on after an uncertain operation

*Cause.* Revision 8 stopped a run at the first uncertain **model** call, but sandbox operations had no such rule. The breaker caught
the Sandboxes client's `SandboxError(uncertain=True)` and re-raised it as a plain `ModelError`, so `uncertain` was lost and the run went
on to the drift audit. Five more stage handlers (the contract-audit witness, the held-out suite, every mutant, the arbitration re-runs on
the candidate and on the base, the arbitration's mutant re-runs) caught any exception, recorded it and continued: after an uncertain
witness or mutant spawn a run could still end **VERIFIED**. The evaluation harness judged a cell after its run had stopped, decided
whether a cell was uncertain by searching its error text for the word "uncertain", and the console worker started the next queued run.
Two recorded development bundles of 17 Oct (`reports/attest-reliability-2026-10-17/evaluation-paced-codex/runs/balanced-brackets-attest-a1-20261017T121900586528Z`
and `.../semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z`) did exactly this: each ended VERIFIED with one mutant spawn of
unknown outcome excluded from its score.

*Repair.* The run's ledger, the one object its provider, executor and pipeline share, now carries the stop state. `Ledger.halt` records
why the run stopped (`uncertain_operation`, `journal_failure`, `metering_unknown`, `batch_stop`), and `Ledger.admit`, which every client
calls immediately before each request it sends (every attempt, every poll, every read), refuses with `RunHalted` from then on. Every
model call and sandbox operation of the pipeline goes through four guarded entry points (`ask`, `_branch`, `_create_checkpoint`,
`_resolve_image`), which refuse once the run has stopped and turn any error that stops a run into `ReconciliationRequired`; the stage
handlers let it pass. The run ends there: verdict ERROR, one reason naming the stage and the cause, and a `reconciliation` record in
the bundle that lists every operation whose outcome is unknown with the read-only check that settles it (evidence protocol 5). No reason,
decision header or console button suggests running the stage again: the console replaces "Start a new run" with "Held for reconciliation".
An uncertain Tavily search ends the run the same way. The harness skips the judge of a stopped run, halts every other cell in flight
(`batch_stop`) and takes uncertainty from the ledger's records. The console records the run as `reconciliation_required` and opens a
hold: no run starts and admission is refused (HTTP 503) until an operator clears the hold with a note (`python -m attest holds`).

### 2. Ambiguous HTTP answers were treated as definite

*Cause.* The Sandboxes client turned every HTTP error into a plain `SandboxError`, and its spawn handler only looked at transport errors:
a spawn answered 502 left the operation without a state, was not uncertain, and was missing from every reconciliation list. A poll
answered 5xx was not retried, raised a plain error, and left the accepted operation `ACCEPTED`, outside the reconciliation list; so did an
operation that never reached a terminal state. The development gateway's client treated every HTTP error but 429 as a definite failure,
although its proxy answers 502 or 504 when the backend is slow or drops the connection after the request was forwarded. The Token Factory
client kept a 5xx's reservation committed but raised a plain error. `read_journal` keyed operations by the service's id, so a spawn with no
id (uncertain, or in flight when the process died) was invisible after a restart.

*Repair.* `attest.http.post_outcome` is the one classification of a failed POST: `not_sent` (no byte left this machine: sent again,
bounded), `rejected` (HTTP 4xx: refused, nothing executed) or `uncertain` (HTTP 5xx or any other answer, or a failure after the request
was written: never sent again, the run stops). A spawn answered 4xx is REJECTED; 5xx, a 2xx without an operation id, or a lost answer is
UNCERTAIN. Polls and other reads are retried, bounded (four retries, 1/2/4/8 s or the server's Retry-After up to 30 s), on a transport
failure or an answer that asks for it (408, 429, 5xx, and 404 for a just-accepted id); an accepted operation whose outcome is still not
read, or that never ends, is ACCEPTED_UNREAD and listed. Both model clients record the HTTP status, the phase and the answer class of
every call, and a 5xx stops the run. Operations carry a client-side id (`op_id`) from their PENDING record on, so the journal names every
unresolved spawn after a restart.

### 3. Operation records were best effort

*Cause.* `add_op` and `update_op` appended to the journal best effort: when the append failed (disk full, an I/O error, a cut line) the
failure was counted and the client went on to send the spawn or to poll, although the module claimed that accepted ids survive an
interruption. A ledger without a journal dispatched without any record.

*Repair.* A sandbox operation is journaled as PENDING, fsynced and read back, before any byte of its spawn is sent; its accepted id the
same way before the first poll; and every later state the same way. When an append fails nothing further is dispatched or polled, the
run halts, and what is known (stage, image, accepted id) goes into the halt record and to the `attest.ledger` log as one `ATTEST-HALT`
line, which survives a journal on a full disk; a halt caused by the journal is not written to it again. A ledger without a journal
dispatches no sandbox operation. Every development-gateway call takes a zero-USD pending record the same way, so a call in flight when
the process stops is visible after a restart, as Nemotron calls already were through their USD reservations.

### 4. A cut HTTP error body escaped the transport wrapper

*Cause.* `request_json` read an error answer's body inside its `except HTTPError` handler. A chunked error body cut short raised a raw
`http.client.IncompleteRead` there, and a stalled one a raw timeout, past the sibling handler that wraps transport failures, losing the
status, the phase and the fact that the request had been sent. (A Content-Length body cut short was silently truncated.)

*Repair.* Both bodies, the error's and the success's, are read under their own guard. An error answer is always an `HttpError` that keeps
its status and records `request_sent`, the phase (`response`) and whether its body arrived complete (`body_complete`, `body_error`); a
success whose body is cut is a `TransportError` that keeps the status. The classification of an answer depends on its status, never on
its body.

### 5. The offline tests depended on private configuration and the network

*Cause.* Four reliability tests built the gateway client without a base URL, so they needed the developer's private configuration and
failed without it. One called `describe()` after its HTTP mock had ended: the policy refresh window compared the governor's (fake) clock
with the real one, so `describe()` sent a real `GET /status` (with four retries) to whatever gateway the configuration named, and the
test passed anyway, because the fallback policy text still contained the phrase it checked. Nothing in the suite blocked the network or
hid credentials.

*Repair.* The tests use an explicit synthetic gateway URL and journal, and the `describe()` call is inside the mock and asserts that it
sends nothing. The policy window uses the governor's clock. `tests/_isolation.py`, imported by `tests/__init__.py`, removes provider
credentials and private configuration from the test process, disables urllib's proxy discovery (`no_proxy=*`), and turns every connection
or name lookup outside the loopback interface into an assertion that no handler catches; `tests/test_zz_isolation.py`, the last module of a
discovery run, fails if any was recorded. The complete suite is then run from a clean checkout, with credentials absent and the network
blocked by the operating system (below).

### 6. The review repository's history is not publishable

*Cause.* The exported tree has been clean since revision 8, but the review repository's earlier commits keep 125 versions of
REDACTION.json and 16 versions of the export script that carry the development gateway's host (as a regular expression, plain and
JSON-escaped), and two early EXPORT.json files carry a local home directory (`scripts/scan_publication_history.py`, which scans every
object of a repository for the private hosts in every spelling, including base64 and compressed data).

*Repair.* `scripts/build_publication_history.py` replays the review history, commit by commit with the same authors, dates and messages,
into a separate repository. Only blobs that hold a private string change, through the export's own redaction, and the derived manifest of
each affected run copy gets that entry's digest and size recomputed. The review repository and its evidence stay untouched; the replay is
deterministic, so each review commit has exactly one publication commit, and `--verify` checks the result (records below).

## Reproduction

`repro/repro_revision9.py --code <checkout>` runs every scenario of the issues above against one checkout, offline: credentials removed,
HOME pointing to an empty directory, every connection and name lookup outside the loopback interface refused inside the process. It
reuses the checkout's own test fakes, so the same script runs against both versions.

Before the repair (0.8.3, clean checkout of `a4a1f19`) and after it (0.9.0, clean checkouts of `697d0e7` and of the pinned `7664742`), in
the same environment as the suites below (no credential, no network):

| Group | Checks | FAIL on 0.8.3 | FAIL on 0.9.0 | What the failures on 0.8.3 were |
| --- | --- | --- | --- | --- |
| A. An uncertain sandbox failure at each of 15 stage situations | 45 | 23 | 0 | after an uncertain witness spawn 16 further requests and a VERIFIED verdict; after an uncertain mutant 8 (VERIFIED); after the held-out suite 9; after the breaker the drift-audit call and the advice "rerun the breaker stage"; after an arbitration mutant re-run 1 (VERIFIED); no stage produced a structured reconciliation record |
| B. Harness and console worker | 4 | 4 | 0 | the harness ran the drift audit and the judge after an uncertain adversarial-test spawn and did not mark the row uncertain; the worker ran the next queued run (26 requests); the row had no reconciliation code |
| C. Adapters: HTTP answers, cut bodies, parallel branches | 15 | 14 | 0 | spawn 502: no state, not uncertain, nothing to reconcile, the next spawn sent; spawn 400: no state; poll 503: one poll, no retry, the operation left ACCEPTED; never-ending operation left ACCEPTED; gateway 502/504 and Token Factory 500 not uncertain and a second request sent; catalog 503 not retried; a cut chunked 502 body raised a raw IncompleteRead and a stalled 503 body a raw TimeoutError; a cut 200 body lost its status; six parallel branches went on after the third spawn's answer was lost |
| D. Journal | 7 | 6 | 0 | disk full, an fsync error or a half-written line on the PENDING record: the spawn was sent anyway; disk full on the accepted id: polled anyway, the id not kept; after a death between dispatch and answer no unresolved spawn named; the console's recovery used the code `interrupted` |
| E. Test isolation | 3 | 3 | 0 | without private configuration four reliability tests and the policy test errored ("the development gateway URL is not configured"); with a gateway URL configured the policy test passed while sending five requests outside its mock (a real `GET /status` and four retries) |

The checks that passed on 0.8.3 are the controls (a gateway 400 is definite; a cut journal tail is reported) and the stages where the old
pipeline already ended the run by letting the exception propagate (checkpoint, red check, implementer tools, verification, repository
suite), which still left no reconciliation record. Files: `repro/before-a4a1f19-0.8.3.txt` and `.json`, `repro/after-697d0e7-0.9.0.txt`
and `.json`, `repro/after-7664742-0.9.0.txt` and `.json` (74 of 74 both times). The new tests (`tests/test_revision9.py`, 53 tests) cover the same ground inside the suite.

## Clean-checkout suites, credentials absent and network blocked

| Run | Environment | Result |
| --- | --- | --- |
| `suites/final-tree-suite-14-clean-7664742-macos-no-network.log` (and `-12-clean-697d0e7-`, the same result) | clean `git worktree` of the pinned `7664742`; a fresh virtualenv with the pinned dependencies (`suites/requirements-pinned.txt`); `env -i` with PATH, LANG and HOME pointing to an empty directory (no credential, no private configuration, no proxy variable); macOS `sandbox-exec` (`suites/macos-no-network.sb`) denying every outbound connection except to the loopback interface; a probe in the same sandbox: connections to 1.1.1.1:443 and 8.8.8.8:53 refused, name lookup refused | **458 tests, OK, 0 skipped** (bash, git and node present) |
| `suites/final-tree-suite-15-clean-7664742-linux-no-network.log` (and `-13-clean-697d0e7-`, the same result) | clean `git archive` of the pinned `7664742` copied into a container on the dedicated Docker daemon of the Aliyun host (`--network none`: its only interface is `lo`; Alpine 3.24.2, Python 3.12.15, uid 65534, all capabilities dropped, no-new-privileges, 384 MB memory and memory plus swap, 1 CPU, 400 PIDs); dependencies installed offline from a wheelhouse of the same pins; a probe: connections refused with "network unreachable", name lookup refused; the container removed afterwards, the host's other services untouched | **458 tests, OK, 26 skipped**: the 20 deployment rehearsals that need bash, the 3 console client checks that need node and the 3 export checks that need git, none of which the image has |

On this Mac the system's proxy (Clash Verge) listens on the loopback interface, which the macOS profile cannot exclude (its loopback
allowance overrides a port-specific denial), so a request routed through it would have left the machine. The suite's own guard
(`tests/_isolation.py`) therefore refuses that port and every other loopback port that was listening before the suite started, and
records every attempt; none was recorded, and the Linux run has no such path at all. An earlier clean run of this pass, of `58d2520`
(whose guard refused only the configured proxy), passed the same 458 in the same macOS set-up; `808137c` was run in the working tree
only (458 OK). The pin names `7664742` (see the console section below for why it follows `697d0e7`).

## Bundles, export provenance and accounting

- `attest check` on the 181 bundles of the export: 181 OK with the 0.8.3 checker and with the 0.9.0 checker
  (`checker/checker-0.8.3-vs-0.9.0.json`). Warnings rise from 481 to 486: the two VERIFIED reliability bundles of 17 Oct get the new
  warning that an operation of unknown outcome stands behind their verdict (correction appended to
  `reports/attest-reliability-2026-10-17/README.md`), and three revision-7 development bundles that ended ERROR after an uncertain model
  call now render a different decision ("do not start a new run before the uncertain call is reconciled" instead of "start a new run"),
  so their stored PROOF.md no longer equals a fresh rendering (a warning for bundles of another revision; no error).
- `scripts/check_export_provenance.py` (`checker/provenance-0.9.0-export.json`): 181 bundles checked OK, 24 fully verified (protocols
  2, 3 and 4: 7, 3, 14), 157 historical, every exported file equal to its source or traced through REDACTION.json, 95 of the 116 batch
  bundles with the package digest of their registration and the same 21 without a recorded or registered digest as in revision 8, 17
  provider profiles equal to their registration, nothing failed: the same figures as the final export of revision 8.
- Budget accounting: the accounting and budget tests pass unchanged except where the stop rule changed what they expect (an uncertain
  breaker call now ends the run ERROR; a resumed batch over an interrupted run with a call in flight starts nothing without
  `--reconciled`); the committed figures of every scenario are unchanged.

## Publication repository

`publication/publication-verify-to-7664742.json` and `publication/publication-map-to-7664742.json`: the review history up to `7664742`
(66 commits) replayed into `dist/publication`; 143 blobs with a private string rewritten and 324 derived manifests recomputed; the scan of
every object of the result (5,825) found no private host in any spelling and no secret-like token; every commit pair differs only by
those rewrites; the package and harness digests of the seven pins (M5, revisions 4 to 9) are equal in both histories and equal to the
recorded values; the 849 run copies whose manifest changed pass `attest check` at the commits where they changed. The review repository
before this pass (`publication/scan-review-repository-a4a1f19.json`): 143 objects with hits (125 REDACTION.json versions, 16 versions of
the export script, 2 EXPORT.json versions with a home directory), no commit message or path name with one. Nothing was pushed; no
remote is configured.

The earlier build up to `697d0e7` (`publication-map-to-697d0e7.json`, 65 commits) maps every commit it shares with the later one to the
same publication commit, as a deterministic replay must.

## The console's held-run state, in a real browser, and a live development run

A run held for reconciliation was opened in Chrome before the deployment (`console/held_run_check.py`, `console/held-run-check-7664742.json`):
a halted bundle written by the offline pipeline (an uncertain adversarial-test spawn), served by a local console with no credential, at
1440 px and at 390 px with mobile emulation, every request that is not a GET aborted in the browser (none was needed). At both widths
nothing is wider than the viewport, the decision header says "This run stopped for reconciliation", the case file offers "Held for
reconciliation" and no "Start a new run", and exhibit E7 shows the reconciliation line. The first run of this check, on `697d0e7`,
showed the decision as "At stage reconciliation": recording the stop relabelled the bundle's stage. `7664742` takes the stage from the
halt record ("At stage breaker-tests") and the tests assert it.

One live development run of the clean checkout of `697d0e7` (`live-codex/`; `python -m attest run --task
examples/durationkit-task/task.json --provider codex --no-grounding --max-mutants 6`) checked the new request paths against the real
services before the deployment: VERIFIED under evidence protocol 5, no reconciliation needed, `attest check` OK with complete evidence
and no warning; 11 gateway calls, each behind a zero-USD pending record closed by its call record; 15 Sandboxes operations, each
journaled PENDING, ACCEPTED and SUCCESS in that order. `7664742` changes no request path.

## Usage in this pass, per service

| Service | Use |
| --- | --- |
| Nebius Token Factory inference (Nemotron) | none: no paid call, smoke test, evaluation or demo run; the $10 proposal stays unapproved |
| Development gateway (team allowance, not USD) | 11 calls, one live development run |
| Token Factory Sandboxes | 15 operations of that run (50.3 s of guest time; raw cost diagnostics 0.393, no confirmed currency); no other Sandboxes request |
| Tavily | none |
| Production console | the deployment of 0.9.0 with the transactional installer (20 Oct 08:22 UTC), and otherwise read-only checks (GET requests, read-only SSH; `reports/attest-deployment-2026-10-20/`) |
| Aliyun host | two runs of the offline suite in a container with no network interface on the dedicated Docker daemon, removed afterwards |

## Deployment

0.9.0 (package `ab5b1705…`), built from a clean checkout of the pin record `65d81f7`, was installed on yungou on 20 Oct at 08:22 UTC with
the transactional installer, after a backup of the store and the data directory; the previous release 0.8.3 stays selectable with
`rollback.sh` (`reports/attest-deployment-2026-10-20/README.md`). Read back afterwards: version 0.9.0 and the package digest through
`/opt/attest/app`; systemd `MemoryLimit` and the cgroup's memory and memory-plus-swap limits all 209,715,200 bytes on the new main
process, no fail count, no OOM kill; queue 0, no reservation, $0.00 committed on the new UTC day; no reconciliation hold open; the
other services on the host unchanged.
